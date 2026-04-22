from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Opt:
    label: str
    value: str
    urgency: int = 0
    next_node: Optional[str] = None
    red_flag: bool = False
    diagnoses: list[str] = field(default_factory=list)
    treatment: str = ""

    def to_dict(self):
        return {
            "label": self.label, "value": self.value,
            "urgency": self.urgency, "next_node": self.next_node,
            "red_flag": self.red_flag, "diagnoses": self.diagnoses,
            "treatment": self.treatment,
        }


@dataclass
class Node:
    question: str
    options: list[Opt]
    subregion: bool = False

    def to_dict(self):
        return {
            "question": self.question,
            "options": [o.to_dict() for o in self.options],
            "subregion": self.subregion,
        }


Flow = dict[str, Node]


@dataclass
class TraversalResult:
    diagnoses: list[str]
    treatment: str
    urgency_score: int
    red_flag: bool
    reached_terminal: bool
    path: list[str]


def traverse(flow: Flow, answers: list[dict]) -> TraversalResult:
    node_id = "start"
    urgency = 0
    red_flag = False
    path = []

    for ans in answers:
        node = flow.get(node_id)
        if not node:
            break
        val = ans.get("answer_value", "")
        matched = False
        for opt in node.options:
            if opt.value == val:
                urgency += opt.urgency
                path.append(f"{node_id}→{val}")
                if opt.red_flag:
                    red_flag = True
                if opt.next_node is None:
                    return TraversalResult(
                        diagnoses=opt.diagnoses,
                        treatment=opt.treatment,
                        urgency_score=urgency,
                        red_flag=red_flag,
                        reached_terminal=True,
                        path=path,
                    )
                node_id = opt.next_node
                matched = True
                break
        if not matched:
            break

    return TraversalResult(
        diagnoses=[], treatment="", urgency_score=urgency,
        red_flag=red_flag, reached_terminal=False, path=path,
    )


# ── HEAD ─────────────────────────────────────────────────────────────────────
HEAD: Flow = {
    "start": Node("Where on your head is the problem?", [
        Opt("Forehead", "forehead", 0, "fh_type"),
        Opt("Temple (left or right side)", "temple", 0, "tp_type"),
        Opt("Back of head or base of skull", "back", 0, "bk_onset"),
        Opt("Top / crown of head", "top", 0, "top_type"),
        Opt("Around eye or face", "eye_face", 0, "ef_area"),
    ], subregion=True),

    # ── Forehead branch ──────────────────────────────────────────────────────
    "fh_type": Node("What type of sensation?", [
        Opt("Pain", "pain", 0, "fh_pain"),
        Opt("Pressure or fullness", "pressure", 1, "fh_pressure"),
        Opt("Warmth or fever feeling", "fever", 0, "fh_fever"),
    ]),
    "fh_pain": Node("How would you describe the pain?", [
        Opt("Dull and constant", "dull", 0, "fh_dull_assoc"),
        Opt("Throbbing or pulsating", "throb", 2, "fh_throb_assoc"),
        Opt("Stabbing or sharp", "stab", 2, "fh_stab_onset"),
        Opt("Pinching or squeezing", "pinch", 1, None,
            diagnoses=["Tension headache"],
            treatment="Ibuprofen 400–600mg or acetaminophen 500–1000mg. Rest in a quiet space, stay hydrated, apply warm compress to neck. Usually resolves within hours."),
    ]),
    "fh_dull_assoc": Node("Any of these accompanying it?", [
        Opt("Fatigue, stress, or eye strain", "stress", 0, None,
            diagnoses=["Tension headache"],
            treatment="Ibuprofen 400–600mg or acetaminophen. Rest, hydrate, take a screen break. Warm compress to neck and shoulders."),
        Opt("Skipped meals or dehydration", "dehydration", 0, None,
            diagnoses=["Dehydration headache"],
            treatment="Drink 16–32 oz of water now. Eat a light meal. Ibuprofen 400mg if needed. Rest. Should improve within 30–60 minutes."),
        Opt("None of the above", "none", 0, None,
            diagnoses=["Tension headache"],
            treatment="Ibuprofen 400–600mg or acetaminophen. Rest in a quiet room, hydrate."),
    ]),
    "fh_throb_assoc": Node("Do you have nausea, light sensitivity, or sound sensitivity?", [
        Opt("Yes — one or more", "yes", 2, None,
            diagnoses=["Migraine", "Migraine without aura"],
            treatment="Take ibuprofen 400–600mg at onset. Move to a dark, quiet room. Cold compress on forehead. Avoid screens. See doctor for prescription triptans if migraines are recurrent."),
        Opt("No associated symptoms", "no", 1, None,
            diagnoses=["Vascular headache", "Tension headache"],
            treatment="Ibuprofen 400–600mg. Rest and hydrate. See doctor if recurring."),
    ]),
    "fh_stab_onset": Node("How severe and how did it start?", [
        Opt("Sudden — worst headache of my life", "thunderclap", 10, None,
            red_flag=True,
            diagnoses=["Possible subarachnoid hemorrhage"],
            treatment="Call 911 immediately. Do not drive yourself."),
        Opt("Severe, built up over minutes", "severe_grad", 3, None,
            diagnoses=["Cluster headache", "Neuralgic pain"],
            treatment="Seek same-day physician evaluation. OTC pain relievers are often ineffective for cluster headaches. Doctor may prescribe oxygen therapy or triptans."),
        Opt("Mild to moderate", "mild_mod", 1, None,
            diagnoses=["Tension headache", "Neuralgic pain"],
            treatment="Ibuprofen 400–600mg. Warm compress. Rest. See doctor if persists more than 3 days."),
    ]),
    "fh_pressure": Node("Do you have nasal congestion or a runny nose?", [
        Opt("Yes", "congestion", 0, None,
            diagnoses=["Acute sinusitis", "Sinus headache"],
            treatment="Oral decongestant (pseudoephedrine). Saline nasal rinse twice daily. Steam inhalation. Ibuprofen for pain. See doctor if not improving in 7–10 days or if fever develops."),
        Opt("No congestion", "no", 0, None,
            diagnoses=["Tension headache", "Stress headache"],
            treatment="Ibuprofen 400–600mg or acetaminophen. Rest in a quiet room. Neck stretches. Reduce screen time."),
    ]),
    "fh_fever": Node("Have you taken your temperature?", [
        Opt("Yes — above 103°F / 39.4°C", "high", 4, None,
            diagnoses=["High fever — possible serious infection"],
            treatment="Seek emergency care. Take acetaminophen 500–1000mg for fever reduction while en route. Do not drive yourself if severely unwell."),
        Opt("Yes — 100–103°F / 37.8–39.4°C", "low", 2, None,
            diagnoses=["Febrile headache — viral or bacterial infection"],
            treatment="Acetaminophen 500–1000mg or ibuprofen for fever and pain. Rest and fluids. See doctor if fever persists more than 3 days."),
        Opt("No or normal temperature", "normal", 0, None,
            diagnoses=["Tension headache"],
            treatment="Ibuprofen 400–600mg. Rest and hydrate."),
    ]),

    # ── Temple branch ────────────────────────────────────────────────────────
    "tp_type": Node("Describe the temple pain:", [
        Opt("Throbbing or pulsating", "throb", 2, "tp_throb_assoc"),
        Opt("Dull ache", "dull", 0, "tp_dull_cause"),
        Opt("Brief stabbing jolts, like electric shocks", "stab", 2, "tp_stab_context"),
        Opt("Constant pressure", "pressure", 1, None,
            diagnoses=["Tension headache"],
            treatment="Ibuprofen 400–600mg. Scalp massage. Reduce jaw clenching. Warm compress to neck and shoulders."),
    ]),
    "tp_throb_assoc": Node("Any nausea, visual changes, or light/sound sensitivity?", [
        Opt("Yes — one or more", "yes", 2, None,
            diagnoses=["Migraine", "Migraine with aura"],
            treatment="Take ibuprofen 400–600mg at onset. Dark, quiet room. Cold compress. Avoid screens. See doctor for triptans if migraines are frequent."),
        Opt("No — pain only", "no", 1, None,
            diagnoses=["Tension headache", "Vascular headache"],
            treatment="Ibuprofen 400–600mg. Rest and hydrate."),
    ]),
    "tp_dull_cause": Node("Did it come on with jaw or ear pain?", [
        Opt("Yes — jaw pain, ear pain, or clicking jaw", "jaw", 1, None,
            diagnoses=["Temporomandibular joint (TMJ) disorder"],
            treatment="Soft foods only. Ibuprofen 400–600mg. Avoid gum and hard foods. Warm compress to jaw. See dentist or doctor within 1–2 weeks."),
        Opt("No jaw/ear involvement", "no", 0, None,
            diagnoses=["Tension headache"],
            treatment="Ibuprofen 400–600mg. Scalp massage. Reduce stress. Warm compress."),
    ]),
    "tp_stab_context": Node("Any of these apply?", [
        Opt("Over 50, with tender scalp or jaw pain while chewing", "arteritis", 5, None,
            diagnoses=["Possible temporal arteritis (giant cell arteritis)"],
            treatment="Seek same-day emergency evaluation. Temporal arteritis requires urgent treatment to prevent permanent vision loss."),
        Opt("Sudden and worst ever", "thunderclap", 10, None,
            red_flag=True,
            diagnoses=["Possible subarachnoid hemorrhage"],
            treatment="Call 911 immediately."),
        Opt("Brief jolts, under 50, otherwise well", "neuralgia", 2, None,
            diagnoses=["Trigeminal neuralgia", "Occipital neuralgia"],
            treatment="See doctor for evaluation. Prescription anticonvulsants (carbamazepine) are first-line. Avoid cold air triggers."),
    ]),

    # ── Back of head branch ──────────────────────────────────────────────────
    "bk_onset": Node("How did the back-of-head pain start?", [
        Opt("Sudden — worst headache of my life", "thunderclap", 10, None,
            red_flag=True,
            diagnoses=["Possible subarachnoid hemorrhage"],
            treatment="Call 911 immediately."),
        Opt("Gradual, with stiff neck and fever", "meningism", 9, None,
            red_flag=True,
            diagnoses=["Possible bacterial meningitis"],
            treatment="Call 911 immediately."),
        Opt("After a head impact or car accident", "trauma", 3, "bk_trauma_loc"),
        Opt("Gradual, no fever, no injury", "gradual", 0, "bk_pain_type"),
    ]),
    "bk_trauma_loc": Node("Did you lose consciousness or feel confused after the impact?", [
        Opt("Yes", "yes", 5, None,
            diagnoses=["Possible concussion or intracranial injury"],
            treatment="Go to the ER immediately."),
        Opt("No", "no", 2, None,
            diagnoses=["Post-traumatic headache", "Whiplash"],
            treatment="Acetaminophen (not ibuprofen in first 24h post-injury). Rest. Ice pack 20 min on/off. See doctor if pain worsens or persists beyond 24 hours."),
    ]),
    "bk_pain_type": Node("What does the back-of-head pain feel like?", [
        Opt("Throbbing or pulsating", "throb", 1, None,
            diagnoses=["Occipital migraine"],
            treatment="Ibuprofen 400–600mg. Dark, quiet room. Cold compress at base of skull. See doctor for recurrent migraines."),
        Opt("Dull ache with neck tension or stiffness", "dull", 0, None,
            diagnoses=["Cervicogenic headache", "Tension headache"],
            treatment="Ibuprofen 400–600mg. Gentle neck stretches. Heat to upper back. Improve posture. Massage. Usually improves over 1–3 days."),
        Opt("Sharp or shooting down into neck", "sharp", 2, None,
            diagnoses=["Occipital neuralgia"],
            treatment="Ibuprofen or naproxen. Warm compress at base of skull. See doctor if not improving — nerve block may help."),
    ]),

    # ── Top / crown branch ───────────────────────────────────────────────────
    "top_type": Node("Describe the top-of-head sensation:", [
        Opt("Pressure band around the whole head", "band", 0, None,
            diagnoses=["Tension headache"],
            treatment="Ibuprofen 400–600mg or acetaminophen. Rest, hydrate, reduce stress. Scalp massage."),
        Opt("Throbbing at the top", "throb", 1, None,
            diagnoses=["Migraine", "Vascular headache"],
            treatment="Ibuprofen 400–600mg. Dark, quiet room. Cold compress. See doctor for triptans if recurrent."),
        Opt("Sudden, severe — worst ever", "thunderclap", 10, None,
            red_flag=True,
            diagnoses=["Possible subarachnoid hemorrhage"],
            treatment="Call 911 immediately."),
        Opt("Came on during or right after exercise", "exertional", 2, None,
            diagnoses=["Exertional headache", "Effort migraine"],
            treatment="Rest and hydrate. Ibuprofen 400mg. See doctor if recurring — rule out vascular cause."),
    ]),

    # ── Eye/Face branch ──────────────────────────────────────────────────────
    "ef_area": Node("Is it in your eye or on your face?", [
        Opt("In or directly around my eye", "eye", 0, "eye_type"),
        Opt("Jaw, cheek, or other facial area", "face", 0, "face_type"),
    ]),
    "eye_type": Node("What are you experiencing with your eye?", [
        Opt("Severe pain, red eye, and blurred or haloed vision", "glaucoma", 8, None,
            red_flag=True,
            diagnoses=["Possible acute angle-closure glaucoma"],
            treatment="Go to the ER immediately. This is an ophthalmic emergency that can cause permanent blindness."),
        Opt("Pain behind eye with one-sided headache", "cluster", 3, None,
            diagnoses=["Cluster headache"],
            treatment="Seek same-day physician evaluation. 100% oxygen and triptans are first-line treatment. OTC pain relievers are usually ineffective."),
        Opt("Eye pain with light sensitivity", "photophobia", 2, None,
            diagnoses=["Migraine with aura", "Uveitis", "Optic neuritis"],
            treatment="Dark room, cold compress. Ibuprofen. See doctor today — eye inflammation requires evaluation."),
        Opt("Burning, gritty, or tired feeling", "dry_eye", 0, None,
            diagnoses=["Dry eye syndrome", "Digital eye strain"],
            treatment="OTC artificial tear eye drops. 20-20-20 rule: every 20 min, look at something 20ft away for 20 sec. Rest eyes."),
    ]),
    "face_type": Node("Which part of the face?", [
        Opt("Jaw pain or clicking / popping jaw", "jaw", 1, None,
            diagnoses=["TMJ disorder", "Dental issue"],
            treatment="Soft foods only. Ibuprofen 400–600mg. Avoid gum and hard foods. Warm compress to jaw. See dentist within 1 week."),
        Opt("Cheek or under-eye pressure / pain", "sinus", 0, None,
            diagnoses=["Maxillary sinusitis"],
            treatment="Nasal decongestant. Saline rinse. Ibuprofen. Steam inhalation. See doctor if not improving in 7–10 days."),
        Opt("Facial numbness, drooping, or weakness", "nerve", 5, None,
            diagnoses=["Possible Bell's palsy", "TIA", "Stroke"],
            treatment="Seek immediate emergency evaluation. Facial drooping with headache may indicate stroke."),
    ]),
}

# ── CHEST ────────────────────────────────────────────────────────────────────
CHEST: Flow = {
    "start": Node("Where is the chest discomfort?", [
        Opt("Center or left side", "center_left", 0, "ch_sensation"),
        Opt("Right side of chest", "right", 0, "ch_right"),
        Opt("Upper chest rising into throat", "upper", 0, "ch_upper"),
    ]),
    "ch_sensation": Node("What does it feel like?", [
        Opt("Pressure, tightness, or squeezing", "pressure", 3, "ch_pressure_rad"),
        Opt("Sharp or stabbing", "sharp", 1, "ch_sharp_trigger"),
        Opt("Burning", "burning", 0, "ch_burn_trigger"),
        Opt("Dull ache", "dull", 1, "ch_dull_trigger"),
    ]),
    "ch_pressure_rad": Node("Does the discomfort spread anywhere?", [
        Opt("Left arm, jaw, neck, or shoulder", "cardiac_rad", 8, None,
            red_flag=True,
            diagnoses=["Possible acute coronary syndrome (ACS)", "Heart attack"],
            treatment="Call 911 immediately. Chew one full-strength aspirin 325mg if not allergic and not bleeding. Sit or lie still."),
        Opt("Between shoulder blades (back)", "back_rad", 7, None,
            red_flag=True,
            diagnoses=["Possible aortic dissection"],
            treatment="Call 911 immediately. Do not eat or drink anything."),
        Opt("Into throat or neck only", "throat_rad", 3, "ch_pressure_assoc"),
        Opt("Stays in the chest only", "local", 2, "ch_pressure_assoc"),
    ]),
    "ch_pressure_assoc": Node("Any of these right now?", [
        Opt("Sweating, nausea, or lightheadedness", "cardiac_assoc", 7, None,
            red_flag=True,
            diagnoses=["Possible acute coronary syndrome", "NSTEMI"],
            treatment="Call 911 immediately. Chew one aspirin 325mg if not allergic."),
        Opt("Shortness of breath at rest", "sob", 4, None,
            diagnoses=["Unstable angina", "Pulmonary embolism"],
            treatment="Go to the ER immediately. Do not drive yourself."),
        Opt("None of these", "none", 1, "ch_pressure_onset"),
    ]),
    "ch_pressure_onset": Node("How did it start?", [
        Opt("Sudden, within seconds or minutes", "sudden", 3, None,
            diagnoses=["Unstable angina", "ACS", "Pulmonary embolism"],
            treatment="Go to the ER now. Do not drive yourself."),
        Opt("During or after physical exertion", "exertional", 3, None,
            diagnoses=["Stable angina", "Exertional angina"],
            treatment="Rest now. Go to the ER. Do not exercise until cardiologist evaluates you."),
        Opt("Gradual build-up, now constant", "gradual", 2, None,
            diagnoses=["Unstable angina", "Pericarditis"],
            treatment="Go to the ER today."),
    ]),
    "ch_sharp_trigger": Node("What brings on the sharp pain?", [
        Opt("Deep breath, cough, or movement", "pleuritic", 2, "ch_pleuritic_assoc"),
        Opt("Pressing or touching the chest wall", "palpable", 0, None,
            diagnoses=["Costochondritis", "Musculoskeletal chest pain"],
            treatment="Ibuprofen 400–600mg three times daily with food. Rest. Avoid heavy lifting. Ice or heat to chest wall. Typically resolves over days to weeks."),
        Opt("No clear trigger", "no_trigger", 2, "ch_sharp_assoc"),
    ]),
    "ch_pleuritic_assoc": Node("Any shortness of breath or recent travel / leg swelling?", [
        Opt("Shortness of breath", "sob", 4, None,
            diagnoses=["Possible pulmonary embolism", "Pleuritis", "Pneumothorax"],
            treatment="Go to the ER immediately."),
        Opt("Recent long trip or leg swelling", "dvt_risk", 4, None,
            diagnoses=["Possible pulmonary embolism"],
            treatment="Go to the ER immediately. Leg swelling plus chest pain is an emergency."),
        Opt("Neither", "none", 1, None,
            diagnoses=["Pleuritis", "Viral pleurisy", "Musculoskeletal"],
            treatment="Ibuprofen 400–600mg. Rest. Shallow breathing for comfort. See doctor today if worsening or fever develops."),
    ]),
    "ch_sharp_assoc": Node("Any fever, cough, or recent illness?", [
        Opt("Fever or productive cough", "infection", 2, None,
            diagnoses=["Pneumonia", "Pleuritis"],
            treatment="See doctor today. Antibiotics may be required. Ibuprofen for pain and fever."),
        Opt("No", "none", 1, None,
            diagnoses=["Musculoskeletal chest pain", "Anxiety"],
            treatment="Ibuprofen 400–600mg. Rest. Slow deep breathing. See doctor if persists beyond 24 hours."),
    ]),
    "ch_burn_trigger": Node("When does the burning occur?", [
        Opt("After eating, lying down, or bending over", "positional", 0, None,
            diagnoses=["Gastroesophageal reflux disease (GERD)", "Acid reflux"],
            treatment="Antacid (Tums or Rolaids) immediately. Avoid lying down after meals. Elevate head of bed 6–8 inches. OTC omeprazole 20mg daily. See doctor if persists."),
        Opt("Constant, not related to food", "constant", 1, "ch_burn_assoc"),
    ]),
    "ch_burn_assoc": Node("Any difficulty swallowing or vomiting blood?", [
        Opt("Difficulty swallowing", "dysphagia", 3, None,
            diagnoses=["Esophagitis", "Esophageal spasm", "Esophageal stricture"],
            treatment="See doctor today. Avoid solid foods until evaluated. OTC omeprazole for relief."),
        Opt("Vomiting blood", "hematemesis", 9, None,
            red_flag=True,
            diagnoses=["Upper GI hemorrhage", "Esophageal tear"],
            treatment="Call 911 immediately."),
        Opt("Neither", "none", 1, None,
            diagnoses=["GERD", "Esophageal spasm"],
            treatment="OTC proton pump inhibitor (omeprazole 20mg daily before breakfast). Avoid spicy food, alcohol, and caffeine. See doctor if not improving in 2 weeks."),
    ]),
    "ch_dull_trigger": Node("What brings it on?", [
        Opt("During or after exercise", "exertional", 3, None,
            diagnoses=["Stable angina", "Possible ACS"],
            treatment="Rest now. See cardiologist urgently. Go to ER if pain continues at rest."),
        Opt("Constant, worse lying flat, better leaning forward", "pericarditis", 3, None,
            diagnoses=["Pericarditis"],
            treatment="See doctor today. Ibuprofen may help but requires clinical evaluation first."),
        Opt("Random, brief, no clear pattern", "random", 1, None,
            diagnoses=["Musculoskeletal chest pain", "Anxiety-related chest pain"],
            treatment="Monitor for 24 hours. See doctor if recurring. Deep breathing exercises. Ibuprofen if tender to touch."),
    ]),
    "ch_right": Node("What accompanies the right-sided chest pain?", [
        Opt("Fever + cough + worse on deep breath", "pneumonia_r", 3, None,
            diagnoses=["Right-sided pneumonia", "Pleuritis"],
            treatment="See doctor today or go to urgent care. Antibiotics may be required."),
        Opt("Sharp under right ribs — worse after fatty meals", "gallbladder", 2, None,
            diagnoses=["Gallbladder disease", "Biliary colic", "Cholecystitis"],
            treatment="See doctor today. Avoid fatty foods. Go to ER if fever develops or pain becomes constant."),
        Opt("Dull ache with no clear trigger", "dull_r", 0, None,
            diagnoses=["Musculoskeletal", "Liver tenderness"],
            treatment="Monitor. Ibuprofen 400mg. See doctor if persistent or fever develops."),
    ]),
    "ch_upper": Node("Describe the upper chest / throat sensation:", [
        Opt("Burning rising into throat — worse after eating", "gerd_upper", 0, None,
            diagnoses=["GERD", "Heartburn"],
            treatment="Antacid immediately. Avoid triggers: spicy, fatty foods, caffeine, alcohol. OTC omeprazole. Elevate head of bed."),
        Opt("Tightness with anxiety or stress", "anxiety", 1, None,
            diagnoses=["Anxiety", "Panic attack", "Musculoskeletal"],
            treatment="Slow deep breathing (4 counts in, 6 out). Sit upright. Cool environment. If first occurrence or severe, see doctor."),
        Opt("Something stuck or difficulty swallowing", "dysphagia", 3, None,
            diagnoses=["Esophageal obstruction", "Esophagitis"],
            treatment="See doctor today. Avoid solid foods. Go to ER if unable to swallow liquids."),
    ]),
}

