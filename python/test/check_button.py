import logging
import time
import unittest
from signal import alarm, pause

from button import Button
from led import LED, LEDEnum

logging.basicConfig(
    level=logging.DEBUG, format='%(asctime)s [%(levelname)-5.5s] %(funcName)-20s: %(message)s')

# falls sowohl when_held als auch when_pressed genutzt werden soll:
#
# from gpiozero import Button
#
# Button.was_held = False
#
# def held(btn):
#     btn.was_held = True
#     print("button was held not just pressed")
#
# def released(btn):
#     if not btn.was_held:
#         pressed()
#     btn.was_held = False
#
# def pressed():
#     print("button was pressed not held")
#
# btn = Button(2)
#
# btn.when_held = held
# btn.when_released = released
#
class MockState():

    def __init__(self):
        self.lastpress = 0
        self.bounce = {'GREEN': .0, 'RED': .0, 'YELLOW': .0, 'DOUBT0': .0,
                       'DOUBT1': .0, 'RESET': .0, 'CONFIG': .0, 'REBOOT': .0}

    def do_ready(self):
        pass

    # Versuch mit Software Bounce
    # nach Release darf ein Drücken nicht innerhalb einer 0.1s
    # erfolgen (verhindert aber schnelles Drücken!)
    # Wenn dies im State ergänzt werden soll, muss der Button
    # berücksichtigt werden
    def press_button(self, button: str) -> None:
        logging.debug(f'_ button press: {button}')
        press = time.time()
        if press < self.bounce[button] + 0.1:
            logging.debug(f'  {self.bounce[button]} {press} ignore bounce')
        else:
            if button == 'GREEN':
                LED.switch_on({LEDEnum.green})
            elif button == 'RED':
                LED.switch_on({LEDEnum.red})
            elif button == 'YELLOW':
                LED.switch_on({LEDEnum.yellow})
            elif button == 'DOUBT0':
                LED.blink_on({LEDEnum.green})
            elif button == 'DOUBT1':
                LED.blink_on({LEDEnum.red})
            elif button == 'REBOOT':
                LED.blink_on({LEDEnum.green, LEDEnum.yellow})
                time.sleep(2)
                LED.switch_on({})
                alarm(1)
            elif button == 'CONFIG':
                LED.blink_on({LEDEnum.red, LEDEnum.yellow})
            elif button == 'RESET':
                LED.blink_on({LEDEnum.red, LEDEnum.yellow, LEDEnum.green})
            else:
                LED.switch_on({})
        pass

    def release_button(self, button: str) -> None:
        logging.debug(f'= button release: {button}\n')
        self.bounce[button] = time.time()
        pass


class ButtonTestCase(unittest.TestCase):

    def test_button(self):
        state = MockState()
        button_handler = Button()
        button_handler.start(state)  # type: ignore
        logging.debug('start - exit with button REBOOT')
        pause()


if __name__ == '__main__':
    unittest.main()
