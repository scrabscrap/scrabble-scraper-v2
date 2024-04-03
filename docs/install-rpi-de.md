---
output:
  pdf_document:
    path: pdf/install-rpi-de.pdf
    highlight: tango
geometry: margin=2cm
---

# Installation ScrabScrap v2

## Basis-Installation Raspberry OS (32-bit; Bullseye)

**Warnung: Raspberry OS Lite Bullseye nur im 32-bit Modus installieren!**

Die Erzeugung der SD Karte mittels "Raspberry Pi Imager". Hier das Image "Raspberry OS (Legacy; 32-bit) Lite - Debian Bullseye" auswählen.

Bei dem Erzeugen der SD Karte ggf. folgende Optionen konfigurieren

- hostname = scrabscrap
- ssh aktivieren = true
- WiFi Zugriff = ID / Passwort
- User / Passwort = (alter default: pi/raspberry)
- Spracheinstellungen

Nachdem der RPI gestartet wurde, per ssh eine Verbindung zum Rechner aufbauen und auf 32-bit Installation prüfen.

```bash
uname -m
```

Hier wird als Ausgaben "armv7l" erwartet. Im Anschluss das System aktualisieren.

```bash
sudo apt-get update
sudo apt-get upgrade
sudo apt-get autoremove
```

Nach dem Update technische Einstellungen auf dem RPI vornehmen

```bash
sudo raspi-config
```

Es müssen aktiviert werden

- Kamera
- i2c

Im nächsten Schritt werden allgemeine Hilfsmittel installiert

### Git und Python installieren

```bash
sudo apt-get install -y git python3-venv python3-dev i2c-tools

#Installation der Libs für OpenCV
sudo apt-get install -yq libzvbi0 libgfortran5 libpango-1.0-0 libsoxr0 libxcb-render0 libx264-160 libvpx6 libpangoft2-1.0-0 libsrt1.4-gnutls libpixman-1-0 libpgm-5.3-0 libvorbis0a libpangocairo-1.0-0 libavformat58 libcairo-gobject2 libvdpau1 libtheora0 libxcb-shm0 libva-x11-2 libssh-gcrypt-4 libudfread0 libgsm1 libmpg123-0 libavutil56 libva-drm2 libdatrie1 libx265-192 libgraphite2-3 libavcodec58 libopus0 libogg0 librabbitmq4 libnorm1 libxrender1 libxfixes3 libopenjp2-7 libwavpack1 libswresample3 libdrm2 libsodium23 librsvg2-2 libcairo2 libshine3 libopenmpt0 libbluray2 libswscale5 libgdk-pixbuf-2.0-0 libwebpmux3 libspeex1 libaom0 libharfbuzz0b libdav1d4 libvorbisenc2 libatlas3-base libzmq5 libgme0 libvorbisfile3 libthai0 libmp3lame0 libva2 libsnappy1v5 libcodec2-0.9 libtwolame0 ocl-icd-libopencl1 libchromaprint1 libxvidcore4 --fix-missing

#numpy lib
sudo apt-get install -yq libopenblas-dev
```

### Clone des ScrabScrap Repositories

Falls von dem RPI auch Commits an das Repository vorgenommen werden sollen, muss
die GitHub Userkennung gesetzt werden.

```bash
git config --global user.name
git config --global user.email
git config --global credential.helper store
git config --global pull.rebase true
git config --global pull.autostash true
```

Danach kann das Repository geladen werden

```bash
cd
git clone https://github.com/scrabscrap/scrabble-scraper-v2.git
```

### Python Konfiguration erzeugen

```bash
cd ~/scrabble-scraper-v2/python
python3 -m venv .venv --prompt cv
#update pip
source .venv/bin/activate
pip install -U pip setuptools wheel
pip install -U -r requirements.txt
```


## Basis-Installation des Raspberry OS (64-bit; Bookworm)

**Warnung: Raspberry OS Lite Bookworm nur im 64-bit Modus verwenden!**

Die Erzeugung der SD Karte mittels "Raspberry Pi Imager". Hier das Image "Raspberry OS (64-bit) Lite - Debian Bookworm" auswählen.

Bei dem Erzeugen der SD Karte ggf. folgende Optionen konfigurieren

- hostname = scrabscrap
- ssh aktivieren = true
- WiFi Zugriff = ID / Passwort
- User / Passwort = (alter default: pi/raspberry)
- Spracheinstellungen

Nachdem der RPI gestartet wurde, per ssh eine Verbindung zum Rechner aufbauen und auf 64-bit Installtion prüfen.

```bash
uname -m
```

Hier wird als Ausgaben "aarch64" erwartet. Im Anschluss das System aktualisieren.


```bash
sudo apt-get update
sudo apt-get upgrade
sudp apt-get autoremove
```

Nach dem Update technische Einstellungen auf dem RPI vornehmen

```bash
sudo raspi-config
```

Es müssen aktiviert werden

- i2c

Im nächsten Schritt werden allgemeine Hilfsmittel installiert

