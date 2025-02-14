# ScrabScrap v2 Hardware-Installation

## Teileliste

* [Raspberry PI 3](https://www.raspberrypi.com/products/raspberry-pi-3-model-b/)
* [Raspberry PI Camera (AZDelivery Kamera für Raspberry Pi) v1.3](https://www.az-delivery.de/products/raspberrykamerav1-3)
* [Anschluss-Kabel Raspberry PI Camera](https://www.az-delivery.de/products/200cm-ersatz-flexkabel-fur-raspberry-pi-kamera-und-das-raspberry-pi-display)
* [Button mit LED Grün/Gelb/Rot (EG STARTS 10x neue LED beleuchtet Arcade-Tasten mit Mikroschalter Mame Multicade)](https://www.amazon.de/gp/product/B01N549IDL)
* Schalter Grün
* Schalter Rot
* Schalter Gelb, Schwarz, Blau
* [2 * Display (AZDelivery 5 x 0,96 Zoll OLED Display I2C SSD1306 Chip 128 x 64 Pixel)](https://www.az-delivery.de/products/0-96zolldisplay)
* [RTC (AZDelivery Real Time Clock RTC DS3231 I2C)](https://www.az-delivery.de/products/ds3231-real-time-clock)
* [Kamera Extender](https://www.berrybase.de/kamerakabelverbinder-fuer-raspberry-pi-15-pin-zu-15-pin)
* Kabel & Stecker

<div style="display:none;page-break-after: always;">\pagebreak</div>

## Anschluss an die Raspberry PI GPIO

![PIN Layout](images/pin-layout.png)

Pin | GPiO | Funktion | Ziel
----|------|----------|-----
1   | 3V3  | I2C      | OLED1 / RTC vcc
3   | 2    | I2C /SDA | OLED1 / RTC sda
5   | 3    | I2C /SCL | OLED1 / RTC scl
9   | Gnd  | B yellow | button/led Gnd
11  | 17   | B yellow | button yellow
13  | 27   | L yellow | led yellow
17  | 3V3  | Pwr      | Pwr (3*) => OLED2
25  | Gnd  | Pwr      | Gnd (3*) => OLED2
29  | 5    | I2C SDA  | OLED2
31  | 6    | I2C SCL  | OLED2
33  | 13   | S yellow | switch yellow => Access Point
35  | 19   | S black  | switch black => reset
37  | 26   | S blue   | switch blue  => reboot
39  | Gnd  | B blk,bl | switch yellow/black/blue Gnd

Pin | GPiO | Funktion | Ziel
----|------|----------|-----
6   | Gnd  | I2C /Gnd | OLED1 / RTC Gnd
14  | Gnd  | B red    | button/led Gnd
16  | 23   | B red    | button red
18  | 24   | L red    | led red
20  | Gnd  | S red    | switch Gnd
22  | 25   | S red    | switch
30  | Gnd  | S green  | switch Gnd
32  | 12   | S green  | switch
34  | Gnd  | B green  | button/led Gnd
36  | 16   | B green  | button green
38  | 20   | L green  | led green

__Hinweis__ Die eingebauten LEDs der Button benötigen keinen Vorwiderstand. Werden diese ersetzt,
so müssen geeignete Vorwiderstände ergänzt werden.

<div style="display:none;page-break-after: always;">\pagebreak</div>

### Anschluss OLED (Display 1 - Grün)

| OLED | Raspberry PI          |
|------|-----------------------|
| SDA  | RPI PIN 3  (GPIO 2)   |
| SCL  | RPI PIN 5  (GPIO 2)   |
| VCC  | RPI PIN 1  (GPIO 3V3) |
| Gnd  | RPI PIN 6  (GPIO Gnd) |

### Anschluss OLED (Display 2 - Rot)

| OLED | Raspberry PI          |
|------|-----------------------|
| SDA  | RPI PIN 29  (GPIO 5)  |
| SCL  | RPI PIN 31  (GPIO 6)  |
| VCC  | RPI PIN 17 (GPIO 3V3) |
| Gnd  | RPI PIN 25 (GPIO Gnd) |

### Anschluss RTC

Die RTC wird parallel zum OLED1 angeschlossen.

| RTC  | Raspberry PI          |
|------|-----------------------|
| SDA  | RPI PIN 3  (GPIO 13)  |
| SCL  | RPI PIN 5  (GPIO 19)  |
| VCC  | RPI PIN 1  (GPIO 3V3) |
| Gnd  | RPI PIN 6  (GPIO Gnd) |

## Schaltplan

![Schaltplan](images/circuit-diagram.png)

## Kamera

### Kamera-Anschluss

![Kamera-Anschluss](images/camera-connector.png)

Kamera-Anschluss (Bild-Quelle: raspberrypi.com)

Das Flachbandkabel für die Kamera wird in einer Klemmschiene befestigt.
Hierzu die Klemmschiene vom Anschluss abziehen und das Flachbandkabel
vorsichtig reinschieben. Beim Flachbandkabel bitte vorher sicherstellen,
dass die Kontaktstreifen nicht beschädigt oder verbogen sind. In diesem
Fall das Flachbandkabel austauschen.

Die blaue Markierung muss beim Einbau in Richtung Klemmschiene zeigen.

### Aufbau des Kamera-Arms

Mit der unteren Inbus Schraube (1; HX5) den Kamera-Arm am Spielbrett befestigen.
Die mittlere Schraube (2; HX5) kann zur Höheneinstellung verwendet werden. Mit der
RPI Kamera v1.3 sollte sich die Kamera-Linse ca. 47,5cm über dem Spielbrett
befinden. Eine Feineinstellung und Rotation der Kamera kann direkt am Kamera-
Halter (3; HX5) vorgenommen werden.

![Kamera-Arm](images/camera-arm.png)
