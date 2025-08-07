#!/bin/bash

source .venv/bin/activate

while getopts c:h flag
do
    case "${flag}" in
        h)
          echo "usage qa.sh"
          echo "always run ruff, mypy, pylint"
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

  echo "*** run ruff"
  ruff check src/*.py src/admin/*.py src/hardware/*.py src/game_board/*.py simulator/*.py
  retVal=$?
  if [ $retVal -ne 0 ]; then
    echo "### ruff returns $retVal"
  fi

  echo "*** run mypy"
  mypy src/*.py src/admin/*.py src/hardware/*.py src/game_board/*.py simulator/*.py
  retVal=$?
  if [ $retVal -ne 0 ]; then
    echo "### mypy returns $retVal"
  fi
  
  echo "*** run pylint"
  pylint src/*.py src/admin/*.py src/hardware/*.py src/game_board/*.py simulator/*.py
  retVal=$?
  if [ $retVal -ne 0 ]; then
    echo "### pylint returns $retVal"
  fi

