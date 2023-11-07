from threading import Thread
from time import sleep


def f1():
    print('hello')
    sleep(2)
    print('world')


def f2():
    print('world')


for i in range(3):
    thread = Thread(target = f1)
    thread.start()
