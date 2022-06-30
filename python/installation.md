# Installation ScrabScrap v2

## Basis-Installation des RPI

Die Erzeugung der SD Karte mittels "Raspberyy Pi Imager". Hier das Image "PI OS Lite (32bit) - Debian Bullseye" auswählen.

Bei dem Erzeugen der SD Karte ggf. folgende Optionen konfigurieren

- hostname = scrabscrap
- ssh aktivieren = true
- WiFi Zugriff = ID / Passwort
- User / Passwort = (alter default: pi/raspberry)
- Spracheinstellungen

Nachdem der RPI gestartet wurde, per ssh eine Verbindung zu dem Rechner aufbauen.

```bash
sudo apt-get update
sudo apt-get dist-upgrade
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

```bash
#git
sudo apt-get install git
#venv f. python
sudo apt-get install python3-venv
#ein environment cv f. python anlegen
python3 -m venv ~/.venv/cv --system-site-packages
#update pip
source ~/.venv/cv/bin/activate
pip install --upgrade pip
#installtion der pip libs
pip install --upgrade gpiozero imutils visual-logging wheel
#installation der pip lib für das oled Display
pip install --upgrade Pillow adafruit-circuitpython-ssd1306
#installation des Tools, um die ic2 Ports zu ermitteln (i2cdetect -y 1)
sudo apt-get install i2c-tools
#optional(python formatierung, profiling)
pip install --upgrade autopep8 cpython snakeviz
#optional ?? flask
pip install flask-restful
```

Die Installation von OpenCV erfolgt jetzt ohne compile

- siehe siehe <https://www.piwheels.org/project/opencv-contrib-python/>
- siehe <https://singleboardblog.com/install-python-opencv-on-raspberry-pi/>

```bash
sudo apt-get install libgsm1 libatk1.0-0 libavcodec58 libcairo2 libvpx6 libvorbisenc2 \
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
```

Nach erfolgreicher installation der benötigten Libraries, kann die Python Bibliothek per ``pip``
installiert werden.

```bash
source ~/.venv/cv/bin/activate
pip install opencv-python==4.5.5.62 opencv-contrib-python==4.5.5.62
```

## Testen der RPI Installation

Die Installation von OpenCV kann wie folgt geprüft werden

```bash
#venv cv aktivieren
source ~/.venv/cv/bin/activate
python3
>> import cv2
>> cv2.__version__
'4.5.3'
>> quit()
```

Prüfen des Zugriffes auf den i2c Bus

```bash
sudo i2cdetect y -1
```

Hier solte die Adresse des Multiplexers angezeigt werden (0x70). Die weiteren Adressen (RTC / OLED Display 0x3c)
werden erst nach dem Aktivieren über den Multiplexer angezeigt.

```python
from smbus import SMBus

i2cbus = SMBus(1)
i2cbus.write_byte(0x70, 1 << <port auf dem mux>)
```

## ScrabScrap Projekt laden (auf dem RPI)

Falls von dem RPI auch Commits an das Repository vorgenommen werden sollen, muss
die GitHub Userkennung gesetzt werden.

```bash
git config user.name
git config user.email
```

Danach kann das Repository geladen werden

```bash
cd
git clone https://github.com/scrabscrap/scrabble-scraper.git
```

## Weitere Konfigurationen

Eine Datei ``~/.alias`` anlegen

```text
alias ll='ls -al'
alias ..='cd ..'
alias ...='cd ../..'
alias cd..='cd ..'
alias workon='f() { source ~/.venv/$1/bin/activate };f'
```

In der ``~/.bashrc`` bzw. ``~/.zshrc`` am Ende ergänzen

```text
source ~/.alias
```

## Autostart von ScrabScrap konfigurieren

TODO: ergänzen

## Installation eines Develepment Rechners

### Installation der Bibliotheken

Installation von Python 3.9

```bash
brew install python@3.9
```

Alias für ``python3``anlegen

```text
alias workon='f() { source ~/.venv/$1/bin/activate };f'
alias python=python3
```

Installation von venv

```bash
python pip install pip --upgrade
python -m pip install --user virtualenv
python -m venv ~/.venv/cv
```

Installation der Libraries

```bash
workon cv
pip install --upgrade gpiozero imutils visual-logging wheel
pip install --upgrade Pillow
pip install --upgrade autopep8 cpython snakeviz
```

Installation OpenCV

```bash
pip install opencv-python==4.5.5.62 opencv-contrib-python==4.5.5.62
```

## Zugriff über einen ssh-Key

(lokaler Rechner)

```bash
cd ~/.ssh
#erzeugen des scrabsrap ssh-keys
ssh-keygen -f ~/.ssh/scrabscrap -t ecdsa
#kopieren auf dem RPI ! user@host ! anpassen
ssh-copy-id -i ~/.ssh/scrabscrap user@host
```

Für den lokalen Rechner für den Host ``scrapscrap`` eine abweichende ssh-keys konfigurieren.

```bash
nano ~/.shh/config 
```

folgende Einträge ergänzen

```text
Host scrabscrap
  HostName scrabscrap
  User <username>
  IdentityFile ~/.ssh/scrabscrap
```

### Zugriff über VS Code

Auf dem lokalen Rechner sollte VS Code mit folgenden Plugins installiert werden

- Remote - SSH (Microsoft)
- Remote Development (Microsoft)
- isort (Microsoft)
- Python (Microsoft)
- Pylance (Microsoft)
- React Native Tools (Microsoft)

Dann kann eine Remote Verbindung zum RPI aufgebaut werden. Hierzu werden zusätzliche Hilfsmittel
auf dem RPI installiert.

Danach kann von dem lokalen Rechner über ssh Entwicklung auf dem RPI durchgeführt werden.

Nach dem Start der ssh Verbindung kann das Verzeichnis ``~/scrabscrap/python`` geöffnet werden.

### Lint und Format

```bash
pip install flake8 autopep8
```

Parameter flake8

```json
    "python.linting.flake8Args": [
        "--max-line-length=128",
        "--ignore=E402"
      ],
```

Parameter autopep8

```json
    "python.formatting.autopep8Args": [
        "--max-line-length=128",
        "--ignore=E402"
      ],
```