### Git und Python installieren

```bash
sudo apt-get install -y git python3-venv python3-dev i2c-tools
#installation picamera2 ohne gui
sudo apt install -y python3-picamera2 --no-install-recommends
```

### Clone des ScrabScrap Repositories

Falls von dem RPI auch Commits an das Repository vorgenommen werden sollen, muss
die GitHub Userkennung gesetzt werden.

```bash
git config --global user.name
git config --global user.email
git config --global credential.helper store
git config --global pull.rebase true
git config --global pull.autostash true
```

Danach kann das Repository geladen werden

```bash
cd
git clone https://github.com/scrabscrap/scrabble-scraper-v2.git
bzw.
git clone https://(user)@github.com/scrabscrap/scrabble-scraper-v2.git
```

### Python Konfiguration erzeugen

Im Gegensatz zur 32-bit Installation, wird hier die Kamera-Bibliothek global installiert. Damit muss bei dem Erzeugen der venv Umgebung die Option "--system-site-packages" angegeben werden.

```bash
cd ~/scrabble-scraper-v2/python
python3 -m venv .venv --system-site-packages --prompt cv
#update pip
source .venv/bin/activate
pip install -U pip setuptools wheel
pip install -U -r requirements.txt
```


## Testen der RPI Installation

Die Installation von OpenCV kann wie folgt geprüft werden

```bash
#venv cv aktivieren
source ~/scrabble-scraper-v2/python/.venv/bin/activate
python
>> import cv2
>> cv2.__version__
'4.6.0.66' bzw. '4.9.0.80' 
>> quit()
```

Prüfen des Zugriffes auf den i2c Bus

```bash
i2cdetect -y 1
```

Hier sollte der Port (3c) des Displays angezeigt werden. Falls eine RTC installiert ist, wird diese hier ebenfalls angezeigt.

## Weitere Konfigurationen

Eine Datei `~/.bash_aliases` anlegen:

```bash
alias ll='ls -al'
alias ..='cd ..'
alias ...='cd ../..'
alias cd..='cd ..'
alias workon='f(){ source ~/scrabble-scraper-v2/python/.venv/bin/activate; }; f'
```

In `.bashrc` oder `~/.zshrc` ergänzen

```bash
source ~/scrabble-scraper-v2/python/.venv/bin/activate
export PYTHONPATH=src:
```

## Autostart von ScrabScrap konfigurieren

Um ScrabScrap automatisch zu starten, muss man auf dem RPI (user pi) angemeldet sein und 
die Konfiguration des crontab-Eintrags des Benutzers vornehmen:

```bash
crontab -u pi ~/scrabble-scraper-v2/scripts/config/crontab.user
```

## boot/config.txt (bullseye) boot/firmware/config.txt (bookworm) einstellen

- i2c mit Baudrate 400000
- spi=off
- i2c bus 3 auf GPIO5 und GPIO6
- Power LED ausschalten
- Bluetooth ausschalten
- Audio aus
- Framebuffer und Memory für die Kamera

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

# Enable DRM VC4 V3D driver
# increase cma video ram
dtoverlay=vc4-kms-v3d,cma-320 
max_framebuffers=2
```

## Installation eines Develepment Rechners

siehe FAQ

## Automatischer HotSpot

siehe [GitHub Projekt https://github.com/gitbls/autoAP](https://github.com/gitbls/autoAP)

```bash
sudo apt install systemd-resolved
sudo curl -L https://github.com/gitbls/autoAP/raw/master/autoAP.sh -o /usr/local/bin/autoAP.sh
sudo curl -L https://github.com/gitbls/autoAP/raw/master/install-autoAP -o /usr/local/bin/install-autoAP
sudo curl -L https://github.com/gitbls/autoAP/raw/master/rpi-networkconfig -o /usr/local/bin/rpi-networkconfig
sudo chmod 755 /usr/local/bin/autoAP.sh /usr/local/bin/install-autoAP /usr/local/bin/rpi-networkconfig
sudo /usr/local/bin/install-autoAP
```

Als AP folgende Werte eingeben

- ssid = ScrabScrap
- psk = scrabscrap
- ip = 10.0.0.1

Zusätzlich muss noch ein lokales WLAN angegeben werden (i.d.R. das WLAN mit dem gerade eine Verbindung besteht).

```bash
sudo /usr/local/bin/rpi-networkconfig
``` 
auf `systemd-networkd` einstellen.


Befehle für den Zugriff auf die Netzwerkkonfiguration

```bash
iwgetid
wpa_cli list_networks -i wlan0
wpa_cli remove_network <number> -i wlan0
wpa_cli save_config
wpa_cli scan -i wlan0
wpa_cli scan_results -i wlan0
wpa_passphrase {ssid} {key}
```

## Sonstiges

### Installation RTC

Siehe: [Adding a Real Time Clock (RTC) to the Raspberry Pi](https://pimylifeup.com/raspberry-pi-rtc/)

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
