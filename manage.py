import os
import threading


curpath = os.getcwd()
print(curpath)

def nats_server():
    natsserver_path = curpath + r'\nats-server.exe'
    os.system(natsserver_path)


def game_server():
    os.system('python ./app/server2.py')


thread1 = threading.Thread(target =  nats_server)
thread2 = threading.Thread(target = game_server)

thread1.start()
thread2.start()

# thread1.join()
# thread2.join()
