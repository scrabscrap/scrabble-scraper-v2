# FAQ

## Vorbereitungen

### Nach dem Aufbau

Folgende Schritte sind nach dem Aufbau des Systems empfohlen

1. Einschalten des Rechners
2. Falls nur unbekannte WLANs im Bereich sind, "Einrichten der WLAN Verbindung" durchführen
3. Im Browser auf die Web-Anwendung von ScrabScrap navigieren
4. Kamera-Arm justieren
5. Einstellungen / Konfiguration prüfen (FTP Verbindung, verwendetes Scrabble Brett usw.)
6. sofern ein FTP Upload verwendet wird, ein "Mini-Test-Spiel" machen und prüfen, ob ein
  Upload der Daten korrekt erfolgt

### Vor jedem Spiel

1. In der Web-Anwendung prüfen, ob das Spielfeld noch korrekt erkannt wird
2. Spielernamen setzen

### Nach jedem Spiel

1. Prüfen, ob das Spiel korrekt beendet wurde (Schalter "End" länger als 3s gedrückt)
2. Danach blinkt der gelbe Button. Es wird das aktuelle Spiel komprimiert und ggf. an den Server hochgeladen
3. Um ein neues Spiel zu beginnen, einen beliebigen Button drücken
4. Es sollte "Name1" und "Name2" im Display angezeigt werden

## Einrichten der WLAN Verbindung

Sofern keine gültige WLAN Verbindung aufgebaut werden kann, wechselt ScrabScrap in
den AP Mode und stellt ein WLAN `ScrabScrap` zur Verfügung. Das Default-Kennwort
lautet `scrabscrap` und sollte bei der ersten Nutzung geändert werden.

Nach Verbindung mit AP kann über die API-Web-Anwendung `http://10.0.0.1:5050` im
Menüpunkt `WiFi` nach aktiven WLAN Netzen gesucht werden und diese hinterlegt werden.

Nach einem Reboot verbindet sich `ScrabScrap` automatisch mit dem stärksten bekannten
WLAN.

_Hinweis:_ Eine detaillierte Beschreibung der einzelnen Schritte ist in dem Dokument
"Konfiguration der WLAN Einträge" enthalten.

## Spielernamen setzen

Die Spielernamen können über API-Web-Anwendung (`http://<ipadresse scrabscrap>:5050/`)
gesetzt werden. Die Spielernamen in die Eingabefelder eintragen und über `Submit` abspeichern.
Hierbei sollte möglichst auf Umlaute und Leerzeichen verzichtet werden.

Die Einstellung kann auch während des Spieles vorgenommen werden und wird dann beim
nächsten Zug aktiv.

## Beleuchtung des Spielbrettes

Das Spielbrett sollte möglichst indirekt beleuchtet werden, um eine Schattenbildung zu vermeiden.
Die Qualität der Ausleuchtung kann mit der API-Web-Anwendung (`http://<ipadresse scrabscrap>:5050/`)
im Menüpunkt `Camera` geprüft werden.

## Kamera justieren

Das Justieren der Kamera erfolgt über die API-Web-Anwendung (`http://<ipadresse scrabscrap>:5050/`).
Hier den Menüpunkt `Camera` aufrufen. Dann wird ein aktuelles Bild mit überlagertem Gitter angezeigt.
Sofern dies bereits passend ist, sind keine weiteren Aktionen nötig.

Falls das Bild nicht passend erkannt wird, den Menüpunkt `Clear Warp` auswählen. Damit wird die Warp
Einstellung gelöscht und das Spielbrett wird bei jeder Bild-Aufnahme dynamisch ermittelt. Soll ein
neuer Warp-Wert gespeichert werden, einfach erneut in das Menü `Camera` wechseln. Ist die Erkennung
jetzt korrekt, können mit `Store Warp` die Koordinaten wieder gespeichert werden. Dies kann durchaus
auch während eines Spieles gemacht werden, wenn z.B. ein Spieler versehentlich gegen die Kamera gestoßen
ist, und damit eventuell die Justierung verschoben hat.

Wird das Spielfeld auf nach mehreren Versuchen nicht korrekt erkannt, kann auf dem unteren Bild mit der
Maus in die Spielfeldecken (einzeln) geklickt werden, dann werden die Koordinaten für den Warp verwendet.

