# FAQ

## Preparations

### After setting up

The following steps are recommended after setting up the system

1. Switch on the computer
2. If there are only unknown WiFis in the area, carry out "Setting up the WiFi connection"
3. Navigate to the ScrabScrap web application in the browser
4. Adjust the camera arm
5. Check settings / configuration (FTP connection, Scrabble board used, etc.)
6. If an FTP upload is used, make a "mini test game" and check whether an upload of the data takes place correctly

### Before each game

1. Check in the web application whether the playing field is still recognised correctly
2. Set player names

### After each match

1. Check whether the game has ended correctly (press the "End" button for longer than 3 seconds)
2. The yellow button flashes. The current game is compressed and uploaded to the server if necessary.
3. Press any button to start a new game.
4. "Name1" and "Name2" should appear in the display.

## Setting up the WiFi connection

If no valid WiFi connection can be established, ScrabScrap switches to AP mode and provides a
WiFI `ScrabScrap`. The default password is `scrabscrap` and should be changed the first time it is used.

After connecting to AP, you can search for a WiFi web application `http://10.0.0.1:5050`. To connect, you must
select the desired WiFi and enter the PSK.

After a reboot, `ScrabScrap` automatically connects to the strongest known WiFi.

_Note:_ A detailed description of the individual steps can be found in the document
"Configuration of the WiFi entries".

## Set player names

The player names can be set via API web application (`http://<ipaddress scrabscrap>:5050/`)
can be set. Enter the player names in the input fields and save them via `Submit`.
If possible, avoid umlauts and spaces.

The setting can also be made during the game and is then activated during the next turn.

## Illumination of the board

The board should be illuminated indirectly to avoid shadows.
The quality of the illumination can be checked with the API web application (`http://<ipaddress scrabscrap>:5050/`)
in the menu item `Camera`.

## Adjusting the camera

The camera can be adjusted via the API web application (`http://<ip address scrabscrap>:5050/`).
Call up the menu item `Camera` here. Then a current picture with superimposed grid is displayed.
If this is already suitable, no further action is necessary.

If the image is not recognised as suitable, select the menu item `Clear Warp`. This clears the warp
setting and the board is determined dynamically with each image capture. If a new
new warp value is to be saved, simply switch back to the `Camera` menu. If the detection
is now correct, the coordinates can be saved again with `Store Warp`. This can also be done
during a game, e.g. if a player has accidentally bumped into the camera, which may have shifted
the adjustment.

If the playing field is not recognised correctly after several attempts, you can move the mouse
into the corners of the playing field (one at a time) on the lower picture.
If the field is not recognised correctly after several attempts, you can click with the mouse in
the corners of the field (one at a time) on the lower picture, then the coordinates will be used
for the warp.

If the camera is not correctly aligned, the section of the camera can be checked in the lower picture.
Here, an approx. 2 cm white border around the playing field should be set at the end. After
correction of the camera arm, press the `Reload` button so that the picture is rebuilt.

## Settings

The settings of the application are configured via the INI file `scrabble.ini` and `ftp-secret.ini`.
In the file `scrabble.ini` the default values in the individual sections are listed under the key
`defaults`. Only the changed values need to be saved.

If the system has already been started, changes can be made via the web interface of the
API interface. To do this, simply call up the URL `http://<ipaddress>:5050`.
to do this. Some functions are only possible if the application is either in the mode
`Start` or `Pause` mode.

## Settings for test / introductory / production operation

For test operation, the extended output of log information is recommended. These settings has
restrictions in the performance of ScrabScrap.

* in the web app: Settings => "development.recording=True"
* in the web app: Logs => Settings => "Set Loglevel" => (*) Debug
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

The following settings should be used for introductory operation. Only minor restrictions in
performance are to be expected.

* web app: Settings => "development.recording=False".
* web app: Logs => Settings => "Set Loglevel" => (*) debug
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

In production operation, logging should be kept to a minimum so that the highest performance can be achieved.

* web app: Settings => "development.recording=False"
* web app: Logs => Settings => "Set Loglevel" => (*) info
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

Completely switching off logging is not recommended. In this case, neither information nor
warnings are written to the log.

* web app: Settings => "development.recording=False".
* web app: Logs => Settings => "Set Loglevel" => (*) error
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

## Test the hardware

When `scrabscrap` has been started, a test of the LEDs and the displays can be
can be triggered. To do this, simply call up the URL `http://<ipaddress>:5050` and then select
the menu item `Test` menu item.

By calling up the LED tests, different modes of the LEDs are displayed (on/off/flashing).
The following pattern is used

