#!/usr/bin/env bash 

echo "## pre setup steps ##"
echo "sudo apt install -y git"
echo "cd ~"
echo "git clone https://github.com/scrabscrap/scrabble-scraper-v2.git"
echo "## end pre setup steps ##"
read -p "Press any key to continue or <ctrl>+<c> to abort..."

SCRIPTPATH=$(dirname "$0")

# update os
sudo apt update
sudo apt full-upgrade

# ensure python environment and git
sudo apt install -y git python3-venv python3-dev
# tool to detect i2c ports (i2cdetect -y 1)
sudo apt install -y i2c-tools

# install libraries and tools
# install libs for OpenCV
sudo apt install -y libgsm1 libatk1.0-0 libavcodec58 libcairo2 libvpx6 libvorbisenc2 \
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
python3 -m venv ~/.venv/cv

# update pip
source ~/.venv/cv/bin/activate
pip install --upgrade pip

# install python requirements
cd ~/scrabscrap2/python
source ~/.venv/cv/bin/activate
pip install -r requirements.txt

# run scrabscrap at reboot
crontab -u pi $SCRIPTPATH/config/crontab.user

# Auto AP
sudo curl -L https://github.com/gitbls/autoAP/raw/master/autoAP.sh -o /usr/local/bin/autoAP.sh
sudo curl -L https://github.com/gitbls/autoAP/raw/master/install-autoAP -o /usr/local/bin/install-autoAP
sudo curl -L https://github.com/gitbls/autoAP/raw/master/rpi-networkconfig -o /usr/local/bin/rpi-networkconfig
sudo chmod 755 /usr/local/bin/autoAP.sh /usr/local/bin/install-autoAP /usr/local/bin/rpi-networkconfig
sudo /usr/local/bin/install-autoAP

echo "------------------------------"
echo "before using scrapscrap activate camera, spi, i2c with:"
echo "sudo raspi-config"
echo "------------------------------"
echo "if you want to commit to the GitHub Repo please provide a git user:"
echo "git config --global user.name"
echo "git config --global user.email"
echo "------------------------------"
echo "the OpenCV installation can be tested with:"
echo "source ~/.venv/cv/bin/activate"
echo "python3"
echo ">> import cv2"
echo ">> cv2.__version__"
echo "output OpenCV version number like: 4.x.x"
echo ">> quit()"
echo "------------------------------"
echo "test the i2c bus:"
echo "sudo i2cdetect -y 1"
echo "this should show the adress of the multiplexer (0x70)"
echo "------------------------------"

read -p "Press any key to continue ..."