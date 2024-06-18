#!/usr/bin/env bash 

SCRIPTPATH=$(dirname "$0")

cd "$SCRIPTPATH/.."

ROOT_PATH=$(pwd)
echo "### ROOT-Folder: $ROOT_PATH"

# update os
echo "####################################################################"
echo "## Upgrade Linux                                                  ##"
echo "####################################################################"
sudo apt-get update -yq
sudo apt-get upgrade --with-new-pkgs -yq
sudo apt-get autoremove -yq

# ensure python environment and git
echo "####################################################################"
echo "## Upgrade/Install Python and tools                               ##"
echo "####################################################################"
sudo apt-get install -yq git python3-venv python3-dev i2c-tools


if [ $(uname -m) == 'aarch64' ]; then
    echo "####################################################################"
    echo "## Upgrade/Install picamera2                                      ##"
    echo "####################################################################"
    sudo apt-get install -yq python3-picamera2 --no-install-recommends
else
    echo 'armv7l no longer supported'
    exit 1
fi

# cleanup
sudo apt -yq autoremove

# create an OpenCV Python environment
echo "####################################################################"
echo "## Create venv                                                    ##"
echo "####################################################################"
cd "$ROOT_PATH/python"
if [ -d .venv ] ; then
    echo ".venv already configured, skipping..."
else
    python3 -m venv .venv  --system-site-packages --prompt cv
fi

# update pip
echo "####################################################################"
echo "## Upgrade pip libraries                                          ##"
echo "####################################################################"
source "$ROOT_PATH/python/.venv/bin/activate"
../scripts/pip-req-check.py
pip install -U pip setuptools wheel -r requirements.txt

# install nodejs npm
echo "####################################################################"
echo "## Upgrade nodejs npm                                             ##"
echo "####################################################################"

if [[ $(/usr/bin/node -v) == *"v21"* ]]; then
    echo "node 21 is installed, skipping..."
else
    sudo apt-get -yq purge nodejs
    sudo rm -r /etc/apt/sources.list.d/nodesource.list
    sudo rm -r /etc/apt/keyrings/nodesource.gpg    
    sudo rm -rf /usr/local/bin/node*
    sudo rm -rf /usr/local/bin/npm*

    sudo apt-get install -y ca-certificates curl gnupg
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | sudo gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg
    NODE_MAJOR=21
    echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_$NODE_MAJOR.x nodistro main" | sudo tee /etc/apt/sources.list.d/nodesource.list
    sudo apt-get update
    sudo apt-get install -yq nodejs
fi

# install node requirements
echo "####################################################################"
echo "## create web-app                                                 ##"
echo "####################################################################"
cd "$ROOT_PATH/react"
npm install
npm run build

# reinstall web-app
echo "####################################################################"
echo "## install web-app to python folder                               ##"
echo "####################################################################"
if [ -d "$ROOT_PATH/python/src/static/webapp" ]; then
    rm -rf "$ROOT_PATH/python/src/static/webapp"
fi
mkdir "$ROOT_PATH/python/src/static/webapp"
cp -r "$ROOT_PATH/react/build/." "$ROOT_PATH/python/src/static/webapp/"
ln -s "$ROOT_PATH/python/work/web" "$ROOT_PATH/python/src/static/webapp/web"

echo "####################################################################"
echo "## reboot                                                         ##"
echo "####################################################################"
# End ScrabScrap
pkill -SIGALRM python 2> /dev/null
sleep 2
pkill -9 python 2> /dev/null
sudo reboot
