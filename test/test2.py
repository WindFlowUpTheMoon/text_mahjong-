import threading
from time import sleep


def func():
    print('hey')
    sleep(3)
    print('world')

thread = threading.Thread(target = func)
thread.start()
thread.join()

print('who are you')
print('im fine')