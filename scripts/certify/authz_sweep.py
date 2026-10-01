"""Anonymous authorization sweep: call every API operation without credentials.

Usage: python scripts/certify/authz_sweep.py BASE_URL
Fails if a tenant, platform or account operation answers without login, or if
any operation returns a server error for junk input.
"""

import re
import sys
import uuid

import httpx

SKIP = re.compile(r"^/api/v1/(llm|chat)|/stream")
PROTECTED = re.compile(
    r"hospital-operations|platform-control|^/api/v1/platform/|/auth/me$|hospital-workspaces"
    r"|^/api/v1/hospital/|^/api/v1/appointments|^/api/v1/conversations|system-health|^/api/v1/identity/me"
)


def main(base: str) -> int:
    spec = httpx.get(base + "/openapi.json", timeout=15).json()
    rows = []
    with httpx.Client(base_url=base, timeout=20) as client:
        for path, item in sorted(spec.get("paths", {}).items()):
            for method in ("get", "post", "put", "patch", "delete"):
                if method not in item or SKIP.search(path):
                    continue
                url = re.sub(
                    r"\{([^}]+)\}",
                    lambda m: "medibook-demo" if m.group(1) == "hospital_slug" else str(uuid.uuid4()),
                    path,
                )
                response = client.request(method.upper(), url, json=None if method == "get" else {})
                rows.append((method.upper(), path, response.status_code))
    counts = {}
    for _, _, status in rows:
        counts[status] = counts.get(status, 0) + 1
    print("anonymous requests by status:", dict(sorted(counts.items())))
    open_protected = [r for r in rows if r[2] < 400 and PROTECTED.search(r[1])]
    server_errors = [r for r in rows if r[2] >= 500]
    for method, path, status in open_protected:
        print("  OPEN WITHOUT LOGIN:", status, method, path)
    for method, path, status in server_errors:
        print("  SERVER ERROR:", status, method, path)
    ok = not open_protected and not server_errors
    print("anonymous sweep:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