# ── NECK ─────────────────────────────────────────────────────────────────────
NECK: Flow = {
    "start": Node("What is your main neck symptom?", [
        Opt("Pain or stiffness", "pain", 0, "nk_pain_cause"),
        Opt("Sore throat or difficulty swallowing", "throat", 0, "nk_throat"),
        Opt("Swelling or lump in the neck", "swelling", 2, "nk_swelling"),
        Opt("Stiff neck + fever + headache", "meningism", 9, None,
            red_flag=True,
            diagnoses=["Possible bacterial meningitis"],
            treatment="Call 911 immediately."),
    ]),
    "nk_pain_cause": Node("What caused the neck pain?", [
        Opt("Woke up with it or slept awkwardly", "positional", 0, None,
            diagnoses=["Acute torticollis", "Muscle strain"],
            treatment="Heat 15–20 min every few hours. Ibuprofen 400–600mg. Gentle range-of-motion exercises. Resolves in 2–3 days."),
        Opt("Car accident or physical impact", "trauma", 3, "nk_trauma_neuro"),
        Opt("Built up gradually over days", "gradual", 1, "nk_gradual_neuro"),
        Opt("Sudden with no cause", "sudden", 2, "nk_rom"),
    ]),
    "nk_trauma_neuro": Node("Any arm numbness, tingling, or weakness?", [
        Opt("Yes", "yes", 4, None,
            diagnoses=["Possible cervical spine injury with nerve compression"],
            treatment="Go to the ER. Keep neck still. Do not stretch or manipulate the neck."),
        Opt("No", "no", 2, None,
            diagnoses=["Whiplash", "Cervical strain"],
            treatment="Acetaminophen 500–1000mg (preferred over ibuprofen for acute injury). Soft collar for comfort. Ice first 24h then heat. See doctor within 1–2 days."),
    ]),
    "nk_gradual_neuro": Node("Any arm numbness, tingling, or weakness?", [
        Opt("Yes — down arm or into fingers", "yes", 3, None,
            diagnoses=["Cervical radiculopathy", "Herniated disc"],
            treatment="See doctor today. Ibuprofen 400–600mg. Avoid heavy lifting and overhead work."),
        Opt("No — pain only", "no", 1, None,
            diagnoses=["Cervical muscle strain", "Degenerative disc disease"],
            treatment="Ibuprofen 400–600mg. Heat to neck. Gentle stretching. See doctor if not improving in 1 week."),
    ]),
    "nk_rom": Node("Can you move your neck normally?", [
        Opt("No — severely limited movement, very painful", "limited", 3, None,
            diagnoses=["Acute disc herniation", "Severe muscle spasm"],
            treatment="See doctor today. Ibuprofen 400–600mg. Ice pack 20 min. Avoid rotation."),
        Opt("Yes — just tender", "tender", 1, None,
            diagnoses=["Muscle strain", "Minor ligament sprain"],
            treatment="Ibuprofen 400–600mg. Rest. Heat. Gentle stretching after 24 hours."),
    ]),
    "nk_throat": Node("Describe your throat symptoms:", [
        Opt("Sore, with fever and white patches on tonsils", "strep", 2, None,
            diagnoses=["Possible strep throat", "Tonsillitis"],
            treatment="See doctor today for strep test. Antibiotics required if positive. Ibuprofen for pain. Cold fluids and throat lozenges."),
        Opt("Sore, cold-like — no fever or white patches", "viral", 0, None,
            diagnoses=["Viral pharyngitis", "Common cold"],
            treatment="Gargle warm salt water. Ibuprofen or acetaminophen. Honey and warm liquids. OTC throat lozenges. Rest."),
        Opt("Difficulty swallowing or feeling of obstruction", "dysphagia", 3, None,
            diagnoses=["Peritonsillar abscess", "Epiglottitis"],
            treatment="See doctor today. Go to ER if unable to swallow saliva or if drooling."),
    ]),
    "nk_swelling": Node("How long has the swelling been present?", [
        Opt("Days to 2 weeks, with recent cold or infection", "reactive", 1, None,
            diagnoses=["Reactive lymphadenopathy"],
            treatment="Usually resolves after the infection clears. Ibuprofen for discomfort. See doctor if swelling persists beyond 2 weeks or is hard or non-tender."),
        Opt("More than 2 weeks and not going away", "persistent", 3, None,
            diagnoses=["Persistent lymphadenopathy — workup needed", "Rule out lymphoma, thyroid pathology"],
            treatment="See doctor within 1–3 days. Do not delay evaluation of persistent neck masses."),
        Opt("Sudden onset with pain and warmth", "abscess", 3, None,
            diagnoses=["Possible neck abscess", "Infected lymph node"],
            treatment="See doctor today. May require antibiotics or drainage."),
    ]),
}

