"""
Rule-Based Clinical Triage Engine
──────────────────────────────────
Acts as the safety floor in the two-layer blend.
Rules are derived from validated triage protocols (ESI, Canadian Triage,
START) and cross-referenced with ICD-10 source codes.

Key principle: always err conservative. A missed emergency is worse
than an unnecessary ER visit.
"""
from dataclasses import dataclass, field
from typing import Callable


# ── Triage level constants (matches frontend exactly) ────────────────────────
LEVEL_HOME = 0
LEVEL_OTC = 1
LEVEL_DOCTOR = 2
LEVEL_ER = 3
LEVEL_911 = 4

TRIAGE_LABELS = {
    0: "Manage at Home",
    1: "OTC Medicine + Monitor",
    2: "Doctor or Urgent Care",
    3: "ER — Same-Day",
    4: "Call 911 Now",
}

NEXT_STEPS = {
    0: [
        "Rest and stay well-hydrated.",
        "Monitor your symptoms every few hours.",
        "Return to this assessment if anything worsens.",
    ],
    1: [
        "Appropriate over-the-counter treatment may provide relief.",
        "Monitor closely — reassess in 24 hours.",
        "Seek care sooner if new or worsening symptoms develop.",
    ],
    2: [
        "Schedule a same-day or next-day appointment.",
        "Urgent care is appropriate if your PCP is unavailable.",
        "Call your doctor's office for guidance on urgency.",
    ],
    3: [
        "Go to your nearest emergency room now.",
        "Do not delay — do not wait for symptoms to resolve.",
        "Have someone drive you or take a rideshare.",
    ],
    4: [
        "Call 911 immediately — do not drive yourself.",
        "Stay on the line with emergency services.",
        "Unlock your front door if possible.",
        "Tell them your symptoms and location.",
    ],
}


@dataclass
class RuleResult:
    level: int
    confidence: float
    red_flag: bool
    conditions: list[str] = field(default_factory=list)
    icd10_hints: list[str] = field(default_factory=list)
    reasoning: str = ""


@dataclass
class ClinicalRule:
    """
    A single clinical triage rule.

    predicate: receives the answers dict {question_id: answer_value}
               returns True if this rule matches.
    zones:     list of zone_ids this rule applies to, or ["*"] for all zones.
    level:     resulting triage level if matched.
    confidence: 0.0–1.0 — how certain this rule is when matched.
    red_flag:  if True, result is immediately returned without checking
               remaining rules (hard interrupt).
    """
    zones: list[str]
    predicate: Callable[[dict], bool]
    level: int
    confidence: float
    conditions: list[str]
    icd10_hints: list[str]
    reasoning: str
    red_flag: bool = False


def _a(answers: dict, qid: str, *values: str) -> bool:
    """Helper: returns True if answers[qid] is in values."""
    return answers.get(qid) in values


# ─────────────────────────────────────────────────────────────────────────────
# CLINICAL RULES  (priority order — first match wins for red flags)
# ─────────────────────────────────────────────────────────────────────────────

