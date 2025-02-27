# Configuration of WiFi Entries

## Adding a New WiFi Network

If ScrabScrap does not detect a known WiFi network, a hotspot can be started by pressing the AP button for more than 3 seconds. This will activate the Access Point, which is named "ScrabScrap". To add a new WiFi network, follow these steps:

1.	Connect the local computer to the ScrabScrap WiFi network (default password: scrabscrap).
2.	Open a web browser and navigate to http://10.42.0.1:5050.
3.	The ScrabScrap configuration page will be displayed.
4.	Navigate to “Settings” -> “WiFi”.
5.  If the desired WiFi network is not listed, perform a Scan first.
6.	Select the desired SSID, enter the WiFi password (PSK), and confirm by clicking “Add”.

![Konfigurationsseite](images/wlan-03.png)  
Configuration page

![WiFi](images/wlan-04.png)  
WiFi page

## Deleting a WiFi Entry

Stored WiFi configurations can be removed. To delete an entry, go to the “Configured WiFi” section, select the network to be removed, and click the “Delete” button.

_Note:_ The currently connected network and preconfigured WiFi networks cannot be deleted.

## Switching WiFi Networks

If multiple WiFi networks are available, ScrabScrap automatically connects to the one with the strongest signal. To manually switch networks, navigate to the “Configured WiFi” section and select the desired network. The selected WiFi will be activated immediately.

_Note:_ The currently connected network cannot be selected.