# ── UPPER ABDOMEN ────────────────────────────────────────────────────────────
UPPER_ABDOMEN: Flow = {
    "start": Node("Where exactly is the upper abdominal pain?", [
        Opt("Center, just below the breastbone", "epigastric", 0, "ua_epigastric"),
        Opt("Right side, under the ribs", "right", 0, "ua_right"),
        Opt("Left side, under the ribs", "left", 0, "ua_left"),
        Opt("Spreads across the entire upper abdomen", "diffuse", 1, "ua_diffuse"),
    ]),
    "ua_epigastric": Node("What type of epigastric pain?", [
        Opt("Burning, worse after eating or when empty", "burning", 0, "ua_burn"),
        Opt("Severe, sudden — radiates into the back", "severe_back", 5, None,
            diagnoses=["Possible acute pancreatitis", "Peptic ulcer perforation"],
            treatment="Go to the ER immediately."),
        Opt("Dull ache, on and off for weeks", "dull_chronic", 0, None,
            diagnoses=["Gastritis", "Peptic ulcer disease"],
            treatment="OTC antacid or omeprazole 20mg daily. Avoid NSAIDs, alcohol, and spicy food. See doctor for H. pylori test if persists."),
    ]),
    "ua_burn": Node("Any nausea or vomiting?", [
        Opt("Vomiting blood or dark coffee-ground material", "hematemesis", 9, None,
            red_flag=True,
            diagnoses=["Upper GI hemorrhage"],
            treatment="Call 911 immediately."),
        Opt("Nausea and vomiting (no blood)", "nausea", 1, None,
            diagnoses=["GERD", "Gastritis"],
            treatment="OTC antacid (Tums) or famotidine. Eat small meals. Avoid lying down after eating."),
        Opt("Neither", "none", 0, None,
            diagnoses=["GERD", "Acid reflux"],
            treatment="OTC omeprazole 20mg daily before breakfast. Dietary changes. Elevate head of bed."),
    ]),
    "ua_right": Node("Any of these with the right upper pain?", [
        Opt("Fever AND yellowing of skin or eyes", "cholangitis", 6, None,
            diagnoses=["Possible acute cholangitis", "Biliary obstruction"],
            treatment="Go to the ER immediately. This combination requires urgent treatment."),
        Opt("Pain after fatty meals, sometimes radiates to right shoulder", "colic", 2, None,
            diagnoses=["Biliary colic", "Cholelithiasis", "Cholecystitis"],
            treatment="See doctor today. Avoid fatty foods. Go to ER if fever develops or pain becomes constant and severe."),
        Opt("Tender to touch with fever", "tender_fever", 3, None,
            diagnoses=["Cholecystitis", "Hepatitis"],
            treatment="Go to the ER today. May require IV antibiotics or surgery."),
        Opt("Dull and persistent, no fever", "dull", 1, None,
            diagnoses=["Liver tenderness", "Musculoskeletal", "Early gallbladder disease"],
            treatment="See doctor within 1–3 days. Ibuprofen for pain. Avoid alcohol."),
    ]),
    "ua_left": Node("Describe the left upper pain:", [
        Opt("Sharp after eating — better with antacids", "gastric", 0, None,
            diagnoses=["Gastritis", "Peptic ulcer"],
            treatment="OTC antacid or omeprazole. Avoid NSAIDs, alcohol, and spicy food. See doctor if persists."),
        Opt("Dull constant pain with recent illness or injury", "spleen", 2, None,
            diagnoses=["Possible splenomegaly", "Splenic pathology"],
            treatment="See doctor today. Avoid contact sports or strenuous activity."),
        Opt("Severe, radiates to back — worst pain ever", "pancreatitis", 5, None,
            diagnoses=["Acute pancreatitis"],
            treatment="Go to the ER immediately."),
    ]),
    "ua_diffuse": Node("How severe and how did it come on?", [
        Opt("Sudden and severe (8–10 out of 10)", "severe_sudden", 5, None,
            diagnoses=["Possible mesenteric ischemia", "Perforated viscus", "Pancreatitis"],
            treatment="Go to the ER immediately."),
        Opt("Moderate, gradual over hours", "moderate", 2, None,
            diagnoses=["Gastroenteritis", "Gastritis"],
            treatment="Clear fluids only. Ibuprofen or acetaminophen. BRAT diet when able. See doctor if vomiting prevents fluid intake."),
        Opt("Mild, with bloating and gas", "mild", 0, None,
            diagnoses=["IBS", "Functional dyspepsia", "Gas and bloating"],
            treatment="Simethicone (Gas-X). Peppermint tea. Avoid carbonated drinks. Walk to stimulate digestion."),
    ]),
}

