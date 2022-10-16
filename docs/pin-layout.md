
# Pin Belegung

Pin | GPiO | Funktion | Ziel
----|------|----------|-----
1   | 3V3  | I2C      | MUX vcc
3   | 2    | I2C /SDA | MUX sda
5   | 3    | I2C /SCL | MUX scl
7   | 4    |          |
9   | Gnd  | B yellow | button/led Gnd
11  | 17   | B yellow | button yellow
13  | 27   | L yellow | led yellow
15  | 22   |          |
17  | 3V3  | Pwr      | Pwr (3*) => OLED, OLED, RTC
19  | 10   |          |
21  | 9    |          |
23  | 11   |          |
25  | Gnd  | Pwr      | Gnd (3*) => OLED, OLED, RTC
27  | -    |          |
29  | 5    |          |
31  | 6    |          |
33  | 13   |          |
35  | 19   | S black  | switch black => reset
37  | 26   | S blue   | switch blue  => reboot
39  | Gnd  | B blk,bl | switch black/blue Gnd

Pin | GPiO | Funktion | Ziel
----|------|----------|-----
2   | 5V   |          |
4   | 5V   |          |
6   | Gnd  | I2C /Gnd | MUX Gnd
8   | 14   |          |
10  | 15   |          |
12  | 18   |          |
14  | Gnd  | B red    | button/led Gnd
16  | 23   | B red    | button red
18  | 24   | L red    | led red
20  | Gnd  | S red    | switch Gnd
22  | 25   | S red    | switch
24  | 8    |          |
26  | 7    |          |
28  | -    |          |
30  | Gnd  | S green  | switch Gnd
32  | 12   | S green  | switch
34  | Gnd  | B green  | button/led Gnd
36  | 16   | B green  | button green
38  | 20   | L green  | led green
40  | 21   |          |

![Pin Layout](images/pin-layout.png)
