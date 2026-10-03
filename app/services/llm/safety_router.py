"""Deterministic clinical safety triage for the chat assistant.

It runs before any doctor search or language-model call, so emergencies and
clinical questions always get a safe, consistent answer, even when the model
is unavailable. English, Banglish (Bangla in Latin letters) and Bangla script
are recognised. MediBook never diagnoses or recommends treatment.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

SafetyRoute = Literal["medical", "emergency", "none"]


@dataclass(slots=True)
class SafetyResult:
    matched: bool
    route: SafetyRoute
    response: str | None = None
    category: str | None = None
    specialty: str | None = None


EMERGENCY_NUMBER = "999"

_EMERGENCY_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("cardiac", (
        r"\bchest\b.{0,25}\b(pain|pains|painful|hurts?|hurting|aches?|aching|tight|tightness|pressure|heavy|heaviness|squeez\w*|burning)\b",
        r"\b(pain|pains|hurts?|hurting|aches?|aching|tightness|pressure|heaviness)\b.{0,25}\bchest\b",
        r"\bheart attack\b",
        r"\bbuke?\s*(betha|batha|byatha|bytha|byetha|chap)\b",
        r"বুক(ে)?\s*(ব্যথা|ব্যাথা|চাপ)",
        r"হার্ট\s*অ্যাটাক",
    )),
    ("breathing", (
        r"\b(can'?t|cannot|can not|unable to|hard to|struggling to)\s+breathe?\b",
        r"\bshort(ness)?\s+of\s+breath\b",
        r"\b(difficulty|trouble|problem)\s+breathing\b",
        r"\bgasping\b",
        r"\bchoking\b",
        r"শ্বাসকষ্ট",
        r"শ্বাস\s*নিতে\s*(পারছি\s*না|কষ্ট)",
    )),
    ("stroke", (
        r"\bstroke\b",
        r"\bface\b.{0,15}\bdroop\w*",
        r"\bslurred\s+speech\b",
        r"\b(numb|numbness|weak|weakness|can'?t move)\b.{0,25}\b(one side|left side|right side)\b",
        r"স্ট্রোক",
    )),
    ("unconscious", (
        r"\bunconscious\b",
        r"\bpassed\s+out\b",
        r"\bfainted\b",
        r"\bnot\s+breathing\b",
        r"\bcollapsed\b",
        r"অজ্ঞান",
    )),
    ("seizure", (
        r"\bseizures?\b",
        r"\bconvulsions?\b",
        r"খিঁচুনি",
    )),
    ("bleeding", (
        r"\b(severe|heavy|heavily|a lot of|lots of|uncontrolled)\s+bleed\w*",
        r"\bbleed\w*\b.{0,15}\b(won'?t stop|not stopping|a lot|heavily)\b",
        r"\b(vomiting|coughing|throwing up)\s+(up\s+)?blood\b",
        r"রক্তক্ষরণ",
        r"রক্ত\s*বমি",
    )),
    ("self_harm", (
        r"\bkill(ing)?\s+myself\b",
        r"\bsuicid\w*",
        r"\bend(ing)?\s+my\s+life\b",
        r"\bwant\s+to\s+die\b",
        r"\b(want|going|thinking)\s+(to\s+|of\s+)?(hurt|harm|harming|hurting)\s+myself\b",
        r"\bself[\s-]?harm\w*",
        r"আত্মহত্যা",
        r"মরে\s*যেতে\s*চাই",
    )),
    ("poisoning", (
        r"\boverdos\w*",
        r"\bpoison\w*",
        r"\b(swallowed|drank|drunk|ate)\b.{0,20}\b(bleach|pills|tablets|kerosene|pesticide|insecticide|chemical)\w*",
        r"বিষ\s*খে",
    )),
    ("allergy", (
        r"\banaphyla\w*",
        r"\b(throat|tongue|lips?)\b.{0,15}\bswell\w*",
        r"\bsevere\s+allergic\b",
    )),
    ("pregnancy", (
        r"\bpregnan\w*\b.{0,40}\b(bleed\w*|severe pain|water broke)",
        r"\b(bleed\w*|severe pain)\b.{0,40}\bpregnan\w*",
    )),
)

_EMERGENCY_DETAIL = {
    "cardiac": "Chest pain that feels crushing, or spreads to your arm, jaw or back, or comes with sweating, breathlessness or nausea, can be a heart attack. Don’t drive yourself.",
    "breathing": "If you can’t speak in full sentences or your lips look blue, call 999 now.",
    "stroke": "Note the time the symptoms started. It matters for treatment.",
    "unconscious": "If the person is not breathing normally, call 999 straight away and follow their instructions.",
    "seizure": "Move hard objects away, don’t put anything in their mouth, and note how long the seizure lasts.",
    "bleeding": "Press firmly on the wound with a clean cloth while help is on the way.",
    "poisoning": "Keep the packet or bottle so the medical team can see what was taken.",
    "allergy": "If there is an adrenaline auto-injector, use it now.",
    "pregnancy": "Bleeding or severe pain in pregnancy needs urgent care.",
}

_FOLLOW_UP_SPECIALTY = {
    "cardiac": ("cardiology", "cardiologist"),
    "breathing": ("pulmonology", "chest specialist"),
    "stroke": ("neurology", "neurologist"),
    "seizure": ("neurology", "neurologist"),
    "pregnancy": ("gynecology", "gynecologist"),
    "self_harm": ("psychiatry", "psychiatrist"),
}

EMERGENCY_RESPONSE = (
    "This could be a medical emergency. Please call 999 now or go to the nearest hospital "
    "emergency department straight away. Don’t wait for an appointment."
)

_EMERGENCY_RESPONSE_BN = (
    "এটি জরুরি অবস্থা হতে পারে। এখনই ৯৯৯ নম্বরে ফোন করুন অথবা নিকটস্থ হাসপাতালের "
    "জরুরি বিভাগে যান। অ্যাপয়েন্টমেন্টের জন্য অপেক্ষা করবেন না।"
)

_CARDIAC_BN = (
    "বুকের চাপ বা ব্যথা যদি হাত, চোয়াল বা পিঠে ছড়িয়ে পড়ে, অথবা ঘাম, শ্বাসকষ্ট বা "
    "বমি ভাব থাকে, তাহলে এটি হার্ট অ্যাটাক হতে পারে। নিজে গাড়ি চালিয়ে যাবেন না।"
)

_SELF_HARM_RESPONSE = (
    "I’m really sorry you’re feeling this way. If you might act on these thoughts or you are in "
    "danger right now, please call 999. Please also tell someone you trust how you are feeling. "
    "You don’t have to go through this alone. When you feel ready, I can help you book an "
    "appointment with a psychiatrist here."
)

_SELF_HARM_RESPONSE_BN = (
    "আপনি এমন কষ্টের মধ্য দিয়ে যাচ্ছেন জেনে আমি সত্যিই দুঃখিত। আপনি যদি নিজের ক্ষতি করার "
    "ঝুঁকিতে থাকেন, এখনই ৯৯৯ নম্বরে ফোন করুন। আপনার বিশ্বস্ত কাউকে আপনার অনুভূতির কথা "
    "জানান। আপনি একা নন।"
)

MEDICAL_RESPONSE = (
    "I can’t diagnose conditions, recommend medicines or doses, or interpret reports. A doctor "
    "needs to do that safely. I can help you find the right doctor here and book a time. "
    "If this feels urgent, call 999."
)

_MEDICAL_RESPONSE_BN = (
    "আমি রোগ নির্ণয়, ওষুধ বা ডোজের পরামর্শ দিতে পারি না। তবে সঠিক ডাক্তার খুঁজে "
    "অ্যাপয়েন্টমেন্ট নিতে সাহায্য করতে পারি। লক্ষণ গুরুতর হলে এখনই ৯৯৯ নম্বরে ফোন করুন।"
)

_MEDICAL_RULES = (
    r"\b(what|which)\s+(medicine|medication|tablet|drug|antibiotic)s?\b",
    r"\b(what|which|how much)\s+(dose|dosage)\b",
    r"\bhow (much|many) .{0,30}\b(should|can) i take\b",
    r"\bwhat should i take\b",
    r"\bside effects?\b",
    r"\bis it safe to take\b",
    r"\bdiagnos\w*",
    r"\bdo i have\b",
    r"\bwhat disease\b",
    r"\binterpret\b.{0,30}\b(report|result|test)s?\b",
    r"\bwhat treatment\b",
    r"\btreatment for\b",
    r"কোন\s*ওষুধ",
)

# Order matters: the first matching specialty wins, so children come first.
_SYMPTOM_RULES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("pediatrics", "pediatrician", (r"\b(my|our)\s+(child|baby|son|daughter|kid|infant)\b",)),
    ("cardiology", "cardiologist", (r"\bpalpitations?\b", r"\bheart\b", r"\bblood pressure\b", r"\bhypertension\b")),
    ("pulmonology", "chest specialist", (r"\bcough\w*", r"\basthma\b", r"\bwheez\w*", r"\blungs?\b")),
    ("dermatology", "dermatologist", (r"\bskin\b", r"\brash\w*", r"\bitch\w*", r"\bacne\b", r"\beczema\b", r"\bhair\s+(fall|loss)\b")),
    ("ENT", "ENT specialist", (r"\bears?\b", r"\bearache\b", r"\bsinus\w*", r"\bthroat\b", r"\btonsil\w*", r"\bhearing\b", r"\bnose\b")),
    ("ophthalmology", "eye specialist", (r"\beyes?\b", r"\bvision\b", r"\bblurr\w*")),
    ("orthopedics", "orthopedic specialist", (r"\bback\s*pain\b", r"\bjoints?\b", r"\bknees?\b", r"\bbones?\b", r"\bfracture\w*", r"\bsprain\w*", r"\bneck\s*pain\b", r"\bshoulder\w*")),
    ("gynecology", "gynecologist", (r"\bpregnan\w*", r"\bperiods?\b", r"\bmenstrua\w*", r"\bpcos\b")),
    ("neurology", "neurologist", (r"\bheadaches?\b", r"\bmigraines?\b", r"\bdizz\w*", r"\bvertigo\b", r"\bnumb\w*")),
    ("gastroenterology", "gastroenterologist", (r"\bstomach\b", r"\babdominal\b", r"\bacidity\b", r"\bgastric\b", r"\bdiarrh\w*", r"\bconstipat\w*", r"\bvomit\w*")),
    ("psychiatry", "psychiatrist", (r"\banxi\w*", r"\bdepress\w*", r"\bpanic\b", r"\binsomnia\b", r"\bcan'?t sleep\b")),
    ("urology", "urologist", (r"\burin\w*", r"\bkidney\s+stones?\b")),
    ("medicine", "medicine specialist", (r"\bfever\b", r"\bcold\b", r"\bflu\b", r"\bweakness\b", r"\bdiabet\w*", r"\bthyroid\b", r"\bjor\b", r"জ্বর")),
)

_SYMPTOM_CUE = re.compile(
    r"\b(i have|i've got|ive got|i got|i am having|i'm having|im having|i feel|i'm feeling|im feeling|feeling|has|have|having|had|"
    r"suffering|hurts?|hurting|aching|aches?|pain|sore|swollen|what (should|can) i do|what to do|is it serious|help me)\b"
    r"|জ্বর|ব্যথা|কষ্ট"
)
_BOOKING_INTENT = re.compile(
    r"\b(book|booking|appointments?|doctors?|find|show|search|available|availability|schedule|slots?|fees?|"
    r"cancel|reschedule|specialists?|cardiologists?|dermatologists?|neurologists?|pediatricians?|gynecologists?|"
    r"gynaecologists?|orthopedics?|orthopaedics?|ent)\b|ডাক্তার|অ্যাপয়েন্টমেন্ট"
)
_BANGLA = re.compile(r"[\u0980-\u09FF]")

_EMERGENCY_COMPILED = tuple((category, tuple(re.compile(p) for p in patterns)) for category, patterns in _EMERGENCY_RULES)
_MEDICAL_COMPILED = tuple(re.compile(p) for p in _MEDICAL_RULES)
_SYMPTOM_COMPILED = tuple((specialty, specialist, tuple(re.compile(p) for p in patterns)) for specialty, specialist, patterns in _SYMPTOM_RULES)

# Kept for modules that read the pattern lists directly.
EMERGENCY_PATTERNS = tuple(p for _, patterns in _EMERGENCY_RULES for p in patterns)
MEDICAL_PATTERNS = _MEDICAL_RULES


def _normalize(message: str) -> str:
    text = message.lower().replace("’", "'").replace("‘", "'")
    return " ".join(text.split())


def _emergency_response(category: str, bangla: bool) -> str:
    if category == "self_harm":
        return _SELF_HARM_RESPONSE_BN if bangla else _SELF_HARM_RESPONSE
    if bangla:
        return f"{_EMERGENCY_RESPONSE_BN} {_CARDIAC_BN}" if category == "cardiac" else _EMERGENCY_RESPONSE_BN
    parts = [EMERGENCY_RESPONSE]
    detail = _EMERGENCY_DETAIL.get(category)
    if detail:
        parts.append(detail)
    follow_up = _FOLLOW_UP_SPECIALTY.get(category)
    if follow_up:
        parts.append(f"Once you are safe, I can help you book a follow-up with a {follow_up[1]} here.")
    return " ".join(parts)


def _symptom_response(specialist: str, search: str, bangla: bool) -> str:
    if bangla:
        return _MEDICAL_RESPONSE_BN
    return (
        f"I can’t diagnose what’s causing this, but a {specialist} is the right doctor to check it. "
        f"Type “find a {search}” and I’ll show who is available here and their next free times. "
        "If it suddenly gets worse or feels severe, call 999 or go to the nearest emergency department."
    )


def safety_route(message: str) -> SafetyResult:
    text = _normalize(message)
    if text == "":
        return SafetyResult(matched=False, route="none")
    bangla = _BANGLA.search(message) is not None

    # "Food poisoning" is not an emergency; keep it out of the emergency scan.
    scan = text.replace("food poisoning", "food illness")
    for category, patterns in _EMERGENCY_COMPILED:
        if any(pattern.search(scan) for pattern in patterns):
            follow_up = _FOLLOW_UP_SPECIALTY.get(category)
            return SafetyResult(
                matched=True,
                route="emergency",
                response=_emergency_response(category, bangla),
                category=category,
                specialty=follow_up[0] if follow_up else None,
            )

    if any(pattern.search(text) for pattern in _MEDICAL_COMPILED):
        return SafetyResult(
            matched=True,
            route="medical",
            response=_MEDICAL_RESPONSE_BN if bangla else MEDICAL_RESPONSE,
            category="clinical_question",
        )

    if _BOOKING_INTENT.search(text) is None and _SYMPTOM_CUE.search(text):
        for specialty, specialist, patterns in _SYMPTOM_COMPILED:
            if any(pattern.search(text) for pattern in patterns):
                return SafetyResult(
                    matched=True,
                    route="medical",
                    response=_symptom_response(specialist, specialist, bangla),
                    category="symptom",
                    specialty=specialty,
                )

    return SafetyResult(matched=False, route="none")
