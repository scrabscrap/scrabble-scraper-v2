#!/usr/bin/env bash 

# param $1= branch
SCRIPTPATH=$(dirname "$0")

if [ "$1" == "" ] 
then
    BRANCH=main
else
    BRANCH=$1
fi

git fetch --tags --prune --all -f
git stash
git checkout $BRANCH -f
git pull --autostash

"$SCRIPTPATH/upgrade-system.sh"
