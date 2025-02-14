# ScrabScrap v2 Hardware-Installation

## Parts list

* [Raspberry PI 3](https://www.raspberrypi.com/products/raspberry-pi-3-model-b/)
* [Raspberry PI Camera (AZDelivery Camera for Raspberry Pi) v1.3](https://www.az-delivery.de/products/raspberrykamerav1-3)
* [Connection  cable Raspberry PI Camera](https://www.az-delivery.de/products/200cm-ersatz-flexkabel-fur-raspberry-pi-kamera-und-das-raspberry-pi-display)
* [Button with LED Green/Yellow/red (EG STARTS 10x neue LED beleuchtet Arcade-Tasten mit Mikroschalter Mame Multicade)](https://www.amazon.de/gp/product/B01N549IDL)
* Switch Green
* Switch Red
* Switch Yellow, Black, Blue
* [2 * Display (AZDelivery 5 x 0,96 Zoll OLED Display I2C SSD1306 Chip 128 x 64 Pixel)](https://www.az-delivery.de/products/0-96zolldisplay)
* [RTC (AZDelivery Real Time Clock RTC DS3231 I2C)](https://www.az-delivery.de/products/ds3231-real-time-clock)
* [Camera Extender](https://www.berrybase.de/kamerakabelverbinder-fuer-raspberry-pi-15-pin-zu-15-pin)
* Cables & connectors

<div style="display:none;page-break-after: always;">\pagebreak</div>

## Connection to the Raspberry PI GPIO

![PIN Layout](images/pin-layout.png)

Pin | GPiO | Function | Usage
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
37  | 26   | S blue   | switch blue => reboot
39  | Gnd  | B blk,bl | switch yellow/black/blue Gnd

Pin | GPiO | Function | Target
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

__Note__ The built-in LEDs of the button do not require a resistor. If these are replaced, a suitable resistor must be added.

<div style="display:none;page-break-after: always;">\pagebreak</div>

### OLED connection (display 1 - green)

| OLED | Raspberry PI          |
|------|-----------------------|
| SDA  | RPI PIN 3 (GPIO 2)    |
| SCL  | RPI PIN 5 (GPIO 2)    |
| VCC  | RPI PIN 1 (GPIO 3V3)  |
| Gnd  | RPI PIN 6 (GPIO Gnd)  |

### OLED connection (display 2 - red)

| OLED | Raspberry PI          |
|------|-----------------------|
| SDA  | RPI PIN 29 (GPIO 5)   |
| SCL  | RPI PIN 31 (GPIO 6)   |
| VCC  | RPI PIN 17 (GPIO 3V3) |
| Gnd  | RPI PIN 25 (GPIO Gnd) |

### RTC connection

The RTC is connected in parallel to the OLED1.

| RTC  | Raspberry PI          |
|------|-----------------------|
| SDA  | RPI PIN 3 (GPIO 13)   |
| SCL  | RPI PIN 5 (GPIO 19)   |
| VCC  | RPI PIN 1 (GPIO 3V3)  |
| Gnd  | RPI PIN 6 (GPIO Gnd)  |

<div style="display:none;page-break-after: always;">\pagebreak</div>

## Circuit diagram

![Circuit diagram](images/circuit-diagram.png)

<div style="display:none;page-break-after: always;">\pagebreak</div>

## Camera

### Camera connection

![Camera-connector](images/camera-connector.png)

Camera connector (image source: raspberrypi.com)

The ribbon cable for the camera is fixed in a clamping rail.
Remove the clamp from the connector and carefully slide the ribbon cable in.
When using the ribbon cable, please make sure beforehand that the contact strips
are not damaged or bent. In this case, replace the ribbon cable.

The blue marking must point in the direction of the clamping rail during installation.

<div style="display:none;page-break-after: always;">\pagebreak</div>

### Assembling the camera arm

Fasten the camera arm to the board with the lower Allen screw (1; HX5).
The middle screw (2; HX5) can be used to adjust the height. With the
RPI camera v1.3 the camera lens should be approx. 47.5cm above the board.
Fine adjustment and rotation of the camera can be done directly at the camera-
holder (3; HX5).

![Camera arm](images/camera-arm.png)