RULES: list[ClinicalRule] = [

    # ── CHEST ─────────────────────────────────────────────────────────────────

    ClinicalRule(
        zones=["chest"],
        predicate=lambda a: (
            _a(a, "sensation", "pressure") and
            (_a(a, "radiation", "cardiac_rad") or _a(a, "assoc", "cardiac_assoc"))
        ),
        level=LEVEL_911,
        confidence=0.94,
        conditions=["Acute coronary syndrome (ACS)", "STEMI / NSTEMI"],
        icd10_hints=["I21.9", "I20.0"],
        reasoning="Classic ACS pattern: pressure with radiation to arm/jaw or diaphoresis/nausea.",
        red_flag=True,
    ),
    ClinicalRule(
        zones=["chest"],
        predicate=lambda a: (
            _a(a, "sensation", "pressure") and
            _a(a, "onset", "sudden") and
            _a(a, "duration", "acute")
        ),
        level=LEVEL_911,
        confidence=0.88,
        conditions=["Possible ACS", "Unstable angina"],
        icd10_hints=["I21.9", "I20.0"],
        reasoning="Sudden pressure onset within the hour — high suspicion for ACS.",
        red_flag=True,
    ),
    ClinicalRule(
        zones=["chest"],
        predicate=lambda a: _a(a, "radiation", "back_rad"),
        level=LEVEL_911,
        confidence=0.80,
        conditions=["Possible aortic dissection"],
        icd10_hints=["I71.0"],
        reasoning="Radiation to inter-scapular region raises concern for aortic dissection.",
        red_flag=True,
    ),
    ClinicalRule(
        zones=["chest"],
        predicate=lambda a: (
            _a(a, "sensation", "sharp") and _a(a, "assoc", "sob")
        ),
        level=LEVEL_ER,
        confidence=0.78,
        conditions=["Possible pulmonary embolism", "Pleuritis", "Pneumothorax"],
        icd10_hints=["I26.99", "J90", "J93.9"],
        reasoning="Pleuritic chest pain with dyspnea warrants same-day emergency evaluation.",
    ),
    ClinicalRule(
        zones=["chest"],
        predicate=lambda a: _a(a, "assoc", "sob"),
        level=LEVEL_ER,
        confidence=0.72,
        conditions=["Chest pain with dyspnea — multiple etiologies"],
        icd10_hints=["R07.9", "J80"],
        reasoning="Any chest pain accompanied by shortness of breath at rest is an ER presentation.",
    ),
    ClinicalRule(
        zones=["chest"],
        predicate=lambda a: (
            _a(a, "sensation", "burning") or _a(a, "onset", "positional")
        ),
        level=LEVEL_OTC,
        confidence=0.72,
        conditions=["Gastroesophageal reflux disease (GERD)", "Esophageal spasm"],
        icd10_hints=["K21.0", "K22.4"],
        reasoning="Burning chest pain worsened by food/position is consistent with GERD.",
    ),
    ClinicalRule(
        zones=["chest"],
        predicate=lambda a: _a(a, "duration", "week", "chronic"),
        level=LEVEL_DOCTOR,
        confidence=0.65,
        conditions=["Musculoskeletal chest pain", "Costochondritis", "Anxiety-related"],
        icd10_hints=["M94.0", "F41.1"],
        reasoning="Chronic chest pain without red flags warrants physician evaluation.",
    ),

    # ── HEAD ──────────────────────────────────────────────────────────────────

    ClinicalRule(
        zones=["head"],
        predicate=lambda a: _a(a, "onset", "thunderclap"),
        level=LEVEL_911,
        confidence=0.97,
        conditions=["Subarachnoid hemorrhage (SAH)", "Intracranial emergency"],
        icd10_hints=["I60.9"],
        reasoning="Thunderclap headache is SAH until proven otherwise — neurosurgical emergency.",
        red_flag=True,
    ),
    ClinicalRule(
        zones=["head"],
        predicate=lambda a: _a(a, "assoc", "stroke"),
        level=LEVEL_911,
        confidence=0.96,
        conditions=["Acute ischemic stroke", "TIA", "Hemorrhagic stroke"],
        icd10_hints=["I63.9", "G45.9"],
        reasoning="FAST criteria met (facial droop, arm weakness, speech) — stroke protocol.",
        red_flag=True,
    ),
    ClinicalRule(
        zones=["head"],
        predicate=lambda a: _a(a, "assoc", "meningitis"),
        level=LEVEL_911,
        confidence=0.93,
        conditions=["Bacterial meningitis", "Viral meningitis", "Encephalitis"],
        icd10_hints=["G00.9", "G03.9"],
        reasoning="Kernig/Brudzinski triad (stiff neck + fever + photophobia) — meningitis protocol.",
        red_flag=True,
    ),
    ClinicalRule(
        zones=["head"],
        predicate=lambda a: (
            _a(a, "severity", "max", "severe") and _a(a, "onset", "sudden", "quick")
        ),
        level=LEVEL_ER,
        confidence=0.75,
        conditions=["High-risk headache", "Intracranial hypertension"],
        icd10_hints=["G44.309", "G93.2"],
        reasoning="Severe sudden headache without classic thunderclap — still requires emergency rule-out.",
    ),
    ClinicalRule(
        zones=["head"],
        predicate=lambda a: (
            _a(a, "location", "orbital") and _a(a, "severity", "severe", "max")
        ),
        level=LEVEL_ER,
        confidence=0.70,
        conditions=["Cluster headache", "Acute angle-closure glaucoma"],
        icd10_hints=["G44.009", "H40.219"],
        reasoning="Orbital severe pain with autonomic features — cluster headache or glaucoma.",
    ),
    ClinicalRule(
        zones=["head"],
        predicate=lambda a: _a(a, "assoc", "migraine_sx"),
        level=LEVEL_DOCTOR,
        confidence=0.82,
        conditions=["Migraine with or without aura"],
        icd10_hints=["G43.909"],
        reasoning="Classic migraine pattern — requires physician evaluation for management plan.",
    ),
    ClinicalRule(
        zones=["head"],
        predicate=lambda a: (
            _a(a, "location", "frontal") and _a(a, "severity", "mild", "mod")
        ),
        level=LEVEL_OTC,
        confidence=0.78,
        conditions=["Tension headache", "Sinusitis"],
        icd10_hints=["G44.209", "J32.9"],
        reasoning="Frontal mild-moderate headache consistent with tension or sinus etiology.",
    ),

    # ── NECK ──────────────────────────────────────────────────────────────────

    ClinicalRule(
        zones=["neck"],
        predicate=lambda a: _a(a, "type", "meningism"),
        level=LEVEL_911,
        confidence=0.94,
        conditions=["Bacterial meningitis"],
        icd10_hints=["G00.9"],
        reasoning="Neck stiffness triad — meningitis protocol.",
        red_flag=True,
    ),
    ClinicalRule(
        zones=["neck"],
        predicate=lambda a: (
            _a(a, "cause", "trauma") and _a(a, "severity", "severe", "max")
        ),
        level=LEVEL_ER,
        confidence=0.82,
        conditions=["Possible cervical spine injury"],
        icd10_hints=["S14.109A"],
        reasoning="High-force neck trauma with severe pain — c-spine injury until cleared.",
    ),
    ClinicalRule(
        zones=["neck"],
        predicate=lambda a: _a(a, "type", "swelling"),
        level=LEVEL_DOCTOR,
        confidence=0.72,
        conditions=["Lymphadenopathy", "Thyroid pathology", "Soft tissue mass"],
        icd10_hints=["R59.0", "E04.9"],
        reasoning="Unexplained neck mass requires physician evaluation and imaging.",
    ),
    ClinicalRule(
        zones=["neck"],
        predicate=lambda a: _a(a, "type", "throat"),
        level=LEVEL_DOCTOR,
        confidence=0.68,
        conditions=["Pharyngitis", "Tonsillitis", "Peritonsillar abscess"],
        icd10_hints=["J02.9", "J03.9"],
        reasoning="Throat symptoms with difficulty swallowing warrant clinical assessment.",
    ),
    ClinicalRule(
        zones=["neck"],
        predicate=lambda a: _a(a, "cause", "positional"),
        level=LEVEL_OTC,
        confidence=0.85,
        conditions=["Muscle strain", "Torticollis"],
        icd10_hints=["S19.9XXA"],
        reasoning="Positional onset strongly suggests benign muscle strain.",
    ),

    # ── UPPER ABDOMEN ─────────────────────────────────────────────────────────

    ClinicalRule(
        zones=["upper_abdomen"],
        predicate=lambda a: _a(a, "assoc", "gi_bleed"),
        level=LEVEL_911,
        confidence=0.96,
        conditions=["Upper GI hemorrhage", "Peptic ulcer perforation"],
        icd10_hints=["K25.4", "K92.1"],
        reasoning="Hematemesis or melena indicates active upper GI bleed — hemorrhagic shock risk.",
        red_flag=True,
    ),
    ClinicalRule(
        zones=["upper_abdomen"],
        predicate=lambda a: (
            _a(a, "assoc", "jaundice") and _a(a, "onset", "sudden", "hours")
        ),
        level=LEVEL_ER,
        confidence=0.85,
        conditions=["Acute cholangitis", "Choledocholithiasis"],
        icd10_hints=["K83.0", "K80.50"],
        reasoning="Charcot's triad components present — acute cholangitis cannot be excluded.",
    ),
    ClinicalRule(
        zones=["upper_abdomen"],
        predicate=lambda a: (
            _a(a, "onset", "sudden") and _a(a, "severity", "severe", "max")
        ),
        level=LEVEL_ER,
        confidence=0.80,
        conditions=["Acute pancreatitis", "Perforated peptic ulcer", "Mesenteric ischemia"],
        icd10_hints=["K85.9", "K26.1"],
        reasoning="Sudden severe upper abdominal pain requires same-day emergency evaluation.",
    ),
    ClinicalRule(
        zones=["upper_abdomen"],
        predicate=lambda a: _a(a, "assoc", "gallbladder"),
        level=LEVEL_DOCTOR,
        confidence=0.78,
        conditions=["Cholelithiasis", "Cholecystitis"],
        icd10_hints=["K80.20", "K81.0"],
        reasoning="Biliary colic pattern — requires ultrasound and clinical evaluation.",
    ),

    # ── LOWER ABDOMEN ─────────────────────────────────────────────────────────

    ClinicalRule(
        zones=["lower_abdomen"],
        predicate=lambda a: (
            _a(a, "assoc", "peritoneal") or
            (_a(a, "assoc", "appendix_mig") and _a(a, "location", "lr"))
        ),
        level=LEVEL_ER,
        confidence=0.91,
        conditions=["Acute appendicitis", "Peritonitis"],
        icd10_hints=["K37", "K65.9"],
        reasoning="Rebound tenderness + fever or classic appendicitis migration pattern.",
    ),
    ClinicalRule(
        zones=["lower_abdomen"],
        predicate=lambda a: _a(a, "assoc", "obstruction"),
        level=LEVEL_ER,
        confidence=0.88,
        conditions=["Bowel obstruction", "Paralytic ileus"],
        icd10_hints=["K56.60"],
        reasoning="Failure to pass gas or stool >24 hrs with pain — obstruction protocol.",
    ),
    ClinicalRule(
        zones=["lower_abdomen"],
        predicate=lambda a: (
            _a(a, "location", "lr") and _a(a, "onset", "gradual", "sudden")
        ),
        level=LEVEL_DOCTOR,
        confidence=0.72,
        conditions=["Possible early appendicitis", "Right ovarian pathology", "Inguinal hernia"],
        icd10_hints=["K37", "N83.20"],
        reasoning="RLQ pain without peritoneal signs — still requires physician evaluation.",
    ),

    # ── GENERAL / WHOLE BODY ─────────────────────────────────────────────────

    ClinicalRule(
        zones=["general"],
        predicate=lambda a: (
            _a(a, "assoc", "confusion2") or _a(a, "severity", "bedbound")
        ),
        level=LEVEL_ER,
        confidence=0.86,
        conditions=["Possible sepsis", "Severe systemic illness", "Encephalopathy"],
        icd10_hints=["A41.9", "R41.3"],
        reasoning="Altered mental status or inability to get out of bed — systemic severity marker.",
    ),
    ClinicalRule(
        zones=["general"],
        predicate=lambda a: (
            _a(a, "assoc", "sob") and _a(a, "assoc2", "high_fever")
        ),
        level=LEVEL_ER,
        confidence=0.84,
        conditions=["Possible sepsis", "Severe pneumonia"],
        icd10_hints=["A41.9", "J18.9"],
        reasoning="Dyspnea at rest with high fever — sepsis screening criteria met.",
    ),
    ClinicalRule(
        zones=["general"],
        predicate=lambda a: _a(a, "primary", "wt_loss"),
        level=LEVEL_DOCTOR,
        confidence=0.75,
        conditions=["Unexplained weight loss — requires workup", "Malignancy screen", "Endocrine / GI"],
        icd10_hints=["R63.4"],
        reasoning="Unintentional weight loss >5% requires physician workup for systemic cause.",
    ),
    ClinicalRule(
        zones=["general"],
        predicate=lambda a: (
            _a(a, "primary", "fever") and _a(a, "duration", "weeks", "chronic")
        ),
        level=LEVEL_DOCTOR,
        confidence=0.78,
        conditions=["Fever of unknown origin", "Chronic infection", "Autoimmune disease"],
        icd10_hints=["R50.9"],
        reasoning="Prolonged fever requires physician workup for infectious, autoimmune, or malignant cause.",
    ),

    # ── MUSCULOSKELETAL (all limb zones + back) ───────────────────────────────

    ClinicalRule(
        zones=["r_arm", "l_arm", "r_forearm", "l_forearm", "r_hand", "l_hand",
               "r_thigh", "l_thigh", "r_leg", "l_leg"],
        predicate=lambda a: (
            _a(a, "cause", "trauma") and _a(a, "severity", "severe", "max")
        ),
        level=LEVEL_ER,
        confidence=0.82,
        conditions=["Possible fracture with neurovascular compromise", "Significant trauma"],
        icd10_hints=["T14.2"],
        reasoning="High-force trauma with severe pain — fracture/dislocation requires imaging.",
    ),
    ClinicalRule(
        zones=["r_arm", "l_arm", "r_forearm", "l_forearm", "r_hand", "l_hand",
               "r_thigh", "l_thigh", "r_leg", "l_leg"],
        predicate=lambda a: (
            _a(a, "type", "numbness", "weakness") and _a(a, "cause", "atraumatic")
        ),
        level=LEVEL_DOCTOR,
        confidence=0.74,
        conditions=["Peripheral neuropathy", "Radiculopathy", "Vascular compromise"],
        icd10_hints=["G54.2", "G57.9"],
        reasoning="Atraumatic numbness/weakness may indicate neurological or vascular pathology.",
    ),
    ClinicalRule(
        zones=["r_arm", "l_arm", "r_forearm", "l_forearm", "r_hand", "l_hand",
               "r_thigh", "l_thigh", "r_leg", "l_leg"],
        predicate=lambda a: _a(a, "cause", "trauma", "minor_trauma"),
        level=LEVEL_DOCTOR,
        confidence=0.68,
        conditions=["Possible fracture", "Ligament sprain", "Contusion"],
        icd10_hints=["T14.2", "T14.3"],
        reasoning="Traumatic injury requires imaging to exclude fracture.",
    ),
    ClinicalRule(
        zones=["r_arm", "l_arm", "r_forearm", "l_forearm", "r_hand", "l_hand",
               "r_thigh", "l_thigh", "r_leg", "l_leg"],
        predicate=lambda a: _a(a, "cause", "overuse"),
        level=LEVEL_OTC,
        confidence=0.80,
        conditions=["Overuse injury", "Tendinopathy", "Muscle strain"],
        icd10_hints=["M70.9", "M79.3"],
        reasoning="Overuse pattern with gradual onset — RICE protocol appropriate.",
    ),
]


