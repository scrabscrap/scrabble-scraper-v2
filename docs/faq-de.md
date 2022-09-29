# FAQ

## Einrichten der WLAN Verbindung

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

## Spielernamen setzen

Die Spielernamen können über API-Web-Anwendung (`http://<ipadresse scrabscrap>:5000/`) gesetzt werden. Die Spielernamen
in die Eingabefelder eintragen und über `Submit` abspeichern. Hierbei sollte möglichst auf Umlaute und Leerzeichen
verzichtet werden.

Die Einstellung kann auch während des Spieles vorgenommen werden und wird dann beim nächsten Zug aktiv.

## Beleuchtung des Spielbrettes

Das Spielbrett sollte möglichst indirekt beleuchtet werden, um eine Schattenbildung zu vermeiden. Die
Qualität der Ausleichtung kann mit der API-Web-Anwendung (`http://<ipadresse scrabscrap>:5000/`) im Menüpunkt `Camera`
geprüft werden.

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

## Test der Hardware

## Settings

## Erzeugung der Dokumentation

## Development

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

#### VS Code Erweiterungen

In VSCode sollten dann folgende Erweiterungen installiert werden.

* GitLens (GitKraken)
* markdownlint (David Anson)
* Python (Microsoft)

soll eine Remote-Entwicklung auf dem Raspberry PI erfolgen, dann müssen noch

* Remote SSH (Microsoft)
* Remote SSH: Editing Configuration Files (Microsoft)

installiert werden.

#### Einstellung .alias

Es bietet sich an, folgende Alias-Einträge anzulegen.

```text
alias workon='f() { source ~/.venv/$1/bin/activate };f'
alias python=python3
```

#### Einstellung .zshrc

Damit die Ausführung in VSCode von Python-Code auch im RUN-Modus funktioniert, in
der .zshrc folgendes ergänzen:

```bash
export PYTHONPATH=src:$PYTHONPATH
```

### Nutzung von GitPods

## Fehlerbehebung
