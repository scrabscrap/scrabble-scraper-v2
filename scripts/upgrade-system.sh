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
echo "## Upgrade Python                                                 ##"
echo "####################################################################"
sudo apt-get install -yq git python3-venv python3-dev
# tool to detect i2c ports (i2cdetect -y 1)
echo "####################################################################"
echo "## Upgrade i2c-tools                                              ##"
echo "####################################################################"
sudo apt-get install -yq i2c-tools

# install libraries and tools
# install libs for OpenCV
echo "####################################################################"
echo "## Upgrade opencv libs                                            ##"
echo "####################################################################"
sudo apt-get install -yq libgsm1 libatk1.0-0 libavcodec58 libcairo2 libvpx6 libvorbisenc2 \
libwayland-egl1 libva-drm2 libwavpack1 libshine3 libdav1d4 libwayland-client0 libxcursor1 \
libopus0 libchromaprint1 libxinerama1 libpixman-1-0 libzmq5 libmp3lame0 libxcb-shm0 libsz2 \
libgtk-3-0 libharfbuzz0b libilmbase25 libvdpau1 libssh-gcrypt-4 libpangocairo-1.0-0 \
libtwolame0 libnorm1 libxi6 libxfixes3 libxcomposite1 libxcb-render0 libwayland-cursor0 \
libvorbisfile3 libspeex1 libxrandr2 libxkbcommon0 libtheora0 libaec0 libx264-160 libaom0 \
libzvbi0 libopenexr25 libogg0 libpangoft2-1.0-0 librsvg2-2 libxvidcore4 libsrt1.4-gnutls \
libbluray2 libvorbis0a libdrm2 libmpg123-0 libatlas3-base libxdamage1 libavformat58 \
libatk-bridge2.0-0 libswscale5 libsnappy1v5 libcodec2-0.9 libsodium23 libudfread0 \
libswresample3 libcairo-gobject2 libx265-192 libthai0 libva-x11-2 ocl-icd-libopencl1 \
libepoxy0 libpango-1.0-0 libavutil56 libva2 librabbitmq4 libgme0 libatspi2.0-0 \
libgraphite2-3 libhdf5-103-1 libgfortran5 libsoxr0 libpgm-5.3-0 libopenmpt0 libxrender1 \
libdatrie1 libgdk-pixbuf-2.0-0 libopenjp2-7 libwebpmux3 --fix-missing

# create an OpenCV Python environment
echo "####################################################################"
echo "## Create venv                                                    ##"
echo "####################################################################"
cd "$ROOT_PATH/python"
if [ -d .venv ] ; then
    echo ".venv already configured"
else
    python3 -m venv .venv --prompt cv
fi

# update pip
echo "####################################################################"
echo "## Upgrade pip libraries                                          ##"
echo "####################################################################"
source "$ROOT_PATH/python/.venv/bin/activate"
pip install -U pip setuptools wheel
pip install -r requirements.txt --only-binary=:all:

# install nodejs npm
echo "####################################################################"
echo "## Upgrade nodejs npm                                             ##"
echo "####################################################################"

if [[ $(/usr/bin/node -v) == *"v19"* ]]; then
    echo "node 19 is installed, skipping..."
else
    sudo apt-get remove -yq nodejs
    sudo rm -rf /usr/local/bin/node*
    sudo rm -rf /usr/local/bin/npm*
    sudo rm -rf /etc/apt/sources.list.d/nodesource.list
    curl -sL https://deb.nodesource.com/setup_19.x | sudo bash -
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

echo "*** reboot ***"
sudo reboot