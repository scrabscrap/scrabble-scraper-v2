# FAQ

## Einrichten der WLAN Verbindung

## Kamera justieren

## Spielernamen setzen

## Beleuchtung des Spielbrettes

## Erweiterung von ScrabScrap

### Abweichende Steine benutzen

### Unterstützung weiterer Sprachen

### Unterstützung weiterer Spielbretter

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
