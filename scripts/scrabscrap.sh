#!/bin/bash

# damit das Script beim Booten des Rechners ausgeführt wird, muss folgender Eintrag
# als User "pi" vorgenommen werden:
# crontab -e
# @reboot /home/pi/scrabble-scraper-v2/script/scrabscrap.sh &

export DISPLAY=:0

# working directory is $PYTHONDIR/work
SCRIPTPATH=$(dirname "$0")
PYTHONDIR="$(cd "$SCRIPTPATH/../python" && pwd)"
WORKDIR=$PYTHONDIR/work

if [ $(uname -m) != 'aarch64' ]; then
  echo 'armv7l no longer supported'
  exit 1
fi

# create directories
mkdir -p "$WORKDIR/log"
mkdir -p "$WORKDIR/web"
mkdir -p "$WORKDIR/recording"

# copy defaults if not exists
cp -n "$PYTHONDIR/defaults/scrabble.ini" "$WORKDIR/scrabble.ini"
cp -n "$PYTHONDIR/defaults/upload-secret.ini" "$WORKDIR/upload-secret.ini"
cp -n "$PYTHONDIR/defaults/log.conf" "$WORKDIR/log.conf"

# start app
export PYTHONPATH=src:
if [ ! -d "$PYTHONDIR/.venv" ]; then
    cd "$PYTHONDIR"
    python3 -m venv .venv  --system-site-packages --prompt cv
    source .venv/bin/activate
    pip install -U pip setuptools wheel
    pip install -U -r requirements.txt
fi
source $PYTHONDIR/.venv/bin/activate
if [ -d "/home/pi/.venv" ]; then
    # cleanup
    rm -rf  "/home/pi/.venv"
fi

cd "$PYTHONDIR"

while : ; do
    python -m scrabscrap >> "$WORKDIR/log/game.log"
    if [ $? -eq 4 ]; then
        echo "restart scrabscrap"
    else
        break
    fi
done
