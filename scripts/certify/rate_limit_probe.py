"""Login rate-limit probe. Run against a backend started with
MEDIBOOK_RATE_LIMIT_ENABLED=true and MEDIBOOK_RATE_LIMIT_AUTH_PER_MINUTE=<limit>.

Usage: python scripts/certify/rate_limit_probe.py BASE_URL [LIMIT]
"""

import sys
import uuid

import httpx


def main(base: str, limit: int) -> int:
    email = "ratelimit-" + uuid.uuid4().hex[:8] + "@example.com"
    codes = []
    retry_after = None
    with httpx.Client(base_url=base, timeout=15) as client:
        for _ in range(limit + 4):
            response = client.post("/api/v1/auth/login", json={"email": email, "password": "wrong-password-123"})
            codes.append(response.status_code)
            if response.status_code == 429 and retry_after is None:
                retry_after = response.headers.get("retry-after")
    ok = 429 in codes and codes.index(429) <= limit + 1 and retry_after is not None
    print(f"{len(codes)} failed logins (limit {limit}) ->", codes, "| Retry-After:", retry_after)
    print("rate limit:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 5))
