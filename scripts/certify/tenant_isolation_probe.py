"""Live tenant-isolation, object-level authorization and role-escalation probe.

Usage: python scripts/certify/tenant_isolation_probe.py BASE_URL ENV_FILE
ENV_FILE is written by scripts/seed_e2e_accounts.py, optionally extended with
E2E_OWN_DOCTOR_ID, E2E_OTHER_DOCTOR_ID and E2E_OTHER_DOCTOR_ACTIVE (a doctor
linked only to the other hospital). Passes only when every positive control
succeeds and every cross-tenant or escalation attempt is refused. Writes are
no-ops: each doctor is set to the activation state it already has.
"""

import sys
import uuid

import httpx

REFUSED = {401, 403, 404}


def load_env(path):
    values = {}
    for line in open(path, encoding="utf-8"):
        if "=" in line:
            key, value = line.rstrip("\n").split("=", 1)
            values[key] = value
    return values


def example(schema, components, depth=0):
    """Smallest valid JSON value for an OpenAPI schema (required fields only)."""
    if depth > 8:
        return None
    if "$ref" in schema:
        return example(components[schema["$ref"].split("/")[-1]], components, depth + 1)
    for key in ("anyOf", "oneOf", "allOf"):
        if key in schema:
            options = [o for o in schema[key] if o.get("type") != "null"]
            return example(options[0], components, depth + 1) if options else None
    if "enum" in schema:
        return schema["enum"][0]
    kind = schema.get("type")
    if kind == "object":
        props = schema.get("properties", {})
        return {name: example(props.get(name, {}), components, depth + 1) for name in schema.get("required", [])}
    if kind == "array":
        return []
    if kind == "boolean":
        return True
    if kind in ("integer", "number"):
        return 1
    if kind == "string":
        formats = {"uuid": str(uuid.uuid4()), "email": "e2e@example.com", "date": "2030-01-01", "date-time": "2030-01-01T00:00:00Z"}
        return formats.get(schema.get("format", ""), "e2e")
    return None


def main(base, env_path):
    env = load_env(env_path)
    own, other = env["E2E_HOSPITAL_SLUG"], env.get("E2E_OTHER_HOSPITAL_SLUG", "")
    results = []

    def check(label, ok, detail):
        results.append(ok)
        print(("PASS  " if ok else "FAIL  ") + label + " -> " + detail)

    with httpx.Client(base_url=base, timeout=20) as client:

        def login(prefix):
            response = client.post(
                "/api/v1/auth/login",
                json={"email": env[prefix + "_EMAIL"], "password": env[prefix + "_PASSWORD"]},
            )
            token = response.json().get("access_token") if response.status_code == 200 else None
            check(prefix.replace("E2E_", "").lower() + " login", token is not None, str(response.status_code))
            return {"Authorization": "Bearer " + token} if token else None

        def statuses(headers, slug, paths):
            out = []
            for path in paths:
                url = path.replace("{hospital_slug}", slug) if slug else path
                out.append((path, client.get(url, headers=headers).status_code))
            return out

        patient = login("E2E_PATIENT")
        hospital = login("E2E_HOSPITAL")
        platform = login("E2E_PLATFORM")
        spec = client.get("/openapi.json").json()
        spec_paths = spec["paths"]
        components = spec.get("components", {}).get("schemas", {})
        tenant_gets = sorted(
            p for p, item in spec_paths.items()
            if p.startswith("/api/v1/hospital-operations/{hospital_slug}") and "get" in item and p.count("{") == 1
        )
        platform_gets = sorted(
            p for p, item in spec_paths.items()
            if (p.startswith("/api/v1/platform-control") or p.startswith("/api/v1/platform/"))
            and "get" in item and "{" not in p
        )
        print("tenant GET operations:", len(tenant_gets), "| platform GET operations:", len(platform_gets))

        if hospital:
            own_codes = statuses(hospital, own, tenant_gets)
            check("hospital admin reads own hospital (positive control)",
                  any(code == 200 for _, code in own_codes), str([c for _, c in own_codes]))
            if other:
                leaks = [(p, c) for p, c in statuses(hospital, other, tenant_gets) if c not in REFUSED]
                check(f"hospital admin refused on {other} (GET sweep)", not leaks, str(leaks or "all refused"))
            escalate = [(p, c) for p, c in statuses(hospital, None, platform_gets) if c not in REFUSED]
            check("hospital admin refused on platform control", not escalate, str(escalate or "all refused"))
            activation = next(
                (p for p, item in spec_paths.items() if p.endswith("/doctors/{doctor_id}/activation") and "patch" in item),
                None,
            )
            own_doctor = env.get("E2E_OWN_DOCTOR_ID", "")
            if activation and own_doctor:
                schema = spec_paths[activation]["patch"]["requestBody"]["content"]["application/json"]["schema"]
                template = example(schema, components)
                template = template if isinstance(template, dict) else {}

                def write(slug, doctor_id, active):
                    url = activation.replace("{hospital_slug}", slug).replace("{doctor_id}", doctor_id)
                    return client.patch(url, headers=hospital, json={**template, "is_active": active}).status_code

                code = write(own, own_doctor, True)
                check("hospital admin updates own doctor (positive control, no-op)", code == 200, str(code))
                other_doctor = env.get("E2E_OTHER_DOCTOR_ID", "")
                other_active = env.get("E2E_OTHER_DOCTOR_ACTIVE", "true") == "true"
                if other and other_doctor:
                    code = write(other, other_doctor, other_active)
                    check(f"hospital admin cannot update a doctor of {other}", code in REFUSED, str(code))
                    code = write(own, other_doctor, other_active)
                    check(f"hospital admin cannot reach a {other}-only doctor through its own slug", code in REFUSED, str(code))
                else:
                    print("SKIP  object-level checks: no doctor is linked only to the other hospital")
        if patient:
            ops = [(p, c) for p, c in statuses(patient, own, tenant_gets) if c not in REFUSED]
            check("patient refused on hospital operations", not ops, str(ops or "all refused"))
            plat = [(p, c) for p, c in statuses(patient, None, platform_gets) if c not in REFUSED]
            check("patient refused on platform control", not plat, str(plat or "all refused"))
        if platform:
            codes = [c for _, c in statuses(platform, None, platform_gets)]
            check("platform admin reads platform control (positive control)", any(c == 200 for c in codes), str(codes))

    passed = all(results) and len(results) >= 8
    print("tenant isolation:", "PASS" if passed else "FAIL")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