Ist die Kamera nicht korrekt ausgerichtet, kann in dem unteren Bild der Ausschnitt der Kamera geprüft
werden. Hier sollte am Ende ein ca. 2 cm weißer Rand um das Spielfeld herum eingestellt werden. Nach
Korrektur des Kamera-Armes den `Reload` Button drücken, damit das Bild neu aufgebaut wird.

## Settings

Die Settings der Anwendung werden über die INI-Datei `scrabble.ini` und `ftp-secret.ini` konfiguriert.
In der Datei `scrabble.ini` sind die Default-Werte in den einzelnen Sektionen unter dem Schlüssel
`defaults` aufgeführt. Es müssen nur die geänderten Werte abgespeichert werden.

Bei einem bereits gestartetem System können Änderungen über die Web-Oberfläche der
API-Schnittstelle vorgenommen werden. Hierzu einfach die URL `http://<ipadresse>:5050`
aufrufen. Einige Funktionen sind nur möglich, wenn sich die Anwendung entweder im Modus
`Start` oder `Pause` befindet.

## Settings für den Test- / Einführungs- / Produktions-Betrieb

Für den Test-Betrieb empfiehlt sich die erweiterte Ausgabe von Log-Informationen. Diese Einstellungen erzeugen
aber Einschränkungen in der Performance.

* in der Web-App: Settings => "development.recording=True"
* in der Web-App: Logs => Settings => "Set Loglevel" => (*) Debug
* scrabble.ini

  ```text
  [development]
  recording = True
  ```

* log.conf:

  ```text
  [logger_root]
  level = DEBUG
  ...
  ```

Beim Einführungs-Betrieb sollten folgende Einstellungen verwendet werden. Hier sind nur geringe Einschränkungen
in der Performane zu erwarten.

* in der Web-App: Settings => "development.recording=False"
* in der Web-App: Logs => Settings => "Set Loglevel" => (*) debug
* scrabble.ini

  ```text
  [development]
  recording = False
  ```

* log.conf

  ```text
  [logger_root]
  level = DEBUG
  ...
  ```

Im Produktionsbetrieb sollte das Logging auf ein Minimum beschränkt werden, damit die höchste Performance
erreicht werden kann.

* in der Web-App: Settings => "development.recording=False"
* in der Web-App: Logs => Settings => "Set Loglevel" => (*) info
* scrabble.ini

  ```text
  [development]
  recording = False
  ```

* log.conf:

  ```text
  [logger_root]
  level = INFO
  ...
  ```

Der vollständige Verzicht auf Logging ist nicht empfohlen. Hier werden weder Informationen noch Warnungen ins das
Log geschrieben.

* in der Web-App: Settings => "development.recording=False"
* in der Web-App: Logs => Settings => "Set Loglevel"  => (*) error
* scrabble.ini

  ```text
  [development]
  recording = False
  ```

* log.conf:

  ```text
  [logger_root]
  level = ERROR
  ...
  ```

## Test der Hardware

Wenn `scrabscrap` gestartet ist, kann über die API-Web-Anwendung ein Test der LEDs und der Displays
ausgelöst werden. Hierzu einfach die URL `http://<ipadresse>:5050` aufrufen und dann den Menü-Punkt
`Test` auswählen.

Durch den Aufruf der LED Tests werden verschiedene Modi der LEDs angezeigt (Ein/Aus/Blinken).
Es wird folgndes Muster verwendet

1. Grün, Gelb, Rot leuchten
2. Grün, Gelb, Rot blinken
3. Grün leuchtet
4. Gelb leuchtet
5. Rot leuchtet
6. Grün blinkt
7. Gelb blinkt
8. Rot blinkt

Beim Display-Test werden folgende Anzeigen getestet

1. Boot Anzeige
2. Kamera Fehler
3. FTP Fehler
4. "Ready" Anzeige
5. Abschalten der Anzeige

Das Spiel kann trotz ausgeschaltetem Display begonnen werden. Es kann über die (erneute) Eingabe der
Spielernamen die Anzeige wieder auf den Ausgangszustand versetzt werden.

## Erweiterung von ScrabScrap

### Abweichende Steine benutzen

