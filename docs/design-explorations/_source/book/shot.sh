#!/bin/sh
# usage: shot.sh <direction-id> <only> <out.png> <width> <height>   e.g. shot.sh 04-review-queue d1 /tmp/d1.png 1280 800
google-chrome --headless=new --disable-gpu --no-sandbox --hide-scrollbars --force-device-scale-factor=1 --virtual-time-budget=4000 \
  --window-size=$4,$5 --screenshot="$3" "file://$(pwd)/docs/design-explorations/book/$1.html?only=$2" >/dev/null 2>&1
