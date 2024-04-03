#!/usr/bin/env bash 

echo "## pre setup steps ##"
echo "sudo apt install -y git"
echo "git config --global user.name"
echo "git config --global user.email"
echo "git config --global credential.helper store"
echo "git config --global pull.rebase true"
echo "git config --global pull.autostash true"
echo "cd ~"
echo "git clone https://github.com/scrabscrap/scrabble-scraper-v2.git"
echo "bzw. git clone https://(user)@github.com/scrabscrap/scrabble-scraper-v2.git"
echo "## end pre setup steps ##"
read -p "Press any key to continue or <ctrl>+<c> to abort..."

SCRIPTPATH=$(dirname "$0")

# update os
sudo apt-get -y update
sudo apt-get -y upgrade

# ensure python environment and git
sudo apt-get install -yq git python3-venv python3-dev i2c-tools

if [ $(uname -m) == 'aarch64' ]; then
  # install 64bit on rpi os bookworm

  sudo apt-get install -yq python3-picamera2 --no-install-recommends

  # pip & venv
  cd ~/scrabble-scraper-v2/python
  python3 -m venv .venv  --system-site-packages --prompt cv
  source ~/scrabble-scraper-v2/python/.venv/bin/activate
  pip install -U pip setuptools wheel
  pip install -U -r requirements.txt

else
  # install 32bit bullseye (armv7l)
  
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


  # create an OpenCV Python environment
  cd ~/scrabble-scraper-v2/python
  python3 -m venv .venv --prompt cv

  # update pip
  source ~/scrabble-scraper-v2/python/.venv/bin/activate
  pip install -U pip setuptools wheel

  # install python requirements
  cd ~/scrabscrap2/python
  source .venv/bin/activate
  pip install -U -r requirements.txt
fi

# cleanup apt
sudo apt -yq autoremove

# run scrabscrap at reboot
crontab -u pi $SCRIPTPATH/config/crontab.user

# Auto AP
sudo apt-get install -yq systemd-resolved
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
echo "output OpenCV version number like: 4.6.0 or 4.9.0"
echo ">> quit()"
echo "------------------------------"
echo "test the i2c bus:"
echo "sudo i2cdetect -y 1"
echo "this should show the adress of the display / rtc (0x3c)"
echo "------------------------------"

read -p "Press any key to continue ..."