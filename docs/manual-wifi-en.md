---
output:
  pdf_document:
    path: pdf/manual-wifi-en.pdf
    highlight: tango
geometry: margin=2cm
---

# Configuration of the WiFi entries

## Add a new WiFi

If ScrabScrap does not find a known WiFi, an access point is opened. The WiFi is named
`ScrabScrap`. To add a new WiFi, the following steps must be carried out.

1. connect the local computer to the WiFi `ScrabScrap` (the default password is `scrabscrap`).
2. navigate in the browser to the URL `<http://10.0.0.1:5050>  
  ![Open the configuration](images/wlan-02.png)
3. the configuration page of ScrabScrap is displayed  
  ![configuration page](images/wlan-03.png)
4. select the menu item "WiFi"  
  ![WiFi](images/wlan-04.png)  
  There you can perform a 'scan' to display the accessible WiFis.
  You may have to start the scan more often if the desired WiFis are not displayed immediately.
5. Enter the SSID and the password of the WiFi in the input fields and confirm with "Add".

## Delete WiFi entry

WiFi configurations can be deleted. To do this, select the WiFi to be deleted in the
"Delete configured WiFi" area and click on the WiFi to be deleted and delete it by
clicking on the "Delete" button.

_Note:_ The currently connected WiFi and the pre-configured WiFis cannot be selected.

## Change WiFi

If several WiFis are available, the WiFi with the strongest reception is selected.
If another one is to be used, this can be selected in the "Select configured WiFi" area.
The selected WiFi will be activated immediately.

_Note:_ The currently connected WiFi cannot be selected.