# ── LOWER ABDOMEN ────────────────────────────────────────────────────────────
LOWER_ABDOMEN: Flow = {
    "start": Node("Where in the lower abdomen?", [
        Opt("Lower right (between navel and right hip)", "lr", 0, "la_right"),
        Opt("Lower left side", "ll", 0, "la_left"),
        Opt("Around the navel", "umbilical", 0, "la_umbilical"),
        Opt("Across the entire lower abdomen", "diffuse", 0, "la_diffuse"),
        Opt("Pelvic area", "pelvis", 0, "la_pelvis"),
    ]),
    "la_right": Node("Any of these with the lower right pain?", [
        Opt("Started near navel, moved to lower right — getting worse", "appendix_classic", 7, None,
            red_flag=True,
            diagnoses=["Classic appendicitis presentation"],
            treatment="Go to the ER immediately. Nothing to eat or drink."),
        Opt("Fever AND pain worsens when I press then release", "rebound", 7, None,
            red_flag=True,
            diagnoses=["Peritonitis", "Ruptured appendicitis"],
            treatment="Go to the ER immediately."),
        Opt("Moderate pain for 1–2 days, no fever", "moderate", 2, None,
            diagnoses=["Possible early appendicitis", "Ovarian cyst", "Inguinal hernia"],
            treatment="See doctor today. Do not use a heating pad. Avoid food and drink until evaluated."),
        Opt("Mild, comes and goes, no fever", "mild", 1, None,
            diagnoses=["Inguinal hernia", "Muscle strain", "IBS"],
            treatment="See doctor within 1–3 days. Ibuprofen for pain. Monitor for worsening."),
    ]),
    "la_left": Node("Any of these with the lower left pain?", [
        Opt("Fever, tenderness on the left, and constipation", "diverticulitis", 4, None,
            diagnoses=["Diverticulitis"],
            treatment="Go to the ER or see doctor today. Antibiotics and possibly IV fluids required."),
        Opt("Crampy with blood in stool", "blood_stool", 4, None,
            diagnoses=["Inflammatory bowel disease", "Ischemic colitis"],
            treatment="See doctor today. Go to ER if bleeding is significant."),
        Opt("Crampy with changes in bowel habits, no blood", "ibs", 0, None,
            diagnoses=["IBS", "Constipation", "Functional abdominal pain"],
            treatment="Increase fiber and fluids. Heating pad. Simethicone. See doctor if pattern continues."),
        Opt("Sharp, sudden onset", "sudden", 2, None,
            diagnoses=["Possible ovarian pathology", "Muscle spasm"],
            treatment="See doctor today. Ibuprofen for pain."),
    ]),
    "la_umbilical": Node("When did this pain start and how?", [
        Opt("Sudden and severe, spreading outward", "spreading", 4, None,
            diagnoses=["Possible appendicitis", "Mesenteric ischemia"],
            treatment="Go to the ER. Nothing to eat or drink."),
        Opt("Gradual with bloating and gas", "bloating", 0, None,
            diagnoses=["IBS", "Gas", "Constipation"],
            treatment="Simethicone. Increase fluids. Walking. Warm compress. See doctor if recurring."),
        Opt("After a meal, crampy", "post_meal", 0, None,
            diagnoses=["Gastroenteritis", "IBS", "Food intolerance"],
            treatment="Clear fluids. Rest. Avoid trigger foods."),
    ]),
    "la_diffuse": Node("Any inability to pass gas or stool?", [
        Opt("Yes — no bowel movement or gas for more than 24 hours", "obstruction", 6, None,
            diagnoses=["Possible bowel obstruction"],
            treatment="Go to the ER immediately. Nothing to eat or drink."),
        Opt("No — bowels moving normally", "normal", 0, "la_diffuse_type"),
    ]),
    "la_diffuse_type": Node("What type of lower abdominal pain?", [
        Opt("Crampy and wave-like", "crampy", 0, None,
            diagnoses=["Gastroenteritis", "IBS flare"],
            treatment="BRAT diet. OTC antispasmodic. Rest and hydrate."),
        Opt("Constant and worsening", "constant", 3, None,
            diagnoses=["Peritonitis", "Ischemia"],
            treatment="See doctor today or go to ER if severe or worsening."),
        Opt("Burning with urinary symptoms", "uti", 1, None,
            diagnoses=["Urinary tract infection (UTI)", "Cystitis"],
            treatment="See doctor today for urinalysis. Drink plenty of water. OTC phenazopyridine for urinary pain relief."),
    ]),
    "la_pelvis": Node("Which pelvic symptom fits?", [
        Opt("Severe pain + missed period + positive or possible pregnancy", "ectopic", 9, None,
            red_flag=True,
            diagnoses=["Possible ectopic pregnancy"],
            treatment="Go to the ER immediately."),
        Opt("Burning during urination and frequency", "uti_pelvis", 1, None,
            diagnoses=["UTI", "Cystitis"],
            treatment="See doctor today for urinalysis and antibiotics. Drink water. OTC phenazopyridine for pain."),
        Opt("Crampy with menstrual period", "dysmenorrhea", 0, None,
            diagnoses=["Dysmenorrhea (menstrual cramps)"],
            treatment="Ibuprofen 400–600mg — start 1 day before period for best effect. Heating pad. Gentle exercise."),
        Opt("Constant dull ache, not related to cycle", "chronic_pelvic", 2, None,
            diagnoses=["Chronic pelvic pain", "Endometriosis", "Uterine fibroids"],
            treatment="See doctor within 1 week. Ibuprofen for pain management."),
    ]),
}

