import socket
from pynats import NATSClient
import json
from datetime import datetime
from random import randint
import sys
from time import sleep
from os import path
from threading import Thread
from pynput import keyboard
from traceback import print_exc


# 客户端类
class Client:
    def __init__(self, name = '匿名'):
        self.name = name
        self.nats_addr = 'nats://172.31.17.170:4222'
        self.ip = str(socket.gethostbyname(socket.gethostname()))
        self.uniq_id = self.generate_randomId()
        print(self.uniq_id)
        self.isjoin = False
        self.hand_cards = {}
        self.pg_cards = []
        self.otherplayers_cards = []
        self.tablecards_num = 0
        self.leftcards = []


    def on_press(self, key):
        '''
        键盘按键处理
        '''
        if key == keyboard.KeyCode.from_char('v'):
            # 打印其他牌面信息
            print('\n牌堆剩余：' + str(self.tablecards_num))
            for id, pgcards in self.otherplayers_cards:
                print(str(id) + '号玩家：', pgcards)
            print('牌面：', self.leftcards)
            print()
        elif key == keyboard.KeyCode.from_char('h'):
            # 打印帮助文档
            with open('../doc/help.txt', 'r', encoding = 'utf-8') as f:
                print(f.read())


    def keyboard_listening(self):
        '''
        按键监听
        '''
        with keyboard.Listener(on_press = self.on_press) as listener:
            listener.join()


    def generate_randomId(self):
        '''
        生成玩家的随机唯一id
        '''
        t = datetime.now().strftime('%d%H%M%S')
        rn = randint(1, 100)
        return t + str(rn)


    def print_playercards(self, pgcards, handcards):
        '''
        漂亮打印玩家手牌和碰/杠后的牌
        '''
        a = [str(i) for i in range(1, 10)]
        b = '一 二 三 四 五 六 七 八 九'.split(' ')
        num_map = dict(zip(a, b))
        l = list()
        for k, v in handcards.items():
            for v0 in v:
                l.append(v0)
            if v: l.append(' ' * 2)
        l1 = [num_map[i[0]] if i[0] in a else i[0] for i in l]
        l2 = [i[1] for i in l]

        lp1 = [num_map[i[0]] if i[0] in a else i[0] for i in pgcards]
        lp2 = [i[1] for i in pgcards]

        for i in l1:
            print(i + ' ', end = '')
        if pgcards:
            print(' ' * 19, end = '')
        for i in lp1:
            print(i + ' ', end = '')
        print()

        for i in l2:
            print(i + ' ', end = '')
        if pgcards:
            print(' ' * 18, end = '')
        for i in lp2:
            print(i + ' ', end = '')
        print()


    def get_handcards_num(self):
        '''
        计算手牌数量
        '''
        l = 0
        for k, v in self.hand_cards.items():
            for i in v:
                l += 1
        return l
        # print('1111',self.handcards_num)


    # 发送加入请求
    def send_join(self):
        with NATSClient(self.nats_addr) as client:
            msg = (self.name + ',' + self.uniq_id + ',' + self.ip).encode()
            client.publish('join', payload = msg)


    def send_throwcard(self, ind):
        with NATSClient(self.nats_addr) as client:
            msg = (self.uniq_id + ',' + str(ind)).encode()
            client.publish('throwcard', payload = msg)


    def send_peng(self, ifpeng):
        with NATSClient(self.nats_addr) as client:
            msg = (self.uniq_id + ',' + ifpeng).encode()
            client.publish('peng', payload = msg)


    def send_chigang(self, ifchigang):
        with NATSClient(self.nats_addr) as client:
            msg = (self.uniq_id + ',' + ifchigang).encode()
            client.publish('chigang', payload = msg)


    def send_bugang(self, ifbugang):
        with NATSClient(self.nats_addr) as client:
            msg = (self.uniq_id + ',' + ifbugang).encode()
            client.publish('bugang', payload = msg)


    def send_angang(self, ifangang):
        with NATSClient(self.nats_addr) as client:
            msg = (self.uniq_id + ',' + ifangang).encode()
            client.publish('angang', payload = msg)


    def receive(self):
        with NATSClient(self.nats_addr) as client:
            # 订阅加入消息
            client.subscribe(self.uniq_id + '.isjoin', callback = self.handle_isjoin)
            # 订阅游戏开始消息
            client.subscribe('startgame', callback = self.handle_startgame)
            # 订阅更新卡牌消息
            client.subscribe(self.uniq_id + '.cardsinfo', callback = self.handle_cardsinfo)
            # 订阅打印手牌消息
            client.subscribe(self.uniq_id + '.showmycards', callback = self.handle_showmycards)
            # 订阅可否打牌消息
            client.subscribe(self.uniq_id + '.throwcard', callback = self.handle_throwcard)
            # 订阅打牌消息
            client.subscribe(self.uniq_id + '.throwcardinfo', callback = self.throwcardinfo)
            # 订阅摸牌消息
            client.subscribe(self.uniq_id + '.getcard', callback = self.handle_getcard)
            # 订阅可否碰牌消息
            client.subscribe(self.uniq_id + '.peng', callback = self.handle_peng)
            # 订阅碰牌消息
            client.subscribe(self.uniq_id + '.penginfo', callback = self.handle_penginfo)
            # 订阅是否吃杠消息
            client.subscribe(self.uniq_id + '.chigang', callback = self.handle_chigang)
            # 订阅吃杠消息
            client.subscribe(self.uniq_id + '.chiganginfo', callback = self.handle_chiganginfo)
            # 订阅是否补杠消息
            client.subscribe(self.uniq_id + '.bugang', callback = self.handle_bugang)
            # 订阅补杠消息
            client.subscribe(self.uniq_id + '.buganginfo', callback = self.handle_buganginfo)
            # 订阅是否暗杠消息
            client.subscribe(self.uniq_id + '.angang', callback = self.handle_angang)
            # 订阅暗杠消息
            client.subscribe(self.uniq_id + '.anganginfo', callback = self.handle_anganginfo)
            # 订阅自摸消息
            client.subscribe(self.uniq_id + '.zimo', callback = self.handle_zimo)
            # 订阅点炮消息
            client.subscribe(self.uniq_id + '.dianpao', callback = self.handle_dianpao)
            client.wait()


    def handle_isjoin(self, msg):
        msg = msg.payload.decode()
        print(msg)
        if msg == '欢迎加入对局！':
            self.isjoin = True
            print('正在等待其他玩家加入对局。。。')
            sleep(1)
        else:
            sys.exit()


    def handle_startgame(self, msg):
        msg = msg.payload.decode()
        print(msg + '\n')


    def handle_cardsinfo(self, msg):
        msg = msg.payload.decode()
        msg = json.loads(msg)
        mycards, self.otherplayers_cards, self.tablecards_num, self.leftcards = msg
        self.hand_cards, self.pg_cards = mycards
        # print(type(msg),msg)


    def handle_showmycards(self, msg):
        msg = msg.payload.decode()
        if msg == 'showmycards':
            print('你的牌为：')
            self.print_playercards(self.pg_cards, self.hand_cards)


    def handle_throwcard(self, msg):
        msg = msg.payload.decode()
        if msg == 'throwcard':
            while True:
                ind = input('打掉: ')
                # 考虑玩家非法输入
                try:
                    ind = int(ind)
                except:
                    if ind == 'x':  # 打掉花牌
                        break
                    else:
                        print('输入有误，请重新输入！')
                else:
                    l = self.get_handcards_num()
                    if 0 < ind <= l:
                        ind -= 1
                        break
                    elif -l <= ind < 0:
                        break
                    else:
                        print('输入有误，请重新输入！')
            self.send_throwcard(ind)


    def throwcardinfo(self, msg):
        msg = msg.payload.decode()
        print(msg)


    def handle_getcard(self, msg):
        msg = msg.payload.decode()
        print('摸到牌：', msg)


    def handle_peng(self, msg):
        msg = msg.payload.decode()
        if msg == '可碰':
            while True:
                ifpeng = input('碰？(输入y/n) ')
                if ifpeng in ('y', 'n', 'Y', 'N'):
                    break
            self.send_peng(ifpeng)


    def handle_penginfo(self, msg):
        msg = msg.payload.decode()
        print(msg)


    def handle_chigang(self, msg):
        msg = msg.payload.decode()
        if msg == '可吃杠':
            while True:
                ifchigang = input('杠？(输入y/n) ')
                if ifchigang in ('y', 'n', 'Y', 'N'):
                    break
            self.send_chigang(ifchigang)


    def handle_chiganginfo(self, msg):
        msg = msg.payload.decode()
        print(msg)


    def handle_bugang(self, msg):
        msg = msg.payload.decode()
        if msg == '可补杠':
            while True:
                ifbugang = input('补杠？(输入y/n) ')
                if ifbugang in ('y', 'n', 'Y', 'N'):
                    break
            self.send_bugang(ifbugang)


    def handle_buganginfo(self, msg):
        msg = msg.payload.decode()
        print(msg)


    def handle_angang(self, msg):
        msg = msg.payload.decode()
        if msg == '可暗杠':
            while True:
                ifangang = input('暗杠？(输入y/n) ')
                if ifangang in ('y', 'n', 'Y', 'N'):
                    break
            self.send_angang(ifangang)


    def handle_anganginfo(self, msg):
        msg = msg.payload.decode()
        print(msg)


    def handle_zimo(self):
        pass


    def handle_dianpao(self):
        pass


def rejoin(curpath):
    '''
    断线重连
    '''
    c = Client()
    filename = curpath.split('\\')[-1].split('.')[0]
    with open(filename + '_clientInfo.txt', 'r', encoding = 'utf-8') as f:
        c.name, c.uniq_id = f.read().split(',')
    c.receive()


def start(curpath):
    filename = curpath.split('\\')[-1].split('.')[0]
    print('filename:', filename)
    c = Client()
    with open(filename + '_clientInfo.txt', 'w', encoding = 'utf-8') as f:
        f.write(c.name + ',' + c.uniq_id)
    c.send_join()

    keyboard_thread = Thread(target = c.keyboard_listening)
    keyboard_thread.start()

    c.receive()


if __name__ == '__main__':
    # print(path.abspath(__file__))
    curpath = path.abspath(__file__)
    try:
        start(curpath)
    except:
        print_exc()
    # rejoin(curpath)   #   如果断线了运行此命令
