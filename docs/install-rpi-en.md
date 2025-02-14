# Installation ScrabScrap v2

The installation of ScrabScrap under 32-bit operating system and Python < 3.11 is no longer supported.

## Basic installation Raspberry OS (64-bit; Bookworm)

**Warning: install Raspberry OS Lite Bookworm only in 64-bit!**

The creation of the SD card using "Raspberry Pi Imager". Select the image "Raspberry OS (64-bit) Lite - Debian Bookworm".

When creating the SD card, configure the following options if necessary

- hostname = scrabscrap
- enable ssh = true
- WiFi access = ID / password
- user / password = (old default: pi/raspberry)
- Language settings

After starting the RPI, connect to the computer via ssh 
and verify 64-bit installation.

```bash
uname -m
```

Expected output is "aarch64". Then update the system.

```bash
sudo apt update
sudo apt full-upgrade
sudo apt-get autoremove
```

After the update, make technical settings on the RPI

```bash
sudo raspi-config
```

The following must be activated

- i2c

The next step is to install general tools.

### Install Git and Python

```bash
sudo apt-get install -y git python3-venv python3-dev i2c-tools
#install picamera2 without gui
sudo apt install -y python3-picamera2 --no-install-recommends
```

### Clone of the ScrabScrap repository

If the RPI is also to commit to the repository, the GitHub user ID must be set.

```bash
git config --global user.name
git config --global user.email
git config --global credential.helper store
git config --global pull.rebase true
git config --global pull.autostash true
```

After that the repository can be loaded

```bash
cd
git clone https://github.com/scrabscrap/scrabble-scraper-v2.git
or
git clone https://(user)@github.com/scrabscrap/scrabble-scraper-v2.git
```



### Create Python configuration

The camera library is installed globally under 64-bit PI OS. This means that the "--system-site-packages" option must be 
specified when creating the venv environment.

```bash
cd ~/scrabble-scraper-v2/python
python3 -m venv .venv --system-site-packages --prompt cv
#update pip
source .venv/bin/activate
pip install -U pip setuptools wheel
pip install -U -r requirements.txt
```

## Testing the RPI installation

The installation of OpenCV can be tested as follows

```bash
#enable venv cv
source ~/scrabble-scraper-v2/python/.venv/bin/activate
python
>> import cv2
>> cv2.__version__
'4.10.0'
>> quit()
```

Checking access to the i2c bus

```bash
i2cdetect -y 1
```
The port (3c) of the display should be shown here. If an RTC is installed, it will also be displayed here.

## Further configurations

Create a file ``~/.bash_aliases``:

```bash
alias ll='ls -al'
alias ..='cd ..'
alias ...='cd ../..'
alias cd..='cd ..'
alias workon='f(){ source ~/scrabble-scraper-v2/python/.venv/bin/activate; }; f'
```

Add to `~/.bashrc` or `~/.zshrc`:

```text
source ~/scrabble-scraper-v2/python/.venv/bin/activate
export PYTHONPATH=src:
```

## Configure autostart of ScrabScrap

In order to start ScrabScrap automatically, one must be logged in on the RPI and then, via `crontab -e`.
to configure the user's crontab entries:

```bash
crontab -u pi ~/scrabble-scraper-v2/scripts/config/crontab.user
```

## set boot/config.txt (bullseye) or boot/firmware/config.txt (bookworm)

- i2c with baud rate 400000
- spi=off
- i2c bus 3 on GPIO5 and GPIO6
- Switch off power LED
- Bluetooth off
- Audio off
- camera framebuffer and memory (only bookworm)

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

#### only bookworm ####
# Enable DRM VC4 V3D driver
# increase cma video ram
dtoverlay=vc4-kms-v3d,cma-320 
max_framebuffers=2
```

## Installation of a develepment computer

see FAQ

## Automatic HotSpot

see [GitHub project https://github.com/gitbls/autoAP](https://github.com/gitbls/autoAP)

```bash
sudo apt install systemd-resolved
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
