#!/usr/bin/env bash
# Fails on anything that must never be committed or that breaks determinism.
set -uo pipefail
fail=0; say(){ printf 'hygiene: %b\n' "$*" >&2; fail=1; }

bad=$(git ls-files . | grep -E '(^|/)\.env$|(^|/)\.dev\.vars$|\.db$|\.db-(wal|shm)$|\.sqlite3?$|(^|/)node_modules/|(^|/)web/dist/|(^|/)var/' || true)
[ -n "$bad" ] && say "tracked files that must be ignored:\n$bad"

# key-shaped strings: known prefixes (Groq, Gemini, Meta, tunnel token, GitHub, AWS, Slack, Stripe, private keys)
here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
git grep -nIE '(gsk_[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{30,}|EAA[A-Za-z0-9]{50,}|eyJhIjoi[A-Za-z0-9+/=_-]{40,}|ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----|xox[abprs]-[A-Za-z0-9-]{10,}|(sk|rk)_(live|test)_[A-Za-z0-9]{16,})' -- . ':!scripts/dev/hygiene.sh' ':!scripts/dev/hygiene.allow' \
  && say "key-shaped string in a tracked file"

# assignment shapes: a SECRET/TOKEN/KEY/PASSWORD name given a long value. .env.example and test fixtures are exempt;
# known placeholders are listed (one extended regex per line) in scripts/dev/hygiene.allow
assigned=$(git grep -nIE '(SECRET|TOKEN|KEY|PASSWORD)[A-Z_]*[[:space:]]*[=:][[:space:]]*["'"'"']?[A-Za-z0-9+/_-]{24,}' \
  -- . ':!.env.example' ':!tests/fixtures' ':!scripts/dev/hygiene.sh' ':!scripts/dev/hygiene.allow' || true)
[ -f "$here/hygiene.allow" ] && assigned=$(printf '%s\n' "$assigned" | grep -vEf "$here/hygiene.allow" || true)
[ -n "$assigned" ] && say "secret-shaped assignment in a tracked file (add a placeholder to scripts/dev/hygiene.allow):\n$assigned"

# phone numbers in fixtures/data must be allowlisted 21600000001..21600000009
phones=$(git grep -nIoE '\b216[0-9]{8}\b' -- tests/fixtures data 2>/dev/null | grep -vE ':2160000000[1-9]$' || true)
[ -n "$phones" ] && say "non-allowlisted phone numbers:\n$phones"

# one clock
git grep -nE 'datetime\.(now|utcnow|today)\(' -- 'src/*.py' ':!src/wasel/clock.py' \
  && say "read time through wasel.clock.Clock, not datetime.now()"

# the generator never calls an LLM; no provider SDKs anywhere (httpx backend only)
git grep -nE '^\s*(import|from)\s+(groq|google\.genai|google\.generativeai|openai)\b' -- 'src/*.py' 'scripts/*.py' \
  && say "no LLM SDK imports (the backend is plain httpx in src/wasel/llm/groq_backend.py)"

# no raw HTML injection in the dashboard
git grep -n 'dangerouslySetInnerHTML' -- 'web/app/*' 'web/components/*' 2>/dev/null && say "dangerouslySetInnerHTML is banned (#17)"

exit $fail