Soll ein abweichender Satz an Scrabble-Steinen verwendet werden, müssen diese in einem geeigneten Format
als Bilder zur Verfügung stehen. Schwarzer Hintergrund mit weißem Text. Die Steingröße muss dabei im
gleichen Verhältnis wie das Spielfeld skaliert werden (Zielspielfeldgröße: 800x800 px). Es ist
möglich nur einen Ausschnitt des Steines zu speichern, dabei muss allerdings das Größenverhältnis
erhalten bleiben.

Bei sehr ähnlichen Steinen empfiehlt es sich, den Buchstabenwert im Bild des Steines zu erhalten (z.B.
bei A und Ä führt der abweichende Buchstabenwert zu einer verbesserten Erkennung).

Der Pfad auf die Steine kann in der Konfigurationsdatei "scrabble.ini" angepasst werden. Der Vorgabewert
für diesen Pfad ist `<python-src-dir>/game_board/img/default/`.

Werden abweichende Farben genutzt, ist u.U. eine Erweiterung der Methode `filter_image` vorzunehmen,
damit die Steine auf dem Brett korrekt erkannt werden können.

### Unterstützung weiterer Sprachen

Es können grundsätzlich unterschiedliche Sprachen unterstützt werden. Hierzu müssen die Anzahl der Steine
für die jeweiligen Buchstaben und deren Scoring-Werte konfiguriert werden.

Diese Einstellung wird in der `scrabble.ini` vorgenommen. Beispiele für die Sprachen `en` und `fr`
sind hier bereits enthalten. Üblicherweise muss hierzu auch ein passendes Set an Steinen verwendet werden.

### Unterstützung weiterer Spielbretter

Eine Unterstützung weiterer Spielbretter geht mit einer Anpassung der Software einher. Hierzu müssen die
Methoden `warp` und `filter_image` implementiert werden.

`warp` sorgt für ein korrekt rotiertes, skaliertes und normiertes Bild des Spielbrettes. Als Ergebnis muss
hier eine Bildgröße von 800x800px mit einem 25px Rand zu dem eigentlichen Spielfeld erzeugt werden. Damit
ist das Gitter des Spielfeldes auf 750x750px normiert.

`filter_image` dient zur Prüfung, welche Felder auf dem Spielbrett durch Steine belegt sind, um den
Erkennungprozess der Buchstaben zu optimieren. Algorithmisch werden ausgehend vom Zentrum die jeweiligen
Nachbarfelder geprüft bis keine weiteren gelegten Steine mehr erkannt werden.

## Development

### Nutzung von GitPod

Die Konfiguration zur Nutzung von VSCode innerhalb von GitPod ist bereits vorgesehen. Um dies
zu verwenden einfach auf den folgenden Button drücken, dann wird eine entsprechende Umgebung
gestartet:

