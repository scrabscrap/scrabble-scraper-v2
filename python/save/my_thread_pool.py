
import time
from concurrent.futures import Future, ThreadPoolExecutor
from threading import Event
from typing import Any

futures_set = []


def running01() -> int:
    time.sleep(2)
    print('running01 ended')
    return 42


def callback01(result) -> None:
    print(f'callback01 {result}')


def running02() -> None:
    time.sleep(1.1)
    print('running02 ended')


def callback02(result) -> None:
    print(f'callback02 {result}')


def running03() -> None:
    time.sleep(2.5)
    print('running03 ended')


def callback03(result) -> None:
    print(f'callback03 {result}')


def running(val: int) -> int:
    time.sleep(2.3)
    return val*2

def callback(result) -> None:
    print(f'result callback {result}')

def runlist(val: list) -> None:
    print(f'runlist: {val}')
    time.sleep(2)


def longrunning(event: Event, val: int) -> int:
    tick = 0
    while True:
        event.wait(1)
        if event.is_set():
            break
        tick += 1
        print(f'tick: {tick}')
    return val*2

def longcallback(result: Future) -> None:
    ret = result.result()
    print(f'result callback {ret}/{result}')

def tp_tryout() -> None:
    executor = ThreadPoolExecutor()
    print(f'queue size: {executor._work_queue.qsize()} max workers: {executor._max_workers}')

    ev = Event()
    flongrunning = executor.submit(longrunning, ev, 42)
    flongrunning.add_done_callback(longcallback)

    f1 = executor.submit(running01)
    f1.add_done_callback(callback01)
    futures_set.append(f1)

    f2 = executor.submit(running02)
    f2.add_done_callback(callback02)
    futures_set.append(f2)

    f3 = executor.submit(running03)
    f3.add_done_callback(callback03)
    futures_set.append(f3)

    for i in range(20):
        print(f'add job {i}')
        f = executor.submit(running03)
        f.add_done_callback(callback03)
        futures_set.append(f)

    print(f'len futures_set: {len(futures_set)}')
    while len(futures_set) > 0:
        if executor._work_queue.qsize() > 0:
            print(f'queue size: {executor._work_queue.qsize()} max workers: {executor._max_workers}')
        for f in futures_set:
            if f.done():
                futures_set.remove(f)
            time.sleep(0.01)
    print(f'size future_set: {len(futures_set)}')

    results = executor.map(running, [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20])
    # for i in results:
    #     i.add_done_callback(callback)
    for i in results:
        print(i)

    # f.add_done_callback(longcallback)
    if not flongrunning.cancel():
        ev.set()

    results = executor.map(runlist, [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20])


if __name__ == '__main__':
    tp_tryout()
