"""
Rule Engine + Blender Tests
────────────────────────────
Run with:
    pytest tests/ -v
    python tests/test_rule_engine.py   (no pytest needed)

No network calls, no database — pure clinical logic.
"""
import sys, os, types

def _stub(name, **attrs):
    m = types.ModuleType(name)
    for k, v in attrs.items(): setattr(m, k, v)
    sys.modules.setdefault(name, m)

# Stubs for packages that may not be installed yet (safe to remove after pip install)
if "pydantic_settings" not in sys.modules:
    class _BS:
        def __init_subclass__(cls, **kw): pass
        def __init__(self, **kw):
            for k, v in kw.items(): setattr(self, k, v)
    _stub("pydantic_settings", BaseSettings=_BS)
for _m in ["google", "google.generativeai", "jose", "passlib",
           "passlib.context", "sqlalchemy", "sqlalchemy.orm",
           "sqlalchemy.ext.asyncio"]:
    _stub(_m)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.rule_engine import (
    rule_engine, RuleResult,
    LEVEL_HOME, LEVEL_OTC, LEVEL_DOCTOR, LEVEL_ER, LEVEL_911,
)
from app.services.blender import blend
from app.services.ai_engine import AIEngineResult
from app.services.ml_engine import MLResult


def ans(*pairs):
    it = iter(pairs)
    return [{"question_id": q, "answer_value": v} for q, v in zip(it, it)]


# ─── CHEST ───────────────────────────────────────────────────────────────────

def test_acs_pressure_radiation():
    r = rule_engine.evaluate("chest", ans("sensation","pressure","radiation","cardiac_rad"))
    assert r.level == LEVEL_911 and r.red_flag

def test_acs_pressure_diaphoresis():
    r = rule_engine.evaluate("chest", ans("sensation","pressure","assoc","cardiac_assoc"))
    assert r.level == LEVEL_911 and r.red_flag

def test_aortic_dissection():
    r = rule_engine.evaluate("chest", ans("radiation","back_rad"))
    assert r.level == LEVEL_911 and r.red_flag

def test_pe_pleuritic_sob():
    r = rule_engine.evaluate("chest", ans("sensation","sharp","assoc","sob"))
    assert r.level >= LEVEL_ER and not r.red_flag

def test_gerd():
    r = rule_engine.evaluate("chest", ans("sensation","burning","onset","positional"))
    assert r.level <= LEVEL_DOCTOR and not r.red_flag


# ─── HEAD ────────────────────────────────────────────────────────────────────

def test_thunderclap():
    r = rule_engine.evaluate("head", ans("onset","thunderclap"))
    assert r.level == LEVEL_911 and r.red_flag

def test_stroke():
    r = rule_engine.evaluate("head", ans("assoc","stroke"))
    assert r.level == LEVEL_911 and r.red_flag

def test_meningitis():
    r = rule_engine.evaluate("head", ans("assoc","meningitis"))
    assert r.level == LEVEL_911 and r.red_flag

def test_migraine():
    r = rule_engine.evaluate("head", ans("assoc","migraine_sx","severity","severe"))
    assert LEVEL_DOCTOR <= r.level <= LEVEL_ER and not r.red_flag

def test_tension_headache():
    r = rule_engine.evaluate("head", ans("location","frontal","severity","mild"))
    assert r.level <= LEVEL_DOCTOR and not r.red_flag


# ─── NECK ────────────────────────────────────────────────────────────────────

def test_neck_meningism():
    r = rule_engine.evaluate("neck", ans("type","meningism"))
    assert r.level == LEVEL_911 and r.red_flag

def test_neck_positional_strain():
    r = rule_engine.evaluate("neck", ans("cause","positional","severity","mild"))
    assert r.level <= LEVEL_OTC and not r.red_flag


# ─── UPPER ABDOMEN ───────────────────────────────────────────────────────────

def test_gi_bleed():
    r = rule_engine.evaluate("upper_abdomen", ans("assoc","gi_bleed"))
    assert r.level == LEVEL_911 and r.red_flag

def test_acute_cholangitis():
    r = rule_engine.evaluate("upper_abdomen", ans("assoc","jaundice","onset","sudden"))
    assert r.level >= LEVEL_ER

