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
sudo apt-get -y --with-new-pkgs upgrade

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
  pip install -U -r requirements.txt --upgrade-strategy=eager

else
  echo 'armv7l no longer supported'
  exit 1
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
echo "output OpenCV version number like: 4.10.0"
echo ">> quit()"
echo "------------------------------"
echo "test the i2c bus:"
echo "sudo i2cdetect -y 1"
echo "this should show the adress of the display / rtc (0x3c)"
echo "------------------------------"

read -p "Press any key to continue ..."