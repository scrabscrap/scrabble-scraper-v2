#!/usr/bin/env bash 

# param $1= operation (install, up, down, reauth, unnstall)
SCRIPTPATH=$(dirname "$0")

if [ "$1" == "" ] 
then
    echo 'invalid call'
    exit 1
fi
export DEBIAN_FRONTEND=noninteractive
echo "####################################################################"
echo "## script tailscale                                               ##"
echo "####################################################################"

case $1 in
    INSTALL)    sudo curl -fsSL https://tailscale.com/install.sh | sh ;;
    UP)         echo  "starting tailscale" && sudo tailscale up 2>&1 ;;
    DOWN)       echo  "stopping tailscale" && sudo tailscale down  2>&1 ;;
    REAUTH)     echo  "reauth tailscale" && sudo tailscale up --force-reauth 2>&1 ;;
    UNINSTALL)  echo  "uninstall tailscale" && sudo tailscale down && sudo apt-get -y remove tailscale ;;
    STATUS)     ;;
    *)          echo  "invalid parameter $1"
esac

if test -f /usr/bin/tailscale; then
    tailscale status --peers=false
else
    echo "tailscale not installed"
fi