# ── MSK (shared by all limb zones) ───────────────────────────────────────────
MSK: Flow = {
    "start": Node("What are you experiencing?", [
        Opt("Pain", "pain", 0, "msk_pain_cause"),
        Opt("Swelling with or without pain", "swelling", 1, "msk_swelling"),
        Opt("Numbness or tingling", "numbness", 2, "msk_numbness"),
        Opt("Weakness or inability to use it", "weakness", 3, "msk_weakness"),
    ]),
    "msk_pain_cause": Node("What caused the pain?", [
        Opt("Direct impact — may be broken", "fracture", 3, "msk_fracture"),
        Opt("Twist, stretch, or overextension", "sprain", 1, "msk_sprain"),
        Opt("Overuse or repetitive activity", "overuse", 0, None,
            diagnoses=["Tendinopathy", "Overuse injury", "Stress reaction"],
            treatment="RICE: Rest, Ice (20 min on/off), Compression, Elevation. Ibuprofen 400–600mg three times daily. No high-impact activity for 3–5 days."),
        Opt("No injury — came on by itself", "atraumatic", 1, "msk_atraumatic"),
    ]),
    "msk_fracture": Node("How severe is it — can you bear weight or use it?", [
        Opt("Cannot use or bear weight at all", "severe", 4, None,
            diagnoses=["Possible fracture or dislocation"],
            treatment="Go to the ER for X-ray. Immobilize the area. Apply ice. Do not attempt to set it yourself."),
        Opt("Limited use, point tenderness", "moderate", 2, None,
            diagnoses=["Possible fracture", "Severe contusion"],
            treatment="See doctor today for X-ray. RICE protocol. Ibuprofen for pain. Avoid weight-bearing."),
        Opt("Can still use it, mildly painful", "mild", 1, None,
            diagnoses=["Contusion", "Possible minor fracture", "Bone bruise"],
            treatment="RICE protocol. Ibuprofen 400–600mg. Recheck in 24 hours — see doctor if not improving."),
    ]),
    "msk_sprain": Node("Can you bear weight or use the area?", [
        Opt("No — too painful or gives way", "grade3", 3, None,
            diagnoses=["Grade II–III ligament sprain", "Possible avulsion fracture"],
            treatment="See doctor today for X-ray. RICE. Crutches if lower limb. No weight bearing."),
        Opt("Yes, but painful", "grade2", 1, None,
            diagnoses=["Grade I–II sprain", "Muscle strain"],
            treatment="RICE for 48 hours. Ibuprofen 400–600mg. Gentle range of motion after 48h. See doctor if not improving in 3–5 days."),
    ]),
    "msk_atraumatic": Node("How long has it been present?", [
        Opt("Started today or overnight", "acute", 1, "msk_hot_joint"),
        Opt("Days to weeks", "subacute", 1, None,
            diagnoses=["Tendinitis", "Bursitis", "Inflammatory arthritis"],
            treatment="Ibuprofen 400–600mg. Rest the area. Ice if swollen. See doctor if not improving in 1–2 weeks."),
        Opt("Months or longer", "chronic", 0, None,
            diagnoses=["Osteoarthritis", "Chronic tendinopathy", "Fibromyalgia"],
            treatment="See doctor for evaluation. Low-impact exercise. Ibuprofen or acetaminophen. Physical therapy may help."),
    ]),
    "msk_hot_joint": Node("Is the joint red, warm, and swollen?", [
        Opt("Yes — very red, hot, and swollen", "hot", 3, None,
            diagnoses=["Possible septic arthritis", "Gout", "Pseudogout"],
            treatment="See doctor today or go to urgent care. Septic arthritis requires same-day evaluation."),
        Opt("Mild swelling only", "mild_swelling", 1, None,
            diagnoses=["Reactive arthritis", "Early inflammatory arthritis"],
            treatment="Ibuprofen 400–600mg. Rest and elevate. See doctor if persists beyond 3 days."),
        Opt("No swelling or redness", "none", 0, None,
            diagnoses=["Muscle spasm", "Minor strain", "Referred pain"],
            treatment="Ibuprofen 400–600mg. Heat for muscle pain. Rest. See doctor if no improvement in 3–5 days."),
    ]),
    "msk_swelling": Node("When did the swelling appear?", [
        Opt("Immediately after an impact (within minutes)", "acute_trauma", 3, None,
            diagnoses=["Hemarthrosis", "Significant ligament tear", "Fracture"],
            treatment="Go to the ER or urgent care for X-ray. RICE. Do not weight-bear."),
        Opt("Hours to days after an injury", "delayed", 1, None,
            diagnoses=["Sprain", "Soft tissue injury", "Effusion"],
            treatment="RICE protocol. Ibuprofen 400–600mg. Elevate. See doctor if severe or not improving."),
        Opt("No injury — came on spontaneously", "spontaneous", 2, "msk_spontaneous"),
    ]),
    "msk_spontaneous": Node("Any redness, warmth, or fever?", [
        Opt("Yes — red, warm, with or without fever", "infected", 3, None,
            diagnoses=["Possible cellulitis", "Septic joint", "Gout"],
            treatment="See doctor today. Hot, red, swollen joints require same-day evaluation."),
        Opt("Swelling only, no redness or warmth", "edema", 2, None,
            diagnoses=["Edema", "DVT if in lower leg", "Lymphedema"],
            treatment="Elevate the limb. See doctor today — one-sided leg swelling should rule out DVT."),
    ]),
    "msk_numbness": Node("Describe the numbness or tingling:", [
        Opt("Follows a path down the arm or leg", "radicular", 2, None,
            diagnoses=["Radiculopathy", "Disc herniation", "Nerve compression"],
            treatment="See doctor within 1–3 days. Ibuprofen 400–600mg. Avoid activities that trigger it."),
        Opt("In the hand or foot only", "peripheral", 1, "msk_hand_numb"),
        Opt("Sudden onset in the entire limb", "sudden", 5, None,
            diagnoses=["Possible stroke", "Acute vascular occlusion"],
            treatment="Go to the ER immediately."),
    ]),
    "msk_hand_numb": Node("Is it worse at night or with repetitive hand use?", [
        Opt("Yes — worse at night, better when shaking hand", "carpal", 1, None,
            diagnoses=["Carpal tunnel syndrome"],
            treatment="Wrist splint at night. Ibuprofen 400mg. Avoid repetitive wrist movements. See doctor for evaluation."),
        Opt("No clear pattern", "none", 1, None,
            diagnoses=["Peripheral neuropathy", "Raynaud's phenomenon"],
            treatment="See doctor within 1 week. Keep extremity warm."),
    ]),
    "msk_weakness": Node("Did the weakness come on suddenly or gradually?", [
        Opt("Sudden — within minutes or hours", "sudden", 6, None,
            diagnoses=["Possible stroke", "TIA", "Acute nerve injury"],
            treatment="Go to the ER immediately."),
        Opt("Gradually over days to weeks", "gradual", 2, None,
            diagnoses=["Nerve compression", "Inflammatory myopathy"],
            treatment="See doctor today. Avoid strenuous activity."),
        Opt("After an injury — cannot contract the muscle", "post_injury", 2, None,
            diagnoses=["Complete tendon or muscle tear"],
            treatment="Go to the ER or orthopedic urgent care. Immobilize. Ice."),
    ]),
}

