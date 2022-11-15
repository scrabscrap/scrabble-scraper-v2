# ScrabScrap

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://github.com/codespaces/new?hide_repo_select=true&ref=main&repo=504629544)

[![Open in Gitpod](https://gitpod.io/button/open-in-gitpod.svg)](https://gitpod.io/#https://github.com/scrabscrap/scrabble-scraper-v2)

Die Idee zum Scrabble Scraper ist vor einem Scrabble Turnier in Hamburg
2019 entstanden.  Da viele Partien parallel gespielt werden, ist es
nicht einfach, in den Spielverlauf paralleler Partien nachträglich
hineinzufinden.

Ziel diese Projekts ist, mit einer Kamera das Spielfeld beobachten und
die gelegten Buchstaben erkennen. Dabei werden die Punkte der einzelnen
Züge ermittelt. Das Ergebnis wird dann per API oder in einer Web-Anwendung
zur Verfügung gestellt.

Als Basis wird ein Raspberry PI 3 verwendet, da hier recht viel
Bastelmaterial zur Verfügung steht und die Kosten für Anschaffung sich
in Grenzen hält. Ziel war, mit der Hardware möglichst unter 100,-- €
zu bleiben.

Die Nutzung vom Raspberry PI 3 führte im Laufe des Projektes
allerdings zu vielen Optimierungen, da die Performance (gerade für
Bildverarbeitung) nicht gerade üppig ist. Sofern leistungsstärkere
Hardware verwendet wird, kann die Erkennungsrate insbesondere bei
Störungen (eine Hand ist im Bild) vermutlich deutlich gesteigert
werden.

Die Version 2 ist in der verwendeten Hardware inkompatibel zur Version 1,
daher wird dies als separates Projekt geführt. Es sind zudem Änderungen
im Threading, der API, der Zustandverwaltung und des Workflows enhalten.

---

*Disclaimer:* das Projekt ist kein offizielles Projekt von J.W. Spear &
Sons Limited, Mattel oder Scrabble Deutschland.

SCRABBLE® is a registered trademark of J.W. Spear & Sons Limited

---

Wer mehr über Scrabble erfahren möchte, kann als Einstiegspunkt
[Wikipedia: Scrabble](https://de.wikipedia.org/wiki/Scrabble)
nutzen.

Vielen Dank für die Unterstützung an
[Scrabble Deutschland eV](http://scrabble-info.de/) für die Tests,
Beratung und Diskussion bei der Umsetzung. Die Beispiele von den Partien
sind dabei auf verschiedenen Scrabble-Turnieren entstanden.

## Lizenz

 This program is free software: you can redistribute it and/or modify  
 it under the terms of the GNU General Public License as published by  
 the Free Software Foundation, version 3.

 This program is distributed in the hope that it will be useful, but
 WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
 General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program. If not, see <http://www.gnu.org/licenses/>.
