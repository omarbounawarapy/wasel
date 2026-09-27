#!/usr/bin/env bash
# Fails on anything that must never be committed or that breaks determinism (05 §5).
set -uo pipefail
fail=0; say(){ printf 'hygiene: %b\n' "$*" >&2; fail=1; }

bad=$(git ls-files . | grep -E '(^|/)\.env$|\.db$|\.db-(wal|shm)$|\.sqlite3?$|(^|/)node_modules/|(^|/)web/dist/|(^|/)var/' || true)
[ -n "$bad" ] && say "tracked files that must be ignored:\n$bad"

# key-shaped strings [VERIFY Groq/Gemini/Meta prefixes]
git grep -nIE '(gsk_[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{30,}|EAA[A-Za-z0-9]{50,}|eyJhIjoi[A-Za-z0-9+/=_-]{40,})' -- . ':!scripts/hygiene.sh' \
  && say "key-shaped string in a tracked file"

# phone numbers in fixtures/data/mocks must be allowlisted 21600000001..21600000009
phones=$(git grep -nIoE '\b216[0-9]{8}\b' -- tests/fixtures data mocks 2>/dev/null | grep -vE ':2160000000[1-9]$' || true)
[ -n "$phones" ] && say "non-allowlisted phone numbers:\n$phones"

# one clock
git grep -nE 'datetime\.(now|utcnow|today)\(' -- 'app/*.py' 'ml/*.py' ':!app/clock.py' \
  && say "read time through app.clock.Clock, not datetime.now()"

# the generator never calls an LLM; no provider SDKs anywhere (httpx backend only)
git grep -nE '^\s*(import|from)\s+(groq|google\.genai|google\.generativeai|openai)\b' -- 'app/*.py' 'ml/*.py' 'scripts/*.py' \
  && say "no LLM SDK imports (the backend is plain httpx in app/llm/groq_backend.py)"

# no raw HTML injection in the dashboard
git grep -n 'dangerouslySetInnerHTML' -- 'web/src/*' 2>/dev/null && say "dangerouslySetInnerHTML is banned (#17)"

exit $fail
