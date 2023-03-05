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

if git merge-base --is-ancestor origin/$BRANCH HEAD; then
    echo "no git changes detected, , skipping git pull ..."
    echo "####################################################################"
    echo "## check for Linux Updates                                        ##"
    echo "####################################################################"
    sudo apt-get update -yq
    sudo apt-get upgrade -yq
    sudo apt-get autoremove -yq
else
    git stash
    git checkout $BRANCH -f
    git pull --autostash
    "$SCRIPTPATH/upgrade-system.sh"
fi
