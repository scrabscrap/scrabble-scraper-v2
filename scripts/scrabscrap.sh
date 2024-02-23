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
    python -m venv .venv --prompt cv
    source .venv/bin/activate
    pip install -U pip setuptools wheel
    pip install --force-reinstall -r requirements.txt --only-binary=:all:
fi
source $PYTHONDIR/.venv/bin/activate
if [ -d "/home/pi/.venv" ]; then
    # cleanup
    rm -rf  "/home/pi/.venv"
fi

cd "$PYTHONDIR"
python -m scrabscrap >> "$WORKDIR/log/game.log"
