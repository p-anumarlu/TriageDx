# triage.ai — Backend

Medical triage guidance API. Two-layer engine: rule-based clinical safety floor +
Google Gemini AI. Outputs one of five urgency tiers, always defaulting to the more
conservative result when the models disagree.

> **This is a triage guidance tool, not a diagnostic device.**
> All output language uses "may be consistent with…" phrasing.

---

## Architecture

```
Frontend (React / Expo)
        │
        ▼  POST /api/assess
┌───────────────────────────────────────┐
│           FastAPI Backend             │
│                                       │
│  ┌─────────────────────────────────┐  │
│  │    Rule Engine  (safety floor)  │  │
│  │  ICD-10 · ESI · START protocol  │  │
│  └──────────────┬──────────────────┘  │
│                 │                     │
│  ┌──────────────▼──────────────────┐  │
│  │   Confidence-Weighted Blender   │  │
│  │   • Red flag → always 911       │  │
│  │   • Rule engine is the floor    │  │
│  │   • Rounds up (conservative)    │  │
│  └──────────────┬──────────────────┘  │
│                 │                     │
│  ┌──────────────▼──────────────────┐  │
│  │    Gemini AI Engine             │  │
│  │    gemini-1.5-flash (free tier) │  │
│  └─────────────────────────────────┘  │
│                                       │
│  PostgreSQL / SQLite  │  HIPAA Logs   │
└───────────────────────────────────────┘
        │
        ▼  AssessmentResponse JSON
```

---

## Quick Start

### 1. Prerequisites