def test_gallbladder_colic():
    r = rule_engine.evaluate("upper_abdomen", ans("assoc","gallbladder","onset","hours"))
    assert r.level >= LEVEL_DOCTOR and not r.red_flag


# ─── LOWER ABDOMEN ───────────────────────────────────────────────────────────

def test_appendicitis():
    r = rule_engine.evaluate("lower_abdomen", ans("location","lr","assoc","appendix_mig"))
    assert r.level >= LEVEL_ER

def test_bowel_obstruction():
    r = rule_engine.evaluate("lower_abdomen", ans("assoc","obstruction"))
    assert r.level >= LEVEL_ER

def test_peritonitis():
    r = rule_engine.evaluate("lower_abdomen", ans("assoc","peritoneal"))
    assert r.level >= LEVEL_ER


# ─── MSK ─────────────────────────────────────────────────────────────────────

def test_msk_overuse():
    r = rule_engine.evaluate("r_leg", ans("cause","overuse","severity","mild"))
    assert r.level <= LEVEL_DOCTOR and not r.red_flag

def test_msk_trauma_severe():
    r = rule_engine.evaluate("r_leg", ans("cause","trauma","severity","severe"))
    assert r.level >= LEVEL_ER

def test_msk_atraumatic_numbness():
    r = rule_engine.evaluate("l_arm", ans("type","numbness","cause","atraumatic"))
    assert r.level >= LEVEL_DOCTOR


# ─── BLENDER ─────────────────────────────────────────────────────────────────

def _rr(level, conf=0.80, red_flag=False, conditions=None):
    return RuleResult(level=level, confidence=conf, red_flag=red_flag,
                      conditions=conditions or [], icd10_hints=[], reasoning="test")

def _ar(level, conf=0.75, red_flag=False, fallback=False):
    return AIEngineResult(level=level, confidence=conf, red_flag=red_flag,
                          conditions=[], reasoning="test", fallback=fallback)


def _ml(level, conf=0.70, fallback=False):
    return MLResult(level=level, confidence=conf, diagnoses=[], reasoning="test", fallback=fallback)

def test_blend_rule_red_flag_wins():
    assert blend("chest", _rr(LEVEL_911, red_flag=True), _ml(LEVEL_DOCTOR), _ar(LEVEL_DOCTOR)).level == LEVEL_911

def test_blend_ai_red_flag_wins():
    assert blend("head", _rr(LEVEL_DOCTOR), _ml(LEVEL_DOCTOR), _ar(LEVEL_911, red_flag=True)).level == LEVEL_911

def test_blend_rule_engine_is_floor():
    # AI cannot downgrade rule engine
    result = blend("chest", _rr(LEVEL_ER), _ml(LEVEL_OTC), _ar(LEVEL_OTC))
    assert result.level >= LEVEL_ER

def test_blend_fallback_keeps_rule():
    # AI falls back → rule + ML blend, both say DOCTOR → result is DOCTOR
    result = blend("head", _rr(LEVEL_DOCTOR), _ml(LEVEL_DOCTOR), _ar(LEVEL_911, fallback=True))
    assert result.level == LEVEL_DOCTOR  # conservative floor upheld

def test_blend_large_disagreement_takes_max():
    # >1 level gap → take the higher
    result = blend("chest", _rr(LEVEL_OTC, conf=0.55), _ml(LEVEL_ER, conf=0.80), _ar(LEVEL_ER, conf=0.85))
    assert result.level >= LEVEL_ER


# ─── Runner ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import traceback
    G, R, Z = "\033[32m", "\033[31m", "\033[0m"
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    ok = fail = 0
    print(f"\n  triage.ai — Clinical Rule Engine + Blender\n  {'─'*44}")
    for t in tests:
        try:
            t(); print(f"  {G}✓{Z}  {t.__name__}"); ok += 1
        except Exception:
            print(f"  {R}✗{Z}  {t.__name__}"); traceback.print_exc(); fail += 1
    c = G if not fail else R
    print(f"\n  {c}{ok}/{ok+fail} passed{Z}\n")
    sys.exit(0 if not fail else 1)
