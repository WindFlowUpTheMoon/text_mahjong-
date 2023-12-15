import os
import threading
from app.server3 import GameServer
from time import sleep
from pynats import NATSClient
from app.base2 import Player
import argparse
from traceback import print_exc


class Manager:
    def __init__(self, game_type):
        self.nats_addr = "nats://localhost:4222"
        self.players = []
        self.players_num = 0
        self.server_id = 0
        self.game_type = game_type  # 游戏类型：双人、三人、四人等
        self.connect()
        self.subscribe()


    def connect(self):
        self.client = NATSClient(self.nats_addr)
        self.client.connect()


    def disconnect(self):
        self.client.close()


    def send_startserver(self, server_id):
        self.client.publish(str(server_id) + '.startserver', payload = 'start'.encode())


    def new_gameserver(self, server_id, players):
        uniqid_players_map, id_players_map = dict(), dict()
        for i, player in enumerate(players):
            uniqid_players_map[player.uniq_id] = player
            player.id = i + 1
            id_players_map[i + 1] = player
        gs = GameServer(server_id, players, uniqid_players_map, id_players_map)


    def subscribe(self):
        self.client.subscribe('join', callback = self.handle_join)
        self.client.wait()


    def handle_join(self, msg):
        print('join')
        name, uniq_id, ip = msg.payload.decode().split(',')
        self.players.append(Player(name, uniq_id))
        self.players_num += 1
        # print(self.players_num, self.game_type)
        if self.players_num % self.game_type == 0:  # 人齐才开桌
            print('new server')
            # 新建一个子线程运行game_server
            ind = self.players_num // self.game_type
            players = self.players[(ind - 1) * self.game_type: ind * self.game_type]
            thread = threading.Thread(target = self.new_gameserver, args = (self.server_id, players,))
            thread.start()
            sleep(1)  # 确保线程创建后再发送服务启动消息
            self.send_startserver(self.server_id)
            self.server_id += 1


def nats_server():
    curpath = os.getcwd()
    print(curpath)
    natsserver_path = curpath + r'\nats-server.exe'
    os.system(natsserver_path)


def server_manage(game_type):
    try:
        game_type = int(game_type)
    except Exception as e:
        print_exc()
        return
    print('game manager start')
    manager = Manager(game_type)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-game_type', default = 2, help = '选择游戏类型，双人、三人、四人或者更多')
    args = parser.parse_args()

    thread1 = threading.Thread(target = nats_server)
    thread2 = threading.Thread(target = server_manage, args = (args.game_type,))

    thread1.start()
    sleep(3)
    thread2.start()