- Python 3.12+
- [VS Code](https://code.visualstudio.com/) with the Python extension
- A free [Google AI Studio](https://aistudio.google.com/app/apikey) API key

### 2. Clone and install

```bash
git clone <your-repo>
cd triage-ai-backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
```

Open `.env` and fill in:

```env
GOOGLE_AI_API_KEY=your-key-from-aistudio.google.com
SECRET_KEY=run-python-secrets-token-hex-32-and-paste-here
```

Generate a secret key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 4. Run the server

```bash
uvicorn app.main:app --reload --port 8000
```

Visit:
- **Swagger UI** → http://localhost:8000/docs
- **ReDoc** → http://localhost:8000/redoc
- **Health check** → http://localhost:8000/health

### 5. Run tests (no server needed)

```bash
# With pytest
pytest tests/ -v

# Or plain Python (no install needed beyond app deps)
python tests/test_rule_engine.py
```

---

## API Reference

### `POST /api/assess`

Core triage endpoint. Accepts a zone + Q&A list, returns a 5-tier urgency result.

**Request**
```json
{
  "zone_id": "chest",
  "answers": [
    { "question_id": "sensation",  "answer_value": "pressure" },
    { "question_id": "radiation",  "answer_value": "cardiac_rad" },
    { "question_id": "assoc",      "answer_value": "cardiac_assoc" },
    { "question_id": "onset",      "answer_value": "sudden" },
    { "question_id": "duration",   "answer_value": "acute" }
  ],
  "session_token": "optional-uuid-from-localstorage"
}
```

**Response**
```json
{
  "session_id": "uuid",
  "triage_level": 4,
  "triage_label": "Call 911 Now",
  "assessment": "Your symptoms may be consistent with a possible cardiac event such as a heart attack. This may be a life-threatening emergency — do not delay.",
  "next_steps": ["Call 911 immediately...", "..."],
  "possible_conditions": ["Acute coronary syndrome (ACS)", "STEMI / NSTEMI"],
  "red_flag": true,
  "confidence": 0.94,
  "rule_engine_level": 4,
  "ai_engine_level": 4,
  "blended": true,
  "disclaimer": "This tool provides general triage guidance only..."
}
```

**Triage levels**

| Level | Label | Meaning |
|-------|-------|---------|
| 0 | Manage at Home | Self-care is appropriate |
| 1 | OTC Medicine + Monitor | Pharmacy-level care |
| 2 | Doctor or Urgent Care | See a clinician today |
| 3 | ER — Same-Day | Emergency room within 1-2 hours |
| 4 | Call 911 Now | Life-threatening — minutes matter |

---

### `POST /api/auth/register`

```json
{ "email": "user@example.com", "password": "securepassword" }
```

### `POST /api/auth/login`

OAuth2 form fields: `username` + `password`. Returns `{ "access_token": "...", "token_type": "bearer" }`.

### `GET /api/auth/me`

Requires `Authorization: Bearer <token>`.

### `GET /api/history`

Returns past sessions. Pass `?session_token=<uuid>` for anonymous tracking,
or use a Bearer token for account-based history.

---

## Supported Body Zones

| Zone ID | Label |
|---------|-------|
| `head` | Head |
| `neck` | Neck / Throat |
| `chest` | Chest |
| `upper_abdomen` | Upper Abdomen |
| `lower_abdomen` | Lower Abdomen |
| `r_arm` / `l_arm` | Right / Left Arm |
| `r_forearm` / `l_forearm` | Forearms |
| `r_hand` / `l_hand` | Hands |
| `r_thigh` / `l_thigh` | Thighs |
| `r_leg` / `l_leg` | Knee & Lower Leg |
| `general` | General / Whole Body |

---

## Database Migrations (Alembic)

```bash
# Generate a migration after changing models
alembic revision --autogenerate -m "describe your change"

# Apply pending migrations
alembic upgrade head

# Rollback one step
alembic downgrade -1
```

For development, the app auto-creates tables on startup via SQLite (`triage.db`).
Use Alembic for production PostgreSQL deployments.

---

## Production Checklist

- [ ] Set `ENVIRONMENT=production` in `.env`
- [ ] Use PostgreSQL: `DATABASE_URL=postgresql+asyncpg://...`
- [ ] Generate a strong `SECRET_KEY`
- [ ] Set `CORS_ORIGINS` to your actual frontend domain
- [ ] Run behind a reverse proxy (nginx / Caddy) with TLS
- [ ] Enable HIPAA audit logging: `HIPAA_AUDIT_LOG=true`
- [ ] Set up automated database backups
- [ ] Review FTC Health Breach Notification Rule compliance
- [ ] Add rate limiting (suggest: `slowapi` library)

---

## Project Structure

```
triage-ai-backend/
├── app/
│   ├── main.py              ← FastAPI app, startup, CORS, routers
│   ├── config.py            ← Settings (pydantic-settings + .env)
│   ├── database.py          ← Async SQLAlchemy engine + session
│   ├── models/
│   │   ├── user.py          ← User table
│   │   └── session.py       ← TriageSession + AuditLog tables
│   ├── schemas/
│   │   ├── assess.py        ← Request/Response Pydantic models
│   │   └── auth.py          ← Auth schemas
│   ├── routers/
│   │   ├── assess.py        ← POST /api/assess  (core endpoint)
│   │   ├── auth.py          ← register / login / me
│   │   └── history.py       ← GET /api/history
│   ├── services/
│   │   ├── rule_engine.py   ← Clinical rules (ICD-10 / ESI protocol)
│   │   ├── ai_engine.py     ← Google Gemini integration
│   │   └── blender.py       ← Confidence-weighted result merger
│   └── core/
│       └── security.py      ← JWT, bcrypt, IP hashing
├── alembic/                 ← Database migration scripts
├── tests/
│   └── test_rule_engine.py  ← Clinical correctness tests
├── .env.example
├── alembic.ini
├── Dockerfile
└── requirements.txt
```

---

## Regulatory Notes

- **FDA**: Positioned as a "triage guidance tool," not a diagnostic device.
  Output language uses "may be consistent with…" throughout.
- **HIPAA**: IP addresses are one-way hashed (SHA-256) in audit logs.
  No free-text PII is stored in `triage_sessions`. For a full HIPAA deployment,
  use an encrypted PostgreSQL instance (AWS RDS with encryption at rest recommended).
- **FTC Health Breach Notification Rule**: Applies to this product as a health app.
  Consult counsel before launch.

---

## Google AI Studio — Free Tier Limits

| Model | RPM | TPD |
|-------|-----|-----|
| gemini-1.5-flash | 15 | 1,500 |
| gemini-2.0-flash | 15 | 1,500 |

For production at scale, upgrade to a paid Google AI tier or cache results
for identical symptom patterns. The rule engine operates at zero API cost
and serves as the fallback when Gemini is unavailable.