1. green, yellow, red light
2. green, yellow, red flashing
3. green lights
4. yellow lights
5. red lights
6. green flashes
7. yellow flashes
8. red flashes

The following displays are tested during the display test

1. boot display
2. camera error
3. FTP error
4. "Ready" display
5. switching off the display

The game can be started even though the display is switched off. The display can be reset by
(re)entering the player names.

## Extension of ScrabScrap

### Using different playing pieces

If a different set of Scrabble pieces is to be used, these must be available as images in a suitable format.
available as pictures. Black background with white text. The size of the pieces must be
scaled in the same proportion as the playing field (target playing field size: 800x800 px). It is
possible to save only a section of the piece, but the size ratio must be maintained.
must be preserved.

In the case of very similar pieces, it is recommended to keep the letter value in the image of the piece (e.g.
for A and Ä, the deviating letter value leads to improved recognition).

The path to the pieces can be adjusted in the configuration file `scrabble.ini`. The default value
for this path is `<python-src-dir>/game_board/img/default/`.

If different colours are used, it may be necessary to extend the `filter_image` method,
so that the pieces on the board can be recognised correctly.

### Support of other languages

Basically, different languages can be supported. For this, the number of pieces
for the respective letters and their scoring values must be configured.

This setting is made in the `scrabble.ini`. Examples for the languages 'en' and 'fr' are already included here.
Usually, a suitable set of pieces must also be used for this.

### Support of further game boards

Supporting further game boards is accompanied by an adaptation of the software. To do this, the
methods `warp` and `filter_image` must be implemented.

`warp` ensures a correctly rotated, scaled and normalised image of the board. As a result
an image size of 800x800px with a 25px border to the actual board must be created. With this
the grid of the board is normalised to 750x750px.

`filter_image` is used to check which fields on the board are occupied by stones in order to optimise the recognition
process of the letters. Algorithmically, starting from the centre, the respective neighbouring squares are checked
until no more placed stones are recognised.

## Development

### Use of GitPod

The configuration for using VSCode within GitPod is already provided. To use this
simply click on the following button, then a corresponding environment will be started:

