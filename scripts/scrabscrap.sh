#!/bin/bash

# damit das Script beim Booten des Rechners ausgeführt wird, muss folgender Eintrag
# als User "pi" vorgenommen werden:
# crontab -e
# @reboot /home/pi/scrabble-scraper-v2/script/scrabscrap.sh &

export DISPLAY=:0

# working directory is $PROJECT/work
SCRIPTPATH=$(dirname "$0")
PROJECT="$(cd "$SCRIPTPATH/.." && pwd)"
WORKDIR=$PROJECT/work

# create directories
mkdir -p "$WORKDIR/log"
mkdir -p "$WORKDIR/web"

# copy defaults if not exists
cp -n "$PROJECT/python/defaults/scrabble.ini" "$WORKDIR/scrabble.ini"
cp -n "$PROJECT/python/defaults/ftp-secret.ini" "$WORKDIR/ftp-secret.ini"
cp -n "$PROJECT/python/defaults/log.conf" "$WORKDIR/log.conf"

# start app
export PYTHONPATH=$PROJECT/python/src
source ~/.venv/cv/bin/activate

cd "$WORKDIR"
python -m scrabscrap >> "$WORKDIR/log/game.log"
