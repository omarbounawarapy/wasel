#!/usr/bin/env bash
# Fails on anything that must never be committed or that breaks determinism.
set -uo pipefail
fail=0; say(){ printf 'hygiene: %b\n' "$*" >&2; fail=1; }

bad=$(git ls-files . | grep -E '(^|/)\.env$|\.db$|\.db-(wal|shm)$|\.sqlite3?$|(^|/)node_modules/|(^|/)web/dist/|(^|/)var/' || true)
[ -n "$bad" ] && say "tracked files that must be ignored:\n$bad"

# key-shaped strings (Groq, Gemini, Meta and tunnel-token prefixes)
git grep -nIE '(gsk_[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{30,}|EAA[A-Za-z0-9]{50,}|eyJhIjoi[A-Za-z0-9+/=_-]{40,})' -- . ':!scripts/dev/hygiene.sh' \
  && say "key-shaped string in a tracked file"

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
