# ScrabScrap

[![Open in GitHub Codespaces](https://img.shields.io/badge/Open_in_GitHub_Codespaces-blue?logo=github)](https://codespaces.new/scrabscrap/scrabble-scraper-v2?quickstart=1) &emsp; [![Open in Gitpod](https://img.shields.io/badge/Open_in_Gitpod-blue?logo=gitpod)](https://gitpod.io/#https://github.com/scrabscrap/scrabble-scraper-v2)

Verwenden Sie zum Browsen oder Entwickeln den mitgelieferten Arbeitsbereich `scrabble-scraper-v2.code-workspace`.

Use the supplied `scrabble-scraper-v2.code-workspace` workspace for browsing or developing.


## Über

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

## About

The idea for the Scrabble Scraper came up before a Scrabble tournament in Hamburg in 2019. Since many games are played in parallel, it is not easy to subsequently find the course of play in parallel games.

The aim of this project is to observe the playing field with a camera and to recognise the letters that have been laid. In the process, the points of the individual moves are determined. The result is then made available via API or in a web application.

A Raspberry PI 3 is used as the basis, as there is quite a lot of tinkering material available here and the costs for purchasing it are kept within limits. The aim was to keep the hardware under €100 if possible.

However, the use of the Raspberry PI 3 led to many optimisations during the course of the project, as the performance (especially for image processing) is weak. If more powerful hardware is used, the recognition rate can probably be increased significantly, especially in the case of disturbances (a hand is in the picture).

Version 2 is incompatible with version 1 in the hardware used, so this is kept as a separate project. There are also changes in the threading, the API, the state management and the workflow.

---

Disclaimer: the project is not an official project of J.W. Spear & Sons Limited, Mattel or Scrabble Germany.

SCRABBLE® is a registered trademark of J.W. Spear & Sons Limited

---

If you want to know more about Scrabble, you can use [Wikipedia: Scrabble](https://de.wikipedia.org/wiki/Scrabble) as a starting point.

Many thanks for the support to [Scrabble Deutschland eV](http://scrabble-info.de/) for the tests, advice and discussion during the implementation. Most of the examples were created at various Scrabble tournaments.

## Lizenz / license

 This program is free software: you can redistribute it and/or modify  
 it under the terms of the GNU General Public License as published by  
 the Free Software Foundation, version 3.

 This program is distributed in the hope that it will be useful, but
 WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
 General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program. If not, see <http://www.gnu.org/licenses/>.
