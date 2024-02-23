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
sudo apt-get upgrade -yq
sudo apt-get autoremove -yq

# ensure python environment and git
echo "####################################################################"
echo "## Upgrade/Install Python                                         ##"
echo "####################################################################"
sudo apt-get install -yq git python3-venv python3-dev
# tool to detect i2c ports (i2cdetect -y 1)
echo "####################################################################"
echo "## Upgrade/Install i2c-tools                                      ##"
echo "####################################################################"
sudo apt-get install -yq i2c-tools

# install libraries and tools
# install libs for OpenCV
echo "####################################################################"
echo "## Upgrade/Install opencv libs                                    ##"
echo "####################################################################"

#opencv opencv-python-headless==4.6.0.66
sudo apt-get install -yq ocl-icd-libopencl1 libchromaprint1 libmp3lame0 libx264-160 libva-drm2 libaom0 libharfbuzz0b \
  libx265-192 libcodec2-0.9 libvorbis0a libpangoft2-1.0-0 libspeex1 libssh-gcrypt-4 libva2 libgraphite2-3 \
  libogg0 libswresample3 libsoxr0 libxcb-render0 librsvg2-2 libavcodec58 libavformat58 libvorbisenc2 libsodium23 \
  libdrm2 libsrt1.4-gnutls libpixman-1-0 libdatrie1 libwebpmux3 libthai0 libmpg123-0 libswscale5 libshine3 libzmq5 \
  libwavpack1 libpangocairo-1.0-0 libopenmpt0 libtheora0 libcairo2 libxrender1 libpango-1.0-0 libvorbisfile3 \
  libsnappy1v5 libgfortran5 libxcb-shm0 libcairo-gobject2 libxfixes3 libavutil56 libgsm1 libzvbi0 libbluray2 \
  libatlas3-base libopus0 libopenjp2-7 libudfread0 libvdpau1 libvpx6 libpgm-5.3-0 libdav1d4 libgdk-pixbuf-2.0-0 \
  libnorm1 libgme0 librabbitmq4 libva-x11-2 libtwolame0 libxvidcore4 --fix-missing

# numpy numpy==1.26.2
sudo apt-get install -yq libopenblas0-pthread libgfortran5 --fix-missing
# pillow Pillow==10.1.0
sudo apt-get install -yq libwebpdemux2 libwebpmux3 liblcms2-2 libopenjp2-7 --fix-missing

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
    python3 -m venv .venv --prompt cv
fi

# update pip
echo "####################################################################"
echo "## Upgrade pip libraries                                          ##"
echo "####################################################################"
source "$ROOT_PATH/python/.venv/bin/activate"
pip freeze | grep -v -f requirements.txt - | grep -v '^#' | xargs pip uninstall -y
pip install -U pip setuptools wheel
pip install -U --upgrade-strategy eager -r requirements.txt --only-binary=:all:

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

# End ScrabScrap
pkill -SIGALRM python 2> /dev/null
echo "####################################################################"
echo "## reboot                                                         ##"
echo "####################################################################"
sudo reboot
