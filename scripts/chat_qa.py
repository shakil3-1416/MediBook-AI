"""Send a fixed set of patient messages to the chat API and report how each was answered.

Usage: PYTHONPATH=. .venv/bin/python scripts/chat_qa.py API_BASE HOSPITAL_SLUG E2E_ENV_FILE

Each message starts a fresh conversation, signed in as the e2e patient. The report
flags failed answers, safety answers and slow answers so problems are easy to spot.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

MESSAGES = [
    "hi",
    "i'm feeling pain in my chest, what to do",
    "I can't breathe properly",
    "I have a skin rash, what should I do?",
    "I have fever for 3 days",
    "what medicine should I take for a headache?",
    "find a cardiologist",
    "show ENT doctors",
    "which doctors are available tomorrow?",
    "book a dermatologist tomorrow evening",
    "my appointments",
    "what is the consultation fee for cardiology?",
    "where is the hospital?",
    "what's the weather today?",
    "আমার বুকে ব্যথা করছে",
    "doctor dekhate chai",
    "I need a dermatologist",
    "how much does a skin doctor cost",
    "any ENT slots available on monday",
    "I want to book an appointment",
]


def read_env(path: str) -> dict[str, str]:
    values = {}
    with open(path) as handle:
        for line in handle:
            key, _, value = line.strip().partition("=")
            if key:
                values[key] = value
    return values


def post(url: str, body: dict, headers: dict, timeout: float) -> tuple[int, object]:
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, json.loads(response.read() or b"{}")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode(errors="replace")[:200]
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return 0, f"no answer ({type(exc).__name__})"


def llm_status() -> str:
    base = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
    try:
        with urllib.request.urlopen(f"{base}/api/tags", timeout=3) as response:
            models = [model.get("name", "") for model in json.loads(response.read()).get("models", [])]
        return f"reachable at {base}; models: {', '.join(models) or 'none installed'}"
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return f"NOT reachable at {base}; answers that need the language model will fail"


WRONG_LANGUAGE = re.compile(r"[\u0900-\u097F]|\b(aapko|aapka|aapki|kijiye|karni|karna|chahiye|kripya)\b", re.IGNORECASE)
DOCTOR_NAME = re.compile(r"\bDr\.? [A-Z][a-z]+(?: [A-Z][a-z]+)*(?: \d+)?")


def hospital_doctor_names(base: str, slug: str) -> set[str]:
    try:
        with urllib.request.urlopen(f"{base}/api/v1/hospital-public/{slug}/doctors", timeout=15) as response:
            data = json.loads(response.read())
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return set()
    doctors = data if isinstance(data, list) else (data.get("doctors") or data.get("items") or [])
    return {str(doctor.get("full_name") or doctor.get("name") or "").strip() for doctor in doctors if isinstance(doctor, dict)}


def verdict(status: int, reply: str, names: set[str] | None = None) -> str:
    if status != 200:
        return f"HTTP {status}"
    if WRONG_LANGUAGE.search(reply):
        return "LANGUAGE"
    if names:
        listed = {match.group(0).strip() for match in DOCTOR_NAME.finditer(reply)}
        if any(name not in names for name in listed):
            return "OTHER-HOSP"
    if reply.strip() == "":
        return "EMPTY"
    lowered = reply.lower()
    if "could not complete" in lowered or "couldn’t answer" in lowered or "couldn't answer" in lowered:
        return "FAILED"
    if "999" in reply or "৯৯৯" in reply:
        return "SAFETY"
    return "OK"


def main() -> int:
    base, slug, env_file = sys.argv[1].rstrip("/"), sys.argv[2], sys.argv[3]
    env = read_env(env_file)
    print(f"language model server: {llm_status()}")
    status, data = post(
        f"{base}/api/v1/auth/login",
        {"email": env.get("E2E_PATIENT_EMAIL", ""), "password": env.get("E2E_PATIENT_PASSWORD", "")},
        {},
        20,
    )
    token = data.get("access_token") if isinstance(data, dict) else None
    if status != 200 or token is None:
        print(f"could not sign in as the e2e patient (HTTP {status})")
        return 1
    headers = {"Authorization": f"Bearer {token}", "X-MediBook-Hospital-Slug": slug}
    names = hospital_doctor_names(base, slug)
    print(f"doctors at {slug}: {len(names)}")
    messages = list(MESSAGES)
    if names:
        messages.append(sorted(names)[0])
    counts: dict[str, int] = {}
    for message in messages:
        started = time.monotonic()
        status, data = post(f"{base}/api/v1/chat", {"message": message}, headers, 45)
        took = time.monotonic() - started
        reply = data.get("response", "") if isinstance(data, dict) else str(data)
        result = verdict(status, str(reply), names)
        counts[result] = counts.get(result, 0) + 1
        one_line = " ".join(str(reply).split())
        slow = " SLOW" if took > 10 else ""
        print(f"{result:<10}{slow:<5} {took:5.1f}s  {message[:44]:<44} -> {one_line[:160]}")
    print("summary: " + ", ".join(f"{key} {value}" for key, value in sorted(counts.items())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
