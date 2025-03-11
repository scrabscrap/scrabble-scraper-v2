# ScrabScrap

ScrabScrap is a Raspberry Pi-powered system designed to automatically track Scrabble scores and manage player timers using a camera and physical buttons. The system detects played tiles, calculates points and provides a scrabble-clock timer.

## Features
✅ **Automated Score Calculation** - Uses a camera to recognize placed Scrabble tiles and compute scores.  
✅ **Chess-Clock Timer** – Tracks each player's elapsed time.  
✅ **Physical Controls** – Players interact via hardware buttons connected to the Raspberry Pi's GPIO.  
✅ **Compact and Modular Build** – Mounted on a aluminum frame (ALU Profile 20x20) for stability.  
✅ **WiFi Connectivity** – Enables easy setup and remote access.  
✅ **Built with Python & React** – Runs seamlessly on a Raspberry Pi.

## Hardware Requirements
- **Raspberry Pi** (Recommended: Raspberry Pi 3b)
- **Camera Module** (for tile detection)
- **Physical Buttons** (for player interactions)
- **Display Module** (to show scores and timers)
- **Aluminum Frame (20x20 ALU Profile)** (for mounting)

see: [Hardware Setup](https://github.com/scrabscrap/scrabble-scraper-v2/wiki/Hardware-Setup)


## Installation
1. **Set up the Raspberry Pi** – Install Raspberry Pi OS and dependencies.  
2. **Clone the Repository**:  
   ```bash
   git clone https://github.com/scrabscrap/scrabble-scraper-v2.git
   cd scrabble-scraper-v2
   ```
3. **Install Dependencies**:  
   ```bash
   cd python
   pip install -r requirements.txt  # Backend
   cd ../react
   npm install  # Frontend
   npm run build
   ```
4. **Run the Application**:  
   ```bash
   cd ../scripts
   ./scrabscrap.sh
   ```

see: [Raspberry PI Installation](https://github.com/scrabscrap/scrabble-scraper-v2/wiki/Raspberry-Pi-Installation)

## Usage
1. Place the Scrabble board under the camera.
2. Press the button to start your turn.
3. The camera scans the board and calculates scores in real-time.
4. The display updates the points and player time.

see: [User manual](https://github.com/scrabscrap/scrabble-scraper-v2/blob/main/docs/manual-user-en.md)

## Wiki & Documentation
For detailed setup instructions, visit the [ScrabScrap Wiki](https://github.com/scrabscrap/scrabble-scraper-v2/wiki/Home).

## Developing Quick Start

[![Open in GitHub Codespaces](https://img.shields.io/badge/Open_in_GitHub_Codespaces-blue?logo=github)](https://codespaces.new/scrabscrap/scrabble-scraper-v2?quickstart=1) &emsp; [![Open in Gitpod](https://img.shields.io/badge/Open_in_Gitpod-blue?logo=gitpod)](https://gitpod.io/#https://github.com/scrabscrap/scrabble-scraper-v2)

Use the supplied `scrabble-scraper-v2.code-workspace` workspace for browsing and developing.

see: [Development](https://github.com/scrabscrap/scrabble-scraper-v2/wiki/Development)

## Contributing
Contributions are welcome! Feel free to submit issues or pull requests.

## License

 This program is free software: you can redistribute it and/or modify  
 it under the terms of the GNU General Public License as published by  
 the Free Software Foundation, version 3.

 This program is distributed in the hope that it will be useful, but
 WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
 General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program. If not, see <http://www.gnu.org/licenses/>.

---

Disclaimer: the project is not an official project of J.W. Spear & Sons Limited, Mattel or Scrabble Germany.

SCRABBLE® is a registered trademark of J.W. Spear & Sons Limited

---

If you want to know more about Scrabble, you can use [Wikipedia: Scrabble](https://de.wikipedia.org/wiki/Scrabble) as a starting point.

Many thanks for the support to [Scrabble Deutschland eV](http://scrabble-info.de/) for the tests, advice and discussion during the implementation. Most of the examples were created at various Scrabble tournaments.

---

🔗 **Project Repository** → [ScrabScrap on GitHub](https://github.com/scrabscrap/scrabble-scraper-v2)  
📫 **Report Issues** → [GitHub Issues](https://github.com/yscrabscrap/scrabble-scraper-v2/issues)  
