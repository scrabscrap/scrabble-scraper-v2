
from config import config
from display import Display


class MockDisplay(Display):

    def show_boot(self):
        print('| Boot  |', end='')
        self.show()

    def show_reset(self):
        print('| Reset |', end='')
        self.show()

    def show_ready(self):
        print('| Ready |', end='')
        self.show()

    def show_pause(self):
        print('| Pause |', end='')
        self.show()

    def add_malus(self, player):
        if player == 0:
            print('(-10 /    )', end='')
        else:
            print('(    / -10)', end='')
        self.show()

    def add_remove_tiles(self, player):
        if player == 0:
            print('| Entf. Zug / ', end='')
        else:
            print('|           / Entf. Zug', end='')
        self.show()

    def show_cam_err(self):
        print('| \u2620 Cam |', end='')
        self.show()

    def show_ftp_err(self):
        print('| \u2620 Ftp |', end='')
        self.show()

    def show_config(self):
        print('| \u270E Cfg |', end='')
        self.show()

    def add_time(self, player, t1, p1, t2, p2):
        m1, s1 = divmod(abs(config.MAX_TIME - t1), 60)
        m2, s2 = divmod(abs(config.MAX_TIME - t2), 60)
        doubt1 = 'x' if player == 0 and p1 <= config.DOUBT_TIMEOUT else ' '
        doubt2 = 'x' if player == 1 and p2 <= config.DOUBT_TIMEOUT else ' '
        left = f'{doubt1} -{m1:1d}:{s1:02d} ({p1:4d})' if config.MAX_TIME - \
            t1 < 0 else f'{doubt1} {m1:02d}:{s1:02d} ({p1:4d})'
        right = f'{doubt2} -{m2:1d}:{s2:02d} ({p2:4d})' if config.MAX_TIME - \
            t2 < 0 else f'{doubt2} {m2:02d}:{s2:02d} ({p2:4d})'
        print(f'|{left} / {right}|', end='')

    def clear_message(self):
        pass

    def clear(self):
        pass

    def show(self):
        print('')
