## ScrabScrap - Spieler 1 (Grün)

### Spielzug

![Zug legen](images/tiles-remove.png) (Zug legen)
![Grüner Button](images/press-green.png) (Grün)

### Pause

![Gelber Button](images/press-yellow.png) (Gelb)

### Anzweifeln (ich habe Recht)

![Gelber Button](images/press-yellow.png) (Gelb) ![Grüner Taster](images/press-green-switch.png) (Grüner **Taster**)  
Im Display von Rot wird angezeigt: Zug Entf.  

Das Spiel wird fortgesetzt mit  
![Gelber Button](images/press-yellow.png) (Gelb)

### Anzweifeln (ich habe Unrecht)

![Gelber Button](images/press-yellow.png) (Gelb) ![Roter Taster](images/press-red-switch.png) (Roter **Taster**)  
Im Display von Grün wird angezeigt: -10 Pkt.  

Das Spiel wird fortgesetzt mit  
![Gelber Button](images/press-yellow.png) (Gelb)

### Ich habe nach dem Zug meinen Spiel-Button nicht betätigt

Pause -> Steine des Gegners vom Brett entfernen -> Pause -> Grün -> Pause -> Steine des Gegners wieder auf das Brett legen -> Pause -> Rot -> Grün ist wieder am Zug

Damit verliert der Spieler 1 (Grün) die Bedenkzeit des Gegners

<div style="display:none;page-break-after: always;">\pagebreak</div>

## ScrabSrap - Spieler 2 (Rot)

### Spielzug

![Zug legen](images/tiles-remove.png) (Zug legen) ![Roter Button](images/press-red.png) (Rot)  
Die Spielzeit für Grün beginnt.

### Pause

![Gelber Button](images/press-yellow.png) (Gelb)  
Die Spielzeit für beide Spieler wird angehalten.

### Anzweifeln (ich habe Recht)

![Gelber Button](images/press-yellow.png) (Gelb) ![Roter Taster](images/press-red-switch.png) (Roter **Taster**)  
Im Display von Grün wird angezeigt: Zug Entf.  

Das Spiel wird fortgesetzt mit  
![Gelber Button](images/press-yellow.png) (Gelb)

### Anzweifeln (ich habe Unrecht)

![Gelber Button](images/press-yellow.png) (Gelb) ![Grüner Taster](images/press-green-switch.png) (Grüner **Taster**)  
Im Display von Grün wird angezeigt: -10 Pkt.  

Das Spiel wird fortgesetzt mit  
![Gelber Button](images/press-yellow.png) (Gelb)

### Ich habe nach dem Zug meinen Spiel-Button nicht betätigt

Pause -> Steine des Gegners vom Brett entfernen -> Pause -> Rot -> Pause -> Steine des Gegners wieder auf das Brett legen -> Pause -> Grün -> Rot ist wieder am Zug

Damit verliert der Spieler 2 (Rot) die Bedenkzeit des Gegners

<div style="display:none;page-break-after: always;">\pagebreak</div>

# Start eines Spiels

## Vorbereitungen

Vor dem Spiel sollte die Video-Kamera ausgerichtet werden. Dies kann
durch den internen Web-Server von ScrabScrap komfortabel im Browser
eingestellt werden.

Falls gewünscht können in der Web-Anwendung zudem die Spielernamen
gesetzt werden.

Das Spiel kann begonnen werden, wenn beide Displays "30:00" anzeigen.

### Grün soll beginnen

![Roter Button](images/press-red.png) (Rot)

### Rot soll beginnen

![Grüner Button](images/press-green.png) (Grün)

# Ende des Spiels

Zunächst sicherstellen, dass das Spiel pausiert ist. Also die gelbe LED blinkt.
Um ein Spiel zu beenden und zu archivieren, muss der **Taster "Reset"** für mehr als 3 Sekunden gedrückt werden. Es erscheint
in den Displays der Hinweis "Reset". Sobald die Daten des Spiels
gesichert sind, beginnt ein neues Spiel.

_Hinweis:_ es kann einen Augenblick dauern, da hier zunächst das gesamte Spiel
inklusive aller Bilder in einer ZIP-Datei gespeichert wird. Diese wird dann
zusätzlich auf den Web-Server hochgeladen.

# Der Rechner reagiert nicht mehr

Falls der Rechner nicht mehr auf das Drücken der farbigen Schaltflächen
reagiert, oder die Displays über mehrere Züge keine korrekte Zeit mehr
anzeigen, ist vermutlich ein Software-Fehler aufgetreten.
In diesem Fall kann der gesamte Rechner durch Drücken des **Tasters "Reboot"** für mehr als 3 Sekunden neu gestartet werden.

_Hinweis:_ in diesem Fall gehen alle nicht gespeicherten Daten verloren und
das aktuelle Spiel kann nicht mehr fortgesetzt werden.

<div style="display:none;page-break-after: always;">\pagebreak</div>

# Quick-Reference - ScrabScrap

## Grundsätzliche Vorbemerkung

Die Anwendung beruht darauf, zu bestimmten Zeitpunkten ein Foto vom
Spielbrett aufzunehmen und dann zu analysieren. Damit dies möglichst
fehlerfrei funktioniert, müssen die Spieler darauf achten, das Brett
nicht zu verdecken, wenn der Button zum Auslösen des Spielzuges
gedrückt wird.

## Anzweifeln

Sofern ein Anzweifeln noch möglich ist, wird im Display des aktiven
Spielers "!?" angezeigt. Auf der rechten Seite des Displays wird zusätzlich die Dauer des aktuelle Spielzuges in Sekunden angezeigt.

## Weitere Taster

Hinter den Buttons befinden sich fünf Taster.

* Grün/Rot: Taster für das Anzweifeln des Zuges  
  (einfaches Drücken)
* Gelb/Blau: Taster für Reset, Reboot, ??  
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
