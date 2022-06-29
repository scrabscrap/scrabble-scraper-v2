
import atexit
import io
import time
from concurrent.futures import Future, ThreadPoolExecutor
from threading import Event
import logging

from config import config
from util import singleton
from display import Display

try:
    from picamera import PiCamera  # type: ignore
except ImportError:
    logging.warn('use mock as PiCamera')
    from simulate.fakecamera import FakeCamera as PiCamera  # type: ignore

pool = ThreadPoolExecutor()


@singleton
class Camera:

    def __init__(self):
        self.frame = []
        self.camera = PiCamera()
        self.camera.resolution = (992, 976)
        self.camera.framerate = config.FPS
        if config.ROTATE:
            self.camera.rotation = 180
        self.event = None
        atexit.register(self._atexit)

    def _atexit(self) -> None:
        self.camera.close()

    def read(self):
        return self.frame

    def update(self, ev: Event) -> None:
        self.event = ev
        with self.camera as camera:
            stream = io.BytesIO()
            for _ in camera.capture_continuous(stream, format="bgr", use_video_port=True):
                stream.truncate()
                stream.seek(0)
                self.frame = stream.getvalue()
                if ev.is_set():
                    break
        ev.clear()

    def cancel(self) -> None:
        if self.event is not None:
            self.event.set()

    def done(self, result: Future) -> None:
        print(f'done {result}')


class RepeatedTimer:
    def __init__(self, interval: int, function: callable):  # type: ignore
        self.interval = interval
        self.function = function
        self.event = None
        self.start = time.time()

    @property
    def _time(self):
        return self.interval - ((time.time() - self.start) % self.interval)

    def tick(self, ev) -> None:
        self.event = ev
        while not ev.wait(self._time):
            self.function()
        ev.clear()

    def cancel(self) -> None:
        if self.event is not None:
            self.event.set()

    def done(self, result: Future) -> None:
        print(f'done {result}')


cnt: int = 0


def timer_call_back():
    global cnt
    cnt += 1
    print(f'ping {cnt}')


# camera
cam = Camera()
cam_event = Event()
cam_future = pool.submit(cam.update, cam_event)
cam_future.add_done_callback(cam.done)

# timer
timer = RepeatedTimer(1, timer_call_back)
timer_event = Event()
timer_future = pool.submit(timer.tick, timer_event)
timer_future.add_done_callback(timer.done)

logging.basicConfig(
    level=logging.DEBUG, format='%(asctime)s [%(levelname)-5.5s] %(funcName)-20s: %(message)s')

if __name__ == '__main__':
    import platform

    print(f'{platform.machine()} - {platform.architecture()} - {platform.system()}')

    time.sleep(10)
    if not timer_future.cancel():
        # timer.cancel()
        timer_event.set()
    # restart
    print('restart')
    if not timer_future.running():
        timer_future = pool.submit(timer.tick, timer_event)
    time.sleep(10)
    if not timer_future.cancel():
        timer.cancel()

    print(f'cam read')
    pic = cam.read()
    print(f'size pic {len(pic)}')
    cam_event.set()

    print(f'pool {pool}')

    disp = Display()
    disp.show_ftp_err()
    disp.clear()
