#!/bin/sh
# Render deck/index.html to ../wasel-pitch.pdf and per-slide PNGs (scratch dir passed as $1, optional).
cd "$(dirname "$0")" || exit 1
google-chrome --headless=new --no-sandbox --disable-gpu --no-pdf-header-footer --virtual-time-budget=4000 \
  --print-to-pdf=../wasel-pitch.pdf index.html 2>&1 | grep -i written