[Open in Gitpod](https://gitpod.io/#https://github.com/scrabscrap/scrabble-scraper-v2)

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

Das Repository kann nun in das Zielverzeichnis gecloned werden.

```bash
cd <zielordner>
git clone https://github.com/scrabscrap/scrabble-scraper-v2.git
```

Danach wird mittels Python die virtuelle Umgebung einrichtet.

```bash
cd ~/scrabble-scraper-v2/python
python3 -m venv .venv --prompt cv
source ~/scrabble-scraper-v2/python/.venv/bin/activate
```

Im Anschluss können die Python Bibliotheken installiert werden.

```bash
cd scrabble-scraper-v2/python
source .venv/bin/activate
pip install -U pip setuptools wheel
pip install --force-reinstall -r requirements.txt --only-binary=:all:
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

installiert werden. Beim Aufruf des Remote-Rechners (RPI) werden dann zusätzliche
Hilfsmittel installiert. Danach kann von dem lokalen Rechner über ssh die Entwicklung
auf dem RPI durchgeführt werden.

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

_Hinweis:_ auf GitHub sind Workflows konfiguriert, die eine Prüfung mittels

* flake8
* pylint
* mypy
* coverage

vornehmen. Die Konfiguration von etwaigen Ausnahmen sind im Source-Code bzw. in den
jweiligen Konfigurationsdateien hinterlegt.

### Einstellung .alias

Es bietet sich an, folgende Alias-Einträge anzulegen.

```bash
alias ll='ls -al'
alias ..='cd ..'
alias ...='cd ../..'
alias cd..='cd ..'
alias workon='f(){ source ~/scrabble-scraper-v2/python/.venv/bin/activate; }; f'
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

installiert sein. Bei der Nutzung von GitPod sind diese Pakete bereits installiert und konfiguriert.

Um die Dokumentation zu erzeugen in dem Verzeichnis `docs` das Script `make_pdf.sh` aufrufen. Es wird
ein Order `pdf` angelegt, in dem die generierten Dokumente abgelegt werden.

## Start der Python Anwendungen

### Raspberry PI

Auf dem Raspberry PI kann die Anwendung wie folgt gestartet werden. Zuvor sollten die Default-Dateien
`scrabble.ini, log.conf, ftp-secret.ini` vom Ordner `defaults` in den Ordner `python/work` kopiert werden
und ggf. angepasst werden. Es muss vor dem Aufruf das venv Profil `cv` aktiviert werden.

```bash
cd python
# ggf. workon cv
python src/scrabscrap.py
```

Die API zum Einstellen von Parametern steht danach unter

* `http://localhost:5050`

zur Verfügung.

Sollte ein Zugriff über `localhost`nicht funktionieren, bitte statt `localhost` die IPv4 Adresse des
Rechners verwenden.

Alternativ kann auf dem RPI die Anwendung auch über `scripts/scrabscrap.sh` gestartet werden.

_Hinweis:_ ScrabScrap wird in diesem Fall als Hintergrund-Prozess gestartet.

### MacOS / GitPod

Hier kann die Hardware des Raspberry PI nicht genutzt werden, daher muss eine Simulation erfolgen.

Zum Start des Simulators folgenden Aufruf verwenden. Zuvor sollten die Default-Dateien
`scrabble.ini, log.conf, ftp-secret.ini` vom Ordner `defaults` in den Ordner `python/work` kopiert werden
und ggf. angepasst werden. Unter GitPod wird dieser Kopiervorgang beim Starten automatisch durchgeführt.
Es muss vor dem Aufruf das venv Profil `cv` aktiviert werden.

```bash
cd python
python simulator/simulator.py
```

Die simulierte Anwendung kann dann im lokalen Browser über

* `http://localhost:5050/simulator`

aufgerufen werden.

Sollte ein Zugriff über `localhost` nicht funktionieren, bitte statt `localhost` die IPv4 Adresse des
Rechners verwenden.

### Code-Coverage der Tests

```bash
cd python
cp -n defaults/* work/
coverage run -m unittest discover
```

Falls eine HTML Ausgabe erzeugt werden soll:

```bash
coverage html
```

### Performance-Analyse

Hier am Beispiel test_scrabble_game.py.

```bash
cd python
cp -n defaults/* work/
python -m cProfile -o test_scrabble_game.prof test/test_scrabble_game.py
```

Die Anzeige der Profiling-Informationen kann dann mit snakeviz erfolgen.

```bash
snakeviz test_scrabble_game.prof
```

## Start der Web-Anwendung

Damit in der Web-Anwendung die Daten der Python-Anwendung angezeigt werden, muss ein symbolischer
Link angelegt werden:

```bash
cd react/public
ln -s ../../python/work/web web
```

_Hinweis:_ Bei der Verwendung von GitPod wird dieser Link automatisch beim Start angelegt.

_Hinweis:_ In diesem Modus muss __kein__ Upload an den FTP-Server erfolgen (d.h. der Upload kann in der
Konfiguration über `output.ftp=False` deaktiviert werden).

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

## Fehlerbehebung / bekannte Probleme

### Reboot

_Hinweis:_ nach einem Reboot immer vor dem Spielbeginn prüfen, ob eine korrekte Netzverbindung
besteht (z.B. durch Aufruf der Web-Oberfläche).

Nach einem Reboot kann es vorkommen, dass keine korrekte Netzwerkverbindung aufgebaut wird.
In diesem Fall muss ScrabScrap aus- und wieder eingeschaltet werden.

### Es wird kein FTP Upload gemacht

Folgende Konfigurationen sind zu prüfen

* `scrabble.ini` ist FTP Output konfiguriert (setting: `output.ftp = True`)
* `ftp-secret.ini` hier die Einträge prüfen
  * ftp-server
  * ftp-user
  * ftp-password
* sofern die Web-App erreichbar ist kann über den Menüpunkt `Tests -> FTP` ein Upload getestet werden
