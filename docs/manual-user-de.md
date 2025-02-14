## ScrabScrap - Spieler 1 (Grün)

### Spielzug

|                                       |                                          |
|---------------------------------------|------------------------------------------|
| ![Zug legen](images/tiles-remove.png) | ![Grüner Button](images/press-green.png) |
| Zug legen                             | Button Grün                              |

### Pause

|                                           |                                           |
|-------------------------------------------|-------------------------------------------|
| ![Gelber Button](images/press-yellow.png) | ![Gelber Button](images/press-yellow.png) |
| Button Gelb                               | Button Gelb                               |
| Pause                                     | Spiel fortsetzen                          |

### Anzweifeln (ich habe Recht)

|                                           |                                                 |                                           |
|-------------------------------------------|-------------------------------------------------|-------------------------------------------|
| ![Gelber Button](images/press-yellow.png) | ![Grüner Taster](images/press-green-switch.png) | ![Gelber Button](images/press-yellow.png) |
| Button Gelb                               | **Taster** Grün \*                              | Button Gelb                               |
| Pause                                     | Im Display von Rot: Zug Entf.                   | Spiel fortsetzen                          |

> \* falls ein Anzweifeln nicht mehr möglich ist, wird im Display Grün "Timeout" angezeigt

### Anzweifeln (ich habe Unrecht)

|                                           |                                              |                                           |
|-------------------------------------------|----------------------------------------------|-------------------------------------------|
| ![Gelber Button](images/press-yellow.png) | ![Roter Taster](images/press-red-switch.png) | ![Gelber Button](images/press-yellow.png) |
| Button Gelb                               | **Taster** Rot \*                            | Button Gelb                               |
| Pause                                     | Im Display von Grün: -10 Pkt.                | Spiel fortsetzen                          |

> \* falls ein Anzweifeln nicht mehr möglich ist, wird im Display Grün "Timeout" angezeigt

### Ich habe nach dem Zug meinen Spiel-Button nicht betätigt

1. Gelber Button: Pause
2. Steine des Gegners vom Brett entfernen
3. Gelber Button: Pause beenden
4. Grüner Button: Zug wird analysiert
5. Steine des Gegners (Rot) wieder auf das Brett legen
6. Roter Button: Zug des Gegners wird analysiert
7. Grün ist wieder am Zug

> Damit verliert der Spieler 1 (Grün) die Bedenkzeit des Gegners

<div style="display:none;page-break-after: always;">\pagebreak</div>

## ScrabScrap - Spieler 2 (Rot)

### Spielzug

|                                       |                                       |
|---------------------------------------|---------------------------------------|
| ![Zug legen](images/tiles-remove.png) | ![Roter Button](images/press-red.png) |
| Zug legen                             | Button Rot                            |

### Pause

|                                           |                                           |
|-------------------------------------------|-------------------------------------------|
| ![Gelber Button](images/press-yellow.png) | ![Gelber Button](images/press-yellow.png) |
| Button Gelb                               | Button Gelb                               |
| Pause                                     | Spiel fortsetzen                          |

### Anzweifeln (ich habe Recht)

|                                           |                                              |                                           |
|-------------------------------------------|----------------------------------------------|-------------------------------------------|
| ![Gelber Button](images/press-yellow.png) | ![Roter Taster](images/press-red-switch.png) | ![Gelber Button](images/press-yellow.png) |
| Button Gelb                               | **Taster** Rot \*                            | Button Gelb                               |
| Pause                                     | Im Display von Grün: Zug Entf                | Spiel fortsetzen                          |

> \* falls ein Anzweifeln nicht mehr möglich ist, wird im Display Rot "Timeout" angezeigt

### Anzweifeln (ich habe Unrecht)

|                                           |                                                 |                                           |
|-------------------------------------------|-------------------------------------------------|-------------------------------------------|
| ![Gelber Button](images/press-yellow.png) | ![Grüner Taster](images/press-green-switch.png) | ![Gelber Button](images/press-yellow.png) |
| Button Gelb                               | **Taster** Grün \*                              | Button Gelb                               |
| Pause                                     | Im Display von Rot: -10 Pkt.                    | Spiel fortsetzen                          |

> \* falls ein Anzweifeln nicht mehr möglich ist, wird im Display Rot "Timeout" angezeigt

### Ich habe nach dem Zug meinen Spiel-Button nicht betätigt

