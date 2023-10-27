import os
import threading
from app.server2 import GameServer
from time import sleep


def nats_server():
    curpath = os.getcwd()
    print(curpath)
    natsserver_path = curpath + r'\nats-server.exe'
    os.system(natsserver_path)


# 服务多启
def server_manage():
    gs = GameServer()


thread1 = threading.Thread(target =  nats_server)
thread2 = threading.Thread(target = server_manage)

thread1.start()
thread2.start()

# thread1.join()
# thread2.join()
