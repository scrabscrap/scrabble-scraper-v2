# Installation ScrabScrap v2

## Basis-Installation des RPI

Die Erzeugung der SD Karte mittels "Raspberry Pi Imager". Hier das Image "PI OS Lite (32bit) - Debian Bullseye" auswählen. Das 64Bit Image unterstützt z.Zt. noch nicht
vollständig die PiCamera.

Bei dem Erzeugen der SD Karte ggf. folgende Optionen konfigurieren

- hostname = scrabscrap
- ssh aktivieren = true
- WiFi Zugriff = ID / Passwort
- User / Passwort = (alter default: pi/raspberry)
- Spracheinstellungen

Nachdem der RPI gestartet wurde, per ssh eine Verbindung zum Rechner aufbauen.

```bash
sudo apt update
sudo apt full-upgrade
```

Nach dem Update technische Einstellungen auf dem RPI vornehmen

```bash
sudo raspi-config
```

Es müssen aktiviert werden

- Kamera
- spi
- i2c

Im nächsten Schritt werden allgemeine Hilfsmittel installiert

### Git und Python installieren

```bash
sudo apt install -y git python3-venv python3-dev
#installation des Tools, um die ic2 Ports zu ermitteln (i2cdetect -y 1)
sudo apt install -y i2c-tools
#Installation der Libs für OpenCV
sudo apt install -y libgsm1 libatk1.0-0 libavcodec58 libcairo2 libvpx6 libvorbisenc2 
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
libdatrie1 libgdk-pixbuf-2.0-0 libopenjp2-7 libwebpmux3 --fix-missing
```

### Clone des ScrabScrap Repositories

Falls von dem RPI auch Commits an das Repository vorgenommen werden sollen, muss
die GitHub Userkennung gesetzt werden.

```bash
git config --global user.name
git config --global user.email
```

Danach kann das Repository geladen werden

```bash
cd
git clone https://github.com/scrabscrap/scrabble-scraper-v2.git
```

### Python Konfiguration erzeugen

```bash
python3 -m venv ~/.venv/cv
#update pip
source ~/.venv/cv/bin/activate
pip install --upgrade pip

#im scrabscrap python Verzeichnis
#wichtig: venv cv muss aktiviert sein 
pip install -r requirements.txt
```

## Testen der RPI Installation

Die Installation von OpenCV kann wie folgt geprüft werden

```bash
#venv cv aktivieren
source ~/.venv/cv/bin/activate
python
>> import cv2
>> cv2.__version__
'4.5.5'
>> quit()
```

Prüfen des Zugriffes auf den i2c Bus

```bash
sudo i2cdetect -y 1
```

Hier sollte die Adresse des Multiplexers angezeigt werden (0x70). Die weiteren Adressen (RTC / OLED Display 0x3c)
werden erst nach dem Aktivieren über den Multiplexer angezeigt.

```python
from smbus import SMBus

i2cbus = SMBus(1)
i2cbus.write_byte(0x70, 1 << <port auf dem mux>)
```

## Weitere Konfigurationen

Eine Datei ``~/.alias`` anlegen:

```bash
alias ll='ls -al'
alias ..='cd ..'
alias ...='cd ../..'
alias cd..='cd ..'
alias workon='f(){ source ~/.venv/$1/bin/activate; }; f'
```

In der ``~/.bashrc`` bzw. ``~/.zshrc`` am Ende ergänzen:

```text
source ~/.alias
```

## Autostart von ScrabScrap konfigurieren

Um ScrabScrap automatisch zu starten, muss man auf dem RPI angemeldet sein und dann über `crontab -e`
die Konfiguration der crontab-Einträge des Benutzers vornehmen:

```bash
@reboot /home/pi/scrabble-scraper-v2/scripts/scrabscrap.sh &
```

## Installation eines Develepment Rechners

siehe FAQ

## Automatischer HotSpot

siehe Artikel [Automatischer HotSpot](https://raspberrypi.stackexchange.com/questions/100134/wpa-supplicant-dnsmasq-fallback-to-ap-mode-if-no-wifi-connection).

```bash
sudo apt install -y dnsmasq
```

edit /etc/dnsmasq.conf

```text
port=0

interface=wlan0
dhcp-authoritative
dhcp-leasefile=/tmp/dhcp.leases
dhcp-range=10.0.0.2,10.0.0.10,24h
#subnet mask
dhcp-option=1,255.0.0.0

#Do not send gateway to client
dhcp-option=3
#Disable DNS
dhcp-option=6
```

edit /etc/network/interfaces

```text
# interfaces(5) file used by ifup(8) and ifdown(8)
# Include files from /etc/network/interfaces.d:
source /etc/network/interfaces.d/*

auto lo
iface lo inet loopback

auto wlan0
iface wlan0 inet manual
  # wpa-driver nl80211
  wpa-roam /etc/wpa_supplicant/wpa_supplicant.conf

iface dhcp_server inet static
  address 10.0.0.1
  netmask 255.0.0.0

iface dhcp_client inet dhcp
```

edit /etc/wpa_supplicant/wpa_supplicant.conf

```text
country=DE
ctrl_interface=DIR=/var/run/wpa_supplicant
ap_scan=1

update_config=1

# ap entry - do not delete
network={
    ssid="ScrabScrap"
    mode=2
    key_mgmt=WPA-PSK
    proto=RSN
    pairwise=CCMP
    group=CCMP
    psk="scrabscrap"
    id_str="dhcp_server"
    priority=-10
}

# dummy entry - do not delete
network={
    ssid="DummySSID_do_not_delete"
    key_mgmt=WPA-PSK
    psk="invalidpassword"
    id_str="dhcp_client"
}
```

Damit das automatische Umschalten auf den Access-Point funktioniert, muss ein WPA Eintrag
für den "dhcp_client" vorhanden sein. Dieser sollte ungültige Werte enthalten, damit
der Access-Point Fallback aktiviert wird.

Service dnsmasq aktivieren

```bash
sudo systemctl enable dnsmasq.service
```

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

### Rote Power LED ausschalten

in `\boot\config.txt`` ergänzen

```text
#Power-LED ausschalten
dtparam=pwr_led_trigger=none
dtparam=pwr_led_activelow=off
```

in `/etc/crontab`

```text
@reboot echo 0 >/sys/class/leds/led1/brightness
```

### Kamera LED ausschalten

in `/boot/config.txt`

```text
disable_camera_led=1
```

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
