#!/bin/bash

source .venv/bin/activate

while getopts ch flag
do
    case $flag in
        h)
          echo "usage qa.sh"
          echo "always run ruff, pyright, unittest"
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

  echo "*** run unittest"
  python -m unittest test/test_a*.py test/test_bo*.py test/test_c*.py test/test_m*.py test/test_s*.py -f &> /dev/null
  retVal=$?
  if [ $retVal -ne 0 ]; then
    echo "### unittest returns $retVal"
  fi

  echo "*** run ruff"
  ruff check src/*.py src/admin/*.py src/game_board/*.py src/hardware/*.py src/utils/*.py simulator/*.py
  retVal=$?
  if [ $retVal -ne 0 ]; then
    echo "### ruff returns $retVal"
  fi

  echo "*** run pyright"
  pyright src/ src/admin/ src/game_board/ src/hardware/ src/utils/ simulator/ --threads 6
  retVal=$?
  if [ $retVal -ne 0 ]; then
    echo "### pyright returns $retVal"
    exit $retVal
  fi

