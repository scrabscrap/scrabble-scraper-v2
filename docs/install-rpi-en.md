# Installation ScrabScrap v2

## Basic installation of the RPI

The creation of the SD card using "Raspberry Pi Imager". Select the image "PI OS Lite (32bit) - Debian Bullseye".
The 64Bit image does not yet fully support the PiCamera completely.

When creating the SD card, configure the following options if necessary

- hostname = scrabscrap
- enable ssh = true
- WiFi access = ID / password
- user / password = (old default: pi/raspberry)
- Language settings

After starting the RPI, connect to the computer via ssh.

```bash
sudo apt update
sudo apt full-upgrade
```

After the update, make technical settings on the RPI

```bash
sudo raspi-config
```

The following must be activated

- camera
- i2c

The next step is to install general tools

### Install Git and Python

```bash
sudo apt install -y git python3-venv python3-dev
#install the tool to detect the ic2 ports (i2cdetect -y 1)
sudo apt install -y i2c-tools
#install the libs for OpenCV
sudo apt-get install -yq libgsm1 libatk1.0-0 libavcodec58 libcairo2 libvpx6 libvorbisenc2 
libwayland-egl1 libva-drm2 libwavpack1 libshine3 libdav1d4 libwayland-client0 libxcursor1 
libopus0 libchromaprint1 libxinerama1 libpixman-1-0 libzmq5 libmp3lame0 libxcb-shm0 libsz2 
libgtk-3-0 libharfbuzz0b libilmbase25 libvdpau1 libssh-gcrypt-4 libpangocairo-1.0-0 
libtwolame0 libnorm1 libxi6 libxfixes3 libxcomposite1 libxcb-render0 libwayland-cursor0 
libvorbisfile3 libspeex1 libxrandr2 libxkbcommon0 libtheora0 libaec0 libx264-160 libaom0 
libzvbi0 libopenexr25 libogg0 libpangoft2-1.0-0 librsvg2-2 libxvidcore4 libsrt1.4-gnutls 
libbluray2 libvorbis0a libdrm2 libmpg123-0 libatlas3-base libxdamage1 libavformat58 
libatk-bridge2.0-0 libswscale5 libsnappy1v5 libcodec2-0.9 libsodium23 libudfread0 
libswresample3 libcairo-gobject2 libx265-192 libthai0 libva-x11-2 ocl-icd-libopencl1 
libepoxy0 libpango-1.0-0 libavutil56 libva2 librabbitmq4 libgme0 libatspi2.0-0 
libgraphite2-3 libhdf5-103-1 libgfortran5 libsoxr0 libpgm-5.3-0 libopenmpt0 libxrender1 
libdatrie1 libgdk-pixbuf-2.0-0 libopenjp2-7 libwebpmux3 libopenblas-dev --fix-missing
```

### Clone of the ScrabScrap repository

If the RPI is also to commit to the repository, the GitHub user ID must be set.

```bash
git config --global user.name
git config --global user.email
```

After that the repository can be loaded

```bash
cd
git clone https://github.com/scrabscrap/scrabble-scraper-v2.git
```

### Create Python configuration

```bash
cd ~/scrabble-scraper-v2/python
python3 -m venv .venv --prompt cv
#update pip
source .venv/bin/activate
pip install -U pip setuptools wheel
pip install --force-reinstall -r requirements.txt --only-binary=:all:
```

## Testing the RPI installation

The installation of OpenCV can be tested as follows

```bash
#enable venv cv
source ~/scrabble-scraper-v2/python/.venv/bin/activate
python
>> import cv2
>> cv2.__version__
'4.5.5'
>> quit()
```

Checking access to the i2c bus

```bash
sudo i2cdetect -y 1
```

## Further configurations

Create a file ``~/.alias``:

```bash
alias ll='ls -al'
alias ..='cd ..'
alias ...='cd ../..'
alias cd..='cd ..'
alias workon='f(){ source ~/scrabble-scraper-v2/python/.venv/bin/activate; }; f'
```

Add to `~/.bashrc` or `~/.zshrc`:

```text
source ~/.alias
```

## Configuring the Autostart of ScrabScrap

In order to start ScrabScrap automatically, one must be logged in on the RPI and then, via `crontab -e`.
to configure the user's crontab entries:

```bash
@reboot /home/pi/scrabble-scraper-v2/scripts/scrabscrap.sh &
```

## set boot/config.txt

- i2c with baud rate 400000
- spi=off
- i2c bus 3 on GPIO5 and GPIO6
- Switch off power LED
- Bluetooth off
- Audio off

```text
# Uncomment some or all of these to enable the optional hardware interfaces
dtparam=i2c_arm=on,i2c_baudrate=400000
#dtparam=i2s=on
dtparam=spi=off

# use gpio5 (pin 29) as sda and gpio6 (pin 31) as scl
# see https://www.instructables.com/Raspberry-PI-Multiple-I2c-Devices/
dtoverlay=i2c-gpio,bus=3,i2c_gpio_delay_us=1,i2c_gpio_sda=5,i2c_gpio_scl=6

#Power-LED ausschalten
dtparam=pwr_led_trigger=none
dtparam=pwr_led_activelow=off
# Disable Bluetooth
dtoverlay=disable-bt

#Camera LED off
# disable_camera_led=1

# Uncomment this to enable infrared communication.
#dtoverlay=gpio-ir,gpio_pin=17
#dtoverlay=gpio-ir-tx,gpio_pin=18

# Additional overlays and parameters are documented /boot/overlays/README

# Enable audio (loads snd_bcm2835)
dtparam=audio=off
```

## Installation of a develepment computer

see FAQ

## Automatic HotSpot

see [GitHub project https://github.com/gitbls/autoAP](https://github.com/gitbls/autoAP)

```bash
sudo curl -L https://github.com/gitbls/autoAP/raw/master/autoAP.sh -o /usr/local/bin/autoAP.sh
sudo curl -L https://github.com/gitbls/autoAP/raw/master/install-autoAP -o /usr/local/bin/install-autoAP
sudo curl -L https://github.com/gitbls/autoAP/raw/master/rpi-networkconfig -o /usr/local/bin/rpi-networkconfig
sudo chmod 755 /usr/local/bin/autoAP.sh /usr/local/bin/install-autoAP /usr/local/bin/rpi-networkconfig
sudo /usr/local/bin/install-autoAP
```

Enter the following values as AP

- ssid = ScrabScrap
- psk = scrabscrap
- ip = 10.0.0.1

In addition, a local WLAN must be specified (usually the WLAN with which there is currently a connection).

At the end, if necessary, set `sudo /usr/local/bin/rpi-networkconfig` to `systemd-networkd`.

Commands for accessing the network configuration

```bash
iwgetid
wpa_cli list_networks -i wlan0
wpa_cli remove_network <number> -i wlan0
wpa_cli save_config
wpa_cli scan -i wlan0
wpa_cli scan_results -i wlan0
wpa_passphrase {ssid} {key}
```

## Miscellaneous

### Installation RTC

See [Adding a Real Time Clock (RTC) to the Raspberry Pi](https://pimylifeup.com/raspberry-pi-rtc/)

```bash
sudo nano /boot/config.txt
```

Add (currently used: DS3231 RTC)

```text
dtoverlay=i2c-rtc,ds3231
```

```bash
sudo reboot
sudo apt -y remove fake-hwclock
sudo update-rc.d -f fake-hwclock remove
sudo nano /lib/udev/hwclock-set
```

Comment out

```text
#if [ -e /run/systemd/system ] ; then
#    exit 0
#fi
```

Read the time directly from the RTC module

```bash
sudo hwclock -v -r
```
