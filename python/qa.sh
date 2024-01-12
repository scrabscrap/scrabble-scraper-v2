#!/bin/bash

source .venv/bin/activate

while getopts c:h flag
do
    case "${flag}" in
        h)
          echo "usage qa.sh"
          echo "always run flake8, mypy, pylint"
          echo "-h help"
          echo "-c run coverage"
          exit 0
          ;;
        c) 
          echo "*** run coverage"
          coverage run -m unittest discover  &> /dev/null
          coverage report
          ;;
    esac
done

  echo "*** run flake8"
  flake8 src/*.py src/hardware/*.py src/game_board/*.py simulator/*.py --max-line-length=128 --ignore=E402 --exclude="ignore/*" --count --show-source --statistics
  retVal=$?
  if [ $retVal -ne 0 ]; then
    echo "### flake8 returns $retVal"
  fi

  echo "*** run mypy"
  mypy --follow-imports skip --config-file mypy.ini src/*.py src/hardware/*.py src/game_board/*.py simulator/*.py
  retVal=$?
  if [ $retVal -ne 0 ]; then
    echo "### mypy returns $retVal"
  fi
  
  echo "*** run pylint"
  pylint src/*.py src/hardware/*.py src/game_board/*.py simulator/*.py
  retVal=$?
  if [ $retVal -ne 0 ]; then
    echo "### pylint returns $retVal"
  fi

