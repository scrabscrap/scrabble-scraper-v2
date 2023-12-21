"""factory for camera"""
import logging
from time import sleep

from hardware.camera_impl import Camera, camera_dict
# import rpi_camera for adding to dict if available
from hardware.camera_rpi_impl import RPI_CAMERA  # pylint: disable=wrong-import-order

logging.info(f'camera_rpi imported = {RPI_CAMERA}')

# default picamera - fallback file
cam: Camera = camera_dict['picamera']() if 'picamera' in camera_dict else camera_dict['file']()


def switch_camera(camera: str) -> bool:
    """switch camera - threadpool has to be restarted"""
    global cam  # pylint: disable=global-statement
    cam.cancel()

    if camera.lower() in camera_dict:
        logging.info(f'switch camera to {camera}')
        cam = camera_dict[camera]()
        return True
    return False


def main() -> None:
    """main function"""

    import sys
    from threading import Event

    from threadpool import pool

    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, force=True,
                        format='%(asctime)s [%(levelname)-5.5s] %(funcName)-20s: %(message)s')

    logging.info(f'>> config {camera_dict}')
    logging.info(f'cam type: {type(cam)}')
    pool.submit(cam.update, event=Event())                                                  # start cam
    sleep(5)
    switch_camera('opencv')
    logging.info(f'cam type: {type(cam)}')
    pool.submit(cam.update, event=Event())                                                  # start cam
    sleep(5)
    cam.cancel()


if __name__ == '__main__':
    main()