[Open in Gitpod](https://gitpod.io/#https://github.com/scrabscrap/scrabble-scraper-v2)

### Setting up a development system under Mac OS

Install the necessary tools via [Homebrew](https://brew.sh/index_de).

```bash
brew install git
brew install node
brew install python@3.11
brew install visual-studio-code --cask
```

Now set up Git identifiers if necessary.

```bash
git config --global user.name "..."
git config --global user.email "..."
```

The repository can now be cloned into the target directory.

```bash
cd <destination folder>
git clone https://github.com/scrabscrap/scrabble-scraper-v2.git
```

Then set up the virtual environment using Python.

```bash
cd ~/scrabble-scraper-v2/python
python3 -m venv .venv --prompt cv
source ~/scrabble-scraper-v2/python/.venv/bin/activate
```

Now the Python libraries can be installed.

```bash
cd scrabble-scraper-v2/python
source .venv/bin/activate
pip install -U pip setuptools wheel
pip install -U -r requirements.txt
```

Libraries that do not run under MacOS are omitted from the "requirements.txt".

After that, the project can already be started with VSCode of the workspace
`scrabble-scrapber-v2.code-workspace` can be opened. In VSCode
must then be selected as Python interpreter ('cv', venv).

The following directories are created as workspace folders

* Python
* Web-App
* Documentation
* Scripts

### Access via an ssh key

(local computer)

```bash
cd ~/.ssh

# create the scrabsrap ssh-key
ssh-keygen -f ~/.ssh/scrabscrap -t ecdsa

# copy on the RPI ! user@host ! customise
ssh-copy-id -i ~/.ssh/scrabscrap user@host
```

For the local machine, configure a different ssh-key for the host ``scrabscrap``.

```bash
nano ~/.shh/config 
```

add the following entries

```text
Host scrabscrap
  HostName scrabscrap
  User <username>
  IdentityFile ~/.ssh/scrabscrap
```

### VS Code extensions

The following extensions should then be installed in VSCode.

* GitLens (GitKraken)
* GitGraph (mhutchie)
* Markdown Preview Enhanced (Yiyi Wang)
* Python (Microsoft)
* Pylance (Microsoft)
* Ruff (Astral Software)

If remote development is to take place on the Raspberry PI, the following

* Remote SSH (Microsoft)
* Remote SSH: Editing Configuration Files (Microsoft)

must be installed. When the remote computer (RPI) is called up, additional
tools are installed. Afterwards, development can be carried out on the RPI from the local computer via ssh.

After starting the ssh connection, the workspace `~/scrabble-scraper-v2/scrabble-scraper-v2.code-workspace` can be opened.

### Lint and format

```bash
pip install flake8 autopep8

```

Parameters flake8

```json
    "python.linting.flake8Args": [
        "--max-line-length=128",
        "--ignore=E402"
      ],

```

Parameters autopep8

```json
    "python.formatting.autopep8Args": [
        "--max-line-length=128",
        "--ignore=E402"
      ],
```

_Note:_ there are workflows configured on GitHub that can perform a check using.

* flake8
* pylint
* mypy
* coverage

are already configured on GitHub. The configuration of any exceptions are stored in the source code or in the
configuration files.

### Setting .alias

It is advisable to create the following alias entries.

```bash
alias ll='ls -al'
alias ..='cd ..'
alias ...='cd ../..'
alias cd ..='cd ..'
alias workon='f(){ source ~/.venv/$1/bin/activate; }; f'
```

#### Setting .zshrc

In order for the execution of Python code in VSCode to work in RUN mode, the following has to be added to .zshrc:

```bash
export PYTHONPATH=src:$PYTHONPATH
```

## Creating the documentation

In order for the documentation to be generated in the form of PDF files

* pandoc
* texlive

must be installed on the system. When using GitPod, these packages are already installed and configured.

To create the documentation, call the script `make_pdf.sh` in the directory `docs`. It will
a folder `pdf` will be created in which the generated documents will be stored.

## Start the Python applications

### Raspberry PI

On the Raspberry PI, the application can be started as follows. Beforehand, the default files
`scrabble.ini`, `log.conf`, `ftp-secret.ini` should be copied from the folder `defaults` to the folder `python/work`
and adapted if necessary. The venv profile`cv` must be activated before the call.

```bash
cd python

# workon cv if necessary
python src/scrabscrap.py

```

The API for setting parameters is then available at

* `http://localhost:5050`

If access via `localhost` does not work, please use the IPv4 address of the computer instead of `localhost`.

Alternatively, the application can be started on the RPI via `scripts/scrabscrap.sh`.

_Note:_ ScrabScrap is started as a background process in this case.

### MacOS / GitPod

The hardware of the Raspberry PI cannot be used here, so a simulation must be made.

Use the following call to start the simulator. Beforehand, the default files
`scrabble.ini`, `log.conf`, `ftp-secret.ini` should be copied from the folder `defaults` into the folder `python/work`.
and adjusted if necessary. Under GitPod, this copying process is carried out automatically at start-up.
The venv profile `cv` must be activated before the call.

```bash
cd python
python simulator/simulator.py
```

The simulated application can then be viewed in the local browser via

* `http://localhost:5050/simulator`

If access via `localhost` does not work, please use the IPv4 address of the computer instead of `localhost`.
address of the computer instead of `localhost`.

### Code coverage of the tests

```bash
cd python
cp -n defaults/* work/
coverage run -m unittest discover
```

If you want to generate HTML output:

```bash
coverage html
```

### Performance analysis

Here at the example test_scrabble_game.py.

```bash
cd python
cp -n defaults/* work/
python -m cProfile -o test_scrabble_game.prof test/test_scrabble_game.py
```

The display of profiling information can then be done with snakeviz.

```bash
snakeviz test_scrabble_game.prof
```

## Start the web application

In order to display the data of the Python application in the web application, a symbolic link must be created.
symbolic link must be created:

```bash
cd react/public
ln -s ../../python/work/web web
```

_Note:_ When using GitPod, this link is automatically created at startup.

_Note:_ In this mode, there is __no__ need to upload to the FTP server (i.e. the upload can be done in the
configuration via `output.ftp=False`).

This means that the data generated in the Python application is then available locally.

The initialisation of the node_modules is done with:

```bash
cd react
npm install
```

The web application is then started with

```bash
cd react
npm start
```

The web application can then be opened in the local browser under

* `http://localhost:5173`

can be called.

## Troubleshooting / known problems

### Reboot

After a reboot, always check whether there is a correct network connection before starting the game
(e.g. by calling up the web interface).

After a reboot, it can happen that no correct network connection is established.
In this case, ScrabScrap must be switched off and on again.

### There is no FTP upload

Check the following configurations

* `scrabble.ini` is configured FTP output (setting: `output.ftp = True`)
* `ftp-secret.ini` check the entries here
  * ftp-server
  * ftp-user
  * ftp-password
* If the web app is accessible, an upload can be tested via the menu item 'Tests -> FTP'.
