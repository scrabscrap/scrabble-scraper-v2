
from random import randint, random
from typing import List


font = None
font1 = None
font2 = None

DISP_MESSAGES = {
    'PAUSE' : ('Pause', font1, (0,0)),
    'BOOT' : ('Boot', font1, (10,10)),
    'DOUBT' : ('?!', font2, (0,0)),
    'TIME' : ('{t:04d}', font2, (5,5)),
    'PLAYTIME' : ('{t:2d}', font1, (0,5)),
}  # type: ignore

class message:

    def __init__(self) -> None:
        self.msg = []

    def add(self, message):
        self.msg.append(message)

    def clear(self):
        print('')
        self.msg.clear()

    def print(self):
        t = randint(0, 9999)
        print(self.msg)
        for i in self.msg:
            txt = eval("f'{}'".format(DISP_MESSAGES[i][0]))
            print(f'{txt} pos: {DISP_MESSAGES[i][2]}')


if __name__ == '__main__':
    m = message()
    m.add('BOOT')
    m.add('TIME')
    m.add('PLAYTIME')
    m.print()
    m.clear()
    m.add('TIME')
    m.add('PLAYTIME')
    m.add('DOUBT')
    m.print()