# ─────────────────────────────────────────────────────────────────────────────
# ENGINE
# ─────────────────────────────────────────────────────────────────────────────

class RuleEngine:
    """
    Evaluates symptom answers against clinical rules.

    Algorithm:
    1. Build answers dict from the Q&A list.
    2. Iterate rules in priority order; apply zone filter.
    3. If a red_flag rule matches → return immediately (hard interrupt).
    4. Collect all non-red-flag matching rules; use the highest-urgency match.
    5. If no rule matches → apply a conservative default based on urgency hint sum.
    """

    def evaluate(self, zone_id: str, answers: list[dict]) -> RuleResult:
        answers_dict: dict[str, str] = {
            a["question_id"]: a["answer_value"] for a in answers
        }

        matching_rules: list[ClinicalRule] = []

        for rule in RULES:
            # Zone filter
            if rule.zones != ["*"] and zone_id not in rule.zones:
                continue

            if not rule.predicate(answers_dict):
                continue

            # Red flag → return immediately
            if rule.red_flag:
                return RuleResult(
                    level=LEVEL_911,
                    confidence=rule.confidence,
                    red_flag=True,
                    conditions=rule.conditions,
                    icd10_hints=rule.icd10_hints,
                    reasoning=rule.reasoning,
                )

            matching_rules.append(rule)

        if not matching_rules:
            return self._default_result(zone_id, answers_dict)

        # Use highest-urgency matching rule
        best = max(matching_rules, key=lambda r: (r.level, r.confidence))
        return RuleResult(
            level=best.level,
            confidence=best.confidence,
            red_flag=False,
            conditions=best.conditions,
            icd10_hints=best.icd10_hints,
            reasoning=best.reasoning,
        )

    @staticmethod
    def _default_result(zone_id: str, answers: dict) -> RuleResult:
        """
        Conservative default when no specific rule matches.
        Maps raw urgency-hint sum from the frontend scoring to a level.
        """
        urgency_map = {
            "pressure": 3, "sharp": 1, "burning": 0, "dull": 1,
            "cardiac_rad": 5, "back_rad": 4, "sob": 3, "cardiac_assoc": 5,
            "sudden": 2, "acute": 1, "severe": 2, "max": 3,
            "trauma": 2, "weakness": 2, "numbness": 1,
        }
        total = sum(urgency_map.get(v, 0) for v in answers.values())

        if total <= 0:
            level = LEVEL_HOME
        elif total <= 2:
            level = LEVEL_OTC
        elif total <= 5:
            level = LEVEL_DOCTOR
        elif total <= 9:
            level = LEVEL_ER
        else:
            level = LEVEL_911

        confidence = 0.55  # Low confidence — no specific rule matched

        return RuleResult(
            level=level,
            confidence=confidence,
            red_flag=False,
            conditions=["Symptom pattern did not match a specific clinical rule"],
            icd10_hints=[],
            reasoning=(
                f"No specific rule matched for zone '{zone_id}'. "
                f"Conservative urgency score of {total} maps to level {level}."
            ),
        )


rule_engine = RuleEngine()
