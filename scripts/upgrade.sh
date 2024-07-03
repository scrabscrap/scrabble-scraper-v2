#!/usr/bin/env bash 

# param $1= branch
SCRIPTPATH=$(dirname "$0")

if [ "$1" == "" ] 
then
    BRANCH=main
else
    BRANCH=$1
fi

echo "####################################################################"
echo "## Upgrade ScrabScrap                                             ##"
echo "####################################################################"
git fetch --tags --prune --all -f

if git merge-base --is-ancestor origin/$BRANCH HEAD; then
    echo "no git changes detected, , skipping git pull ..."
    git stash
    git checkout $BRANCH -f
    echo "####################################################################"
    echo "## Upgrade Linux                                                  ##"
    echo "####################################################################"
    sudo apt-get update -yq
    sudo apt-get upgrade --with-new-pkgs -yq
    sudo apt-get autoremove -yq

    if command -v tailscale &> /dev/null; then
       sudo tailscale update --yes
    fi

    echo "####################################################################"
    echo "## reboot                                                         ##"
    echo "####################################################################"
    # End ScrabScrap
    pkill -SIGALRM python 2> /dev/null
    sleep 2
    pkill -9 python 2> /dev/null
    sudo reboot
else
    git stash
    git checkout $BRANCH -f
    git pull --autostash

    if command -v tailscale &> /dev/null; then
       sudo tailscale update --yes
    fi

    "$SCRIPTPATH/upgrade-system.sh"
fi
