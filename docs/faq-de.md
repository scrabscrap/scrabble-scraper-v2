# FAQ

## Einrichten der WLAN Verbindung

Sofern keine gültige WLAN Verbindung aufgebaut werden kann, wechselt ScrabScrap in
den AP Mode und stellt ein WLAN `ScrabScrap` zur Verfügung. Das Default-Kennwort
lautet `scrabscrap` und sollte bei der ersten Nutzung geändert werden.

Nach Verbindung mit AP kann über die API-Web-Anwendung `http://10.0.0.1:5000` im
Menüpunkt `WiFi` nach aktiven WLAN Netzen gesucht werden und diese hinterlegt werden.

Nach ein Reboot verbindet sich `ScrabScrap` automatisch mit dem stärksten bekannten
WLAN.

## Spielernamen setzen

Die Spielernamen können über API-Web-Anwendung (`http://<ipadresse scrabscrap>:5000/`) gesetzt werden. Die Spielernamen
in die Eingabefelder eintragen und über `Submit` abspeichern. Hierbei sollte möglichst auf Umlaute und Leerzeichen
verzichtet werden.

Die Einstellung kann auch während des Spieles vorgenommen werden und wird dann beim nächsten Zug aktiv.

## Beleuchtung des Spielbrettes

Das Spielbrett sollte möglichst indirekt beleuchtet werden, um eine Schattenbildung zu vermeiden. Die
Qualität der Ausleichtung kann mit der API-Web-Anwendung (`http://<ipadresse scrabscrap>:5000/`) im Menüpunkt `Camera`
geprüft werden.

## Kamera justieren

Das Justieren der Kamera erfolgt über die API-Web-Anwendung (`http://<ipadresse scrabscrap>:5000/`). Hier den Menüpunkt `Camera`
aufrufen. Dann wird ein aktuelles Build mit überlagertem Gitter angezeigt. Sofern dies bereits passend ist, sind keine weiteren
Aktionen nötig.

Falls das Bild nicht passend erkannt wird, den Mnüpunkt `Clear Warp` auswählen. Damit wird die Warp Einstellung gelöscht
und das Spielbrett wird bei jeder Bild-Aufnahme dynmaisch ermittelt. Soll ein neuer Warp-Wert gespeichert werde, einfach
erneut in das Menü `Camera`wechseln. Ist die Erkennung jetzt korrekt, können mit `Store Warp` die Koordinaten wieder
gespeichert werden. Dies kann durchaus auch während eines Spieles gemacht werden, wenn z.B. ein Spieler versehentlich
gegen die Kamera gestoßen ist, und damit eventuell die Jusiterung verschoben hat.

Wird das Spieltfeld auf nach mehreren Versuchen nicht korrekt erkannt, kann auf dem unteren Bild mit der Maus in die
Spielfeldecken (einzeln) geklickt werden, dann werden die Koordinaten für den Warp verwendet.

Ist die Kamera nicht korrekt ausgerichtet, kann in dem unteren Bild der Ausschnitt der Kamera geprüft werden. Hier sollte
am Ende ein ca. 2cm weisser Rand um das Spielfeld herum eingestellt werden. Nach Korrektur des Kamera-Armes den `Reload`
Button drücken, damit das Bild neu aufgebaut wird.

## Settings

Die Settings der Anwendung werden über die INI-Datei `scrabscrap.ini` und `ftp-secret.ini` konfiguriert. In der
Datei `scrabscrap.ini` sind die Default-Werte in den einzelnen Sektionen unter dem Schlüssel `defaults` aufgeführt.
Es müssen nur die geänderten Werte abgespeichert werden.

Bei einem bereits gestartetem System können Änderungen über die Web-Oberfläche der
API-Schnittstelle vorgenommen werden. Hierzu einfach die URL `http://<ipadresse>:5000`
aufrufen. Einige Funktionen sind nur möglich, wenn sich die Anwendung entweder im Modus
`Start` oder `Pause`befindet.

## Test der Hardware

Wenn `scrabscrap`gestartet ist, kann über die API-Web-Anwendung ein Test der LEDs und der Displays
ausgelöst werden. Hierzu einfach die URL `http://<ipadresse>:5000` aufrufen und dann den Menü-Punkt
`Test` auswählen.