# ── GENERAL (minimal — AI engine handles this zone) ──────────────────────────
GENERAL: Flow = {
    "start": Node("What is your primary concern?", [
        Opt("Fever", "fever", 1, "gen_duration"),
        Opt("Extreme fatigue or weakness", "fatigue", 0, "gen_duration"),
        Opt("Unexplained weight loss", "wt_loss", 2, "gen_duration"),
        Opt("Widespread body aches", "aches", 0, "gen_duration"),
        Opt("Dizziness or lightheadedness", "dizzy", 1, "gen_duration"),
        Opt("Confusion or cognitive changes", "confusion", 3, "gen_assoc"),
    ]),
    "gen_duration": Node("How long have you had this?", [
        Opt("Less than 3 days", "acute", 0, "gen_severity"),
        Opt("3–7 days", "week", 1, "gen_severity"),
        Opt("1–4 weeks", "weeks", 2, "gen_severity"),
        Opt("More than 1 month", "chronic", 3, "gen_severity"),
    ]),
    "gen_severity": Node("How much is this affecting your daily function?", [
        Opt("Minimal — managing most activities", "minimal", -1, "gen_assoc"),
        Opt("Moderate — noticeably slower", "mod", 0, "gen_assoc"),
        Opt("Significant — mostly resting", "significant", 2, "gen_assoc"),
        Opt("Severe — cannot get out of bed", "bedbound", 4, "gen_assoc"),
    ]),
    "gen_assoc": Node("Any of these as well?", [
        Opt("Confusion or disorientation", "confusion2", 5, None,
            diagnoses=["Systemic illness with altered mentation — requires evaluation"],
            treatment="Seek emergency evaluation. Altered mental status is a red flag."),
        Opt("Shortness of breath at rest", "sob", 4, None,
            diagnoses=["Systemic illness with respiratory involvement"],
            treatment="Go to the ER."),
        Opt("Fever above 103°F / 39.4°C or rigors", "high_fever", 3, None,
            diagnoses=["Possible sepsis", "Serious infection"],
            treatment="Seek urgent medical care today."),
        Opt("Night sweats for more than a week", "night_sweats", 2, None,
            diagnoses=["Constitutional symptoms — requires workup"],
            treatment="See doctor within 1–3 days."),
        Opt("None of these", "none", 0, None,
            diagnoses=["Constitutional symptoms requiring clinical evaluation"],
            treatment="See doctor within 1–3 days for complete evaluation."),
    ]),
}

# ── Registry ─────────────────────────────────────────────────────────────────
_MSK_ZONES = {
    "r_arm", "l_arm", "r_forearm", "l_forearm",
    "r_hand", "l_hand", "r_thigh", "l_thigh", "r_leg", "l_leg",
}

ZONE_FLOWS: dict[str, Flow] = {
    "head": HEAD,
    "neck": NECK,
    "chest": CHEST,
    "upper_abdomen": UPPER_ABDOMEN,
    "lower_abdomen": LOWER_ABDOMEN,
    "general": GENERAL,
    **{zone: MSK for zone in _MSK_ZONES},
}


def get_flow(zone_id: str) -> Flow:
    return ZONE_FLOWS.get(zone_id, MSK)


def get_flow_as_dict(zone_id: str) -> dict:
    flow = get_flow(zone_id)
    return {node_id: node.to_dict() for node_id, node in flow.items()}