1. Gelber Button: Pause
2. Steine des Gegners vom Brett entfernen
3. Gelber Button: Pause beenden
4. Roter Button: Zug wird analysiert
5. Steine des Gegners (Grün) wieder auf das Brett legen
6. Grüner Button: Zug des Gegners wird analysiert
7. Rot ist wieder am Zug

> Damit verliert der Spieler 2 (Rot) die Bedenkzeit des Gegners

<div style="display:none;page-break-after: always;">\pagebreak</div>

# Start eines Spiels

## Vorbereitungen

Vor dem Spiel sollte die Kamera ausgerichtet werden. Wird diese Kameraposition
gespeichert, erhöht das die Stabilität der Bilderkennung, da nicht bei jedem
Aufruf das Spielfeld ermittelt werden muss. Dies kann durch den internen Web-Server
von ScrabScrap komfortabel im Browser eingestellt werden.

Falls gewünscht können in der Web-Anwendung zudem die Spielernamen und der Turniername
gesetzt werden.

Das Spiel kann begonnen werden, wenn beide Displays die jeweiligen
Spielernamen anzeigen.

### Grün soll beginnen

![Roter Button](images/press-red.png)  
Button Rot

### Rot soll beginnen

![Grüner Button](images/press-green.png)  
Button Grün

# Ende des Spiels

Zunächst sicherstellen, dass das Spiel pausiert ist. Also die gelbe LED leuchtet.
Um ein Spiel zu beenden und zu archivieren, muss der **Taster "End"** für mehr
als 3 Sekunden gedrückt werden. Es erscheint in den Displays der aktuelle Spielstand
un der gelbe Button blinkt.
Ein neues Spiel kann durch Drücken auf einen beliebigen Button gestartet werden. Es
erscheint dann "Name1" und "Name2" im Display.

_Hinweis:_ es kann einen Augenblick dauern, da hier zunächst das gesamte Spiel
inklusive aller Bilder in einer ZIP-Datei gespeichert wird. Diese wird dann
zusätzlich auf den Web-Server hochgeladen.

# Der Rechner reagiert nicht mehr

Falls der Rechner nicht mehr auf das Drücken der farbigen Schaltflächen
reagiert, oder die Displays über mehrere Züge keine korrekte Zeit mehr
anzeigen, ist vermutlich ein Software-Fehler aufgetreten.
In diesem Fall kann der gesamte Rechner durch Drücken des **Tasters "Boot"**
für mehr als 3 Sekunden neu gestartet werden.

_Hinweis:_ in diesem Fall gehen alle nicht gespeicherten Daten verloren und
das aktuelle Spiel kann nicht mehr fortgesetzt werden.

<div style="display:none;page-break-after: always;">\pagebreak</div>

# Quick-Reference - ScrabScrap

## Grundsätzliche Vorbemerkung

Die Anwendung beruht darauf, zu bestimmten Zeitpunkten ein Foto vom
Spielbrett aufzunehmen und dann zu analysieren. Damit dies möglichst
fehlerfrei funktioniert, müssen die Spieler darauf achten, das Brett
nicht zu verdecken, wenn der Button zum Auslösen des Spielzugs
gedrückt wird.

## Anzweifeln

Sofern ein Anzweifeln noch möglich ist, wird im Display des aktiven
Spielers "!?" angezeigt. Auf der rechten Seite des Displays wird zusätzlich
die Dauer des aktuellen Spielzugs in Sekunden angezeigt.

## Weitere Taster

Hinter den Buttons befinden sich fünf Taster.

* Grün/Rot: Taster für das Anzweifeln des Zugs  
  (einfaches Drücken)
* Gelb/Schwarz/Blau: Taster für Access Point, Ende des Spiels, Reboot
  (halten von mehr als 3s)

Die Funktion des Schalters ist jeweils beschriftet.

## Allgemeine Hinweise

Die Anwendung ist so konzipiert, dass sie auch im Fehlerfall
weiterläuft. Es werden nur die nicht funktionierenden Teile der
Anwendung deaktiviert. Das hat aber zur Folge, dass abhängige Teile
ebenfalls nicht mehr korrekt funktionieren. So kann natürlich keine
Berechnung des Brettes vorgenommen werden, wenn die Kamera keine
korrekten Bilder mehr aufnehmen kann.

<div style="display:none;page-break-after: always;">\pagebreak</div>

## Zustandsdiagramm

![Zustände](images/states.png)