Durch den Aufruf der LED Tests werden verschiedene Modi der LEDs angezeigt (Ein/Aus/Blinken).
Beim Aufruf des Display-Test werden verschiedene Anzeigen der Reihe nach angezeigt.

## Erweiterung von ScrabScrap

### Abweichende Steine benutzen

Soll ein abweichender Satz an Scrabble-Steinen verwendet werden, müssen diese in einem geeigneten Format als Bilder zur
Verfügung stehen. Schwarzer Hintergrund mit weissem Text in der (Stein-)Größe ?x?. Es ist möglich nur einen Ausschnitt
des Steines zu speichern, dabei muss allerdings das Größenverhältnis erhalten bleiben.

Bei sehr ähnlichen Steinen empfiehlt es sich, den Buchstabenwert im Bild zu erhalten (z.B. bei A und Ä führt der abweichende
Buchstabenwert zu einer verbesserten Erkennung).

Der Pfad auf die Steine kann in der Konfigurationsdatei "scrabble.ini" angepasst werden. Der Vorgabewert für diesen Pfad
ist `<python-src-dir>/game_board/img/default/`.

Werden abweichende Farben genutzt, ist u.U. eine Erweiterung der Methode `filter_image` vorzunehmen, damit die Steine auf
dem Brett korrekt erkannt werden können.

### Unterstützung weiterer Sprachen

Es können grundsätzlich unterschiedliche Sprachen unterstützt werden. Hierzu müssen die Anzahl der Steine für die jeweiligen
Buchstaben und deren Scoring-Werte konfiguriert werden.

Diese Einstellung wird in der `scrabble.ini` vorgenommen. Beispiele für die Sprachen `en` und `fr` sind hier bereits
enthalten. Üblicherweise muss hierzu auch ein passendes Set an Steinen verwendet werden.

### Unterstützung weiterer Spielbretter

Eine Unterstützung weiterer Spielbretter geht mit einer Anpassung der Software einher. Hierzu müssen die Methoden `warp` und
`filter_image`implementiert werden.

`warp` sorgt für ein korrekt rotiertes, skaliertes und normiertes Bild des Spielbrettes. Als Ergebnis muss hier eine
Bildgröße von 800x800px mit einem 25px Rand zu dem eigentlichen Spielfeld erzeugt werden. Damit ist das Gitter des
Spielfeldes auf 750x750px normiert.

`filter_image` dient zur Prüfung welche Felder auf dem Spielbrett durch Steine belegt sind, um den Erkennungprozess der
Buchstaben zu optimieren. Algortihmisch wird ausgehend vom Zentrum die jeweiligen Nachbarfelder geprüft bis keine weiteren
gelegten Steine mehr erkannt werden.

## Development

### Nutzung von GitPod

Die Konfiguration zur Nutzung von VSCode innerhalb von GitPod ist bereits vorgesehen. Um dies
zu verwenden einfach auf den folgenden Button drücken, dann wird eine entsprechende Umgebung
gestartet:

[![Open in Gitpod](https://gitpod.io/button/open-in-gitpod.svg)](https://gitpod.io/#https://github.com/scrabscrap/scrabble-scraper-v2)

### Einrichten eines Entwicklungssystems unter Mac OS

Installation der notwendigen Tools per [Homebrew](https://brew.sh/index_de).

```bash
brew install git
brew install node
brew install python@3.9
brew install visual-studio-code --cask
```

Jetzt ggf. Git-Kennungen einrichten.

```bash
git config --global user.name "..."
git config --global user.email "..."
```

Danach wird mittels Python die virtuelle Umgebung einrichtet.

```bash
python3 -m venv ~/.venv/cv
source ~/.venv/cv/bin/activate
```

Das Repository kann nun in das Zielverzeichnis gecloned werden.

```bash
cd <zielordner>
git clone https://github.com/scrabscrap/scrabble-scraper-v2.git
```

Im Anschluss können die Python Bibliotheken installiert werden.

```bash
cd scrabble-scraper-v2/python
source ~/.venv/cv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Bibliotheken, die nicht unter MacOS lauffähig sind, werden in den "requirements.txt"
ausgespart.

Danach kann das Projekt bereits mit VSCode der Workspace
`scrabble-scrapber-v2.code-workspace` geöffnet werden. In VSCode
muss dann als Python Interpreter ('cv', venv) ausgewählt werden.

Als Workspace Folder werden folgende Verzeichnisse angelegt

* Python
* Web-App
* Documentation
* Scripts

### Zugriff über einen ssh-Key

(lokaler Rechner)

```bash
cd ~/.ssh
#erzeugen des scrabsrap ssh-keys
ssh-keygen -f ~/.ssh/scrabscrap -t ecdsa
#kopieren auf dem RPI ! user@host ! anpassen
ssh-copy-id -i ~/.ssh/scrabscrap user@host
```

Für den lokalen Rechner für den Host ``scrabscrap`` eine abweichende ssh-keys konfigurieren.

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

### VS Code Erweiterungen

In VSCode sollten dann folgende Erweiterungen installiert werden.

* GitLess
* GitGraph
* markdownlint (David Anson)
* Python (Microsoft)
* Pylance (Microsoft)
* optional: vscode-pdf

soll eine Remote-Entwicklung auf dem Raspberry PI erfolgen, dann müssen noch

* Remote SSH (Microsoft)
* Remote SSH: Editing Configuration Files (Microsoft)

installiert werden.

### Zugriff über VS Code

Auf dem lokalen Rechner sollte VS Code mit folgenden Plugins installiert werden

* GitLess
* GitGraph
* markdownlint (David Anson)
* Python (Microsoft)
* Pylance (Microsoft)
* Html Preview (George Oliveira)

Dann kann eine Remote Verbindung zum RPI aufgebaut werden. Hierzu werden zusätzliche Hilfsmittel
auf dem RPI installiert.

Danach kann von dem lokalen Rechner über ssh Entwicklung auf dem RPI durchgeführt werden.

Nach dem Start der ssh Verbindung kann der Workspace `~/scrabble-scraper-v2/scrabble-scraper-v2.code-workspace`
geöffnet werden.

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

### Einstellung .alias

Es bietet sich an, folgende Alias-Einträge anzulegen.

```text
alias workon='f() { source ~/.venv/$1/bin/activate };f'
alias python=python3
```

#### Einstellung .zshrc

Damit die Ausführung in VSCode von Python-Code auch im RUN-Modus funktioniert, muss in
der .zshrc folgendes ergänzt werden:

```bash
export PYTHONPATH=src:$PYTHONPATH
```

## Erzeugung der Dokumentation

Damit die Dokumentation in Form von PDF Dateien erzeugt werden kann, muss auf dem System

* pandoc
* texlive

installiert sein.

Dann kann in dem Verzeichnis `docs` mit dem Script `make_pdf.sh` die Dokumentation erzeugt werden.

## Start der Python Anwendungen

### Raspberry PI

Auf dem Raspberry PI kann die Anwendung wie folgt gestartet werden

```bash
cd python/src
# ggf. workon cv
python scrabscrap.py
```

Die API zum Einstellen von Parametern steht danach unter

* `http://localhost:5000`

zur Verfügung.

Sollte ein Zugriff über `localhost`nicht funktionieren, bitte statt `localhost` die IPv4 Adresse des
Rechners verwenden.

### MacOS / GitPod

Hier kann die Hardware des Raspberry PI nicht genutzt werden, daher muss eine Simulation erfolgen.

Zum Start des Simulators folgenden Aufruf verwenden

```bash
cd python/simulator
python simulator.py
````

Die simulierte Anwendung kann dann im lokalen Browser über

* `http://localhost:5000`

aufgerufen werden.

Sollte ein Zugriff über `localhost`nicht funktionieren, bitte statt `localhost` die IPv4 Adresse des
Rechners verwenden.

## Start der Web-Anwendung

Damit in der Web-Anwendung die Daten der Python-Anwendung angezeigt werden, muss ein symbolischer
Link angelegt werden:

```bash
cd react/public
ln -s ../../python/work/web web
```

Damit stehen dann die Daten, die in der Python-Anwendung erzeugt werden lokal zur Verfügung.

Die Initialisierung der node_modules erfolgt mit:

```bash
cd react
npm install
```

Der Start der Web-Anwendung erfolgt dann mit

```bash
cd react
npm start
````

Die Web-Anwendung kann dann im lokalen Browser unter

* `http://localhost:3000`

aufgerufen werden.

## Fehlerbehebung
