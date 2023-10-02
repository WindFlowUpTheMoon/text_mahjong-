import socket
from pynats import NATSClient
import json
from datetime import datetime
from random import randint
import sys
from time import sleep
from os import path
# from threading import Thread
# from pynput import keyboard
from traceback import print_exc
from collections import Counter
from pprint import pprint


# 客户端类
class Client:
    def __init__(self, name = '匿名'):
        self.name = name
        self.nats_addr = 'nats://localhost:4222'
        self.ip = str(socket.gethostbyname(socket.gethostname()))
        self.uniq_id = self.generate_randomId()
        # print(self.uniq_id)
        self.isjoin = False
        self.hand_cards = {}
        self.pg_cards = []
        self.otherplayers_cards = []
        self.tablecards_num = 0
        self.leftcards = []


    def set_natsaddr(self, ip):
        self.nats_addr = 'nats://'+str(ip)


    def connect(self):
        self.client = NATSClient(self.nats_addr)
        self.client.connect()


    def disconnect(self):
        self.client.close()


    def get_help(self):
        msg='''
            /****************************************************************************/
            输入 正整数n 代表要打掉的第n张手牌，输入 -n 代表要打掉的倒数第n张手牌，输入 x 打掉手里的花牌；
            输入 v 可查看其他牌面信息，包括牌堆剩余数量、其他玩家碰/杠后放桌上的牌、被打掉的牌；
            输入其他的信息将向其他玩家广播此信息；
            /****************************************************************************/
            '''
        print(msg)


    # def on_press(self, key):
    #     '''
    #     键盘按键处理
    #     '''
    #     if key == keyboard.KeyCode.from_char('v'):
    #         # 打印其他牌面信息
    #         print('\n牌堆剩余：' + str(self.tablecards_num))
    #         for id, pgcards in self.otherplayers_cards:
    #             print(str(id) + '号玩家：', pgcards)
    #         print('牌面：')
    #         self.print_leftcards(self.leftcards)
    #         print()
    #     elif key == keyboard.KeyCode.from_char('h'):
    #         # 打印帮助文档
    #         self.get_help()
        # elif key == keyboard.KeyCode.from_char('c'):
        #     # 狗叫
        #     info = input('输入：')
        #     self.send_bark(info)


    # def keyboard_listening(self):
    #     '''
    #     按键监听
    #     '''
    #     with keyboard.Listener(on_press = self.on_press) as listener:
    #         listener.join()


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


    def print_leftcards(self, l):
        '''
        漂亮打印被打掉的牌面信息
        '''
        l.sort()
        c = Counter(l)
        maj_map = {'筒子': [], '条子': [], '万字': [], '字牌': []}
        for k, v in c.items():
            if k[1] == '筒':
                maj_map['筒子'].append((k, v))
            elif k[1] == '条':
                maj_map['条子'].append((k, v))
            elif k[1] == '万':
                maj_map['万字'].append((k, v))
            else:
                maj_map['字牌'].append((k, v))
        pprint(maj_map)


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


    def send_bark(self, info):
        msg = (self.uniq_id + ',' + info).encode()
        self.client.publish('bark', payload = msg)


    # 发送加入请求
    def send_join(self):
        msg = (self.name + ',' + self.uniq_id + ',' + self.ip).encode()
        self.client.publish('join', payload = msg)


    def send_throwcard(self, ind):
        msg = (self.uniq_id + ',' + str(ind)).encode()
        self.client.publish('throwcard', payload = msg)


    def send_peng(self, ifpeng, cptype):
        msg = (self.uniq_id + ',' + ifpeng + ',' + cptype).encode()
        self.client.publish('peng', payload = msg)


    def send_chigang(self, ifchigang, cptype):
        msg = (self.uniq_id + ',' + ifchigang + ',' + cptype).encode()
        self.client.publish('chigang', payload = msg)


    def send_bugang(self, ifbugang):
        msg = (self.uniq_id + ',' + ifbugang).encode()
        self.client.publish('bugang', payload = msg)


    def send_angang(self, ifangang):
        msg = (self.uniq_id + ',' + ifangang).encode()
        self.client.publish('angang', payload = msg)


    def send_zimo(self, ifzimo):
        msg = (self.uniq_id + ',' + ifzimo).encode()
        self.client.publish('zimo', payload = msg)


    def send_dianpao(self, ifdianpao):
        msg = (self.uniq_id + ',' + ifdianpao).encode()
        self.client.publish('dianpao', payload = msg)


    def send_chigang_peng(self, flag, cptype):
        msg = (self.uniq_id + ',' + flag + ',' + cptype).encode()
        self.client.publish('chigang_peng', payload = msg)


    def send_dianpao_peng(self, flag, cptype):
        msg = (self.uniq_id + ',' + flag + ',' + cptype).encode()
        self.client.publish('dianpao_peng', payload = msg)


    def send_dianpao_chigang(self, flag, cptype):
        msg = (self.uniq_id + ',' + flag + ',' + cptype).encode()
        self.client.publish('dianpao_chigang', payload = msg)


    def send_dianpao_chigang_peng(self, flag, cptype):
        msg = (self.uniq_id + ',' + flag + ',' + cptype).encode()
        self.client.publish('dianpao_chigang_peng', payload = msg)


    def receive(self):
        # 订阅玩家狗叫信息
        self.client.subscribe(self.uniq_id + '.barkinfo', callback = self.handle_barkinfo)
        # 订阅加入消息
        self.client.subscribe(self.uniq_id + '.isjoin', callback = self.handle_isjoin)
        # 订阅游戏开始消息
        self.client.subscribe('startgame', callback = self.handle_startgame)
        # 订阅更新卡牌消息
        self.client.subscribe(self.uniq_id + '.cardsinfo', callback = self.handle_cardsinfo)
        # 订阅打印手牌消息
        self.client.subscribe(self.uniq_id + '.showmycards', callback = self.handle_showmycards)
        # 订阅可否打牌消息
        self.client.subscribe(self.uniq_id + '.throwcard', callback = self.handle_throwcard)
        # 订阅打牌消息
        self.client.subscribe(self.uniq_id + '.throwcardinfo', callback = self.throwcardinfo)
        # 订阅摸牌消息
        self.client.subscribe(self.uniq_id + '.getcard', callback = self.handle_getcard)
        # 订阅可否碰牌消息
        self.client.subscribe(self.uniq_id + '.peng', callback = self.handle_peng)
        # 订阅碰牌消息
        self.client.subscribe(self.uniq_id + '.penginfo', callback = self.handle_penginfo)
        # 订阅是否吃杠消息
        self.client.subscribe(self.uniq_id + '.chigang', callback = self.handle_chigang)
        # 订阅吃杠消息
        self.client.subscribe(self.uniq_id + '.chiganginfo', callback = self.handle_chiganginfo)
        # 订阅是否补杠消息
        self.client.subscribe(self.uniq_id + '.bugang', callback = self.handle_bugang)
        # 订阅补杠消息
        self.client.subscribe(self.uniq_id + '.buganginfo', callback = self.handle_buganginfo)
        # 订阅是否暗杠消息
        self.client.subscribe(self.uniq_id + '.angang', callback = self.handle_angang)
        # 订阅暗杠消息
        self.client.subscribe(self.uniq_id + '.anganginfo', callback = self.handle_anganginfo)
        # 订阅自摸消息
        self.client.subscribe(self.uniq_id + '.zimo', callback = self.handle_zimo)
        # 订阅胡牌牌面信息
        self.client.subscribe(self.uniq_id + '.showhucards', callback = self.handle_showhucards)
        # 订阅点炮消息
        self.client.subscribe(self.uniq_id + '.dianpao', callback = self.handle_dianpao)
        # 订阅点炮牌面信息
        self.client.subscribe(self.uniq_id + '.showdianpaocards', callback = self.handle_showdianpaocards)
        # 订阅吃杠/碰消息
        self.client.subscribe(self.uniq_id + '.chigang_peng', callback = self.handle_chigang_peng)
        # 订阅点炮/碰消息
        self.client.subscribe(self.uniq_id + '.dianpao_peng', callback = self.handle_dianpao_peng)
        # 订阅点炮/吃杠消息
        self.client.subscribe(self.uniq_id + '.dianpao_chigang', callback = self.handle_dianpao_chigang)
        # 订阅点炮/吃杠/碰消息
        self.client.subscribe(self.uniq_id + '.dianpao_chigang_peng', callback = self.handle_dianpao_chigang_peng)
        # 订阅游戏结束消息
        self.client.subscribe(self.uniq_id + '.gameover', callback = self.handle_gameover)
        self.client.wait()


    def handle_barkinfo(self, msg):
        id, info = msg.payload.decode().split(',')
        print(id+'号：'+info)


    def handle_isjoin(self, msg):
        msg = msg.payload.decode()
        print(msg)
        if msg == '欢迎加入对局！':
            print('输入时输入 h 或 help 可查看帮助文档')
            self.isjoin = True
            print('正在等待其他玩家加入对局。。。')
            sleep(1)
        else:
            print('hhhh')
            self.disconnect()


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
            # print(self.hand_cards)
            self.print_playercards(self.pg_cards, self.hand_cards)


    def handle_throwcard(self, msg):
        msg = msg.payload.decode()
        if msg == 'throwcard':
            while True:
                inp = input('输入: ')
                # 考虑玩家非法输入
                try:
                    inp = int(inp)
                except:
                    if inp == 'x':  # 打掉花牌
                        break
                    elif inp == 'v':    # 查看其他牌面信息
                        print('\n牌堆剩余：' + str(self.tablecards_num))
                        for id, pgcards in self.otherplayers_cards:
                            print(str(id) + '号玩家：', pgcards)
                        print('牌面：')
                        self.print_leftcards(self.leftcards)
                        print()
                    elif inp in ('h','H','help','Help','HELP'):
                        self.get_help()
                    else:
                        self.send_bark(inp)
                else:
                    l = self.get_handcards_num()
                    if 0 < inp <= l:
                        inp -= 1
                        break
                    elif -l <= inp < 0:
                        break
                    else:
                        print('输入有误，请重新输入！')
            self.send_throwcard(inp)


    def throwcardinfo(self, msg):
        msg = msg.payload.decode()
        print(msg)


    def handle_getcard(self, msg):
        msg = msg.payload.decode()
        print('摸到牌：', msg)


    def handle_peng(self, msg):
        cptype = msg.payload.decode()
        while True:
            ifpeng = input('碰？(输入y/n) ')
            if ifpeng in ('y', 'n', 'Y', 'N'):
                break
        self.send_peng(ifpeng, cptype)


    def handle_penginfo(self, msg):
        msg = msg.payload.decode()
        print(msg)


    def handle_chigang(self, msg):
        cptype = msg.payload.decode()
        while True:
            ifchigang = input('杠？(输入y/n) ')
            if ifchigang in ('y', 'n', 'Y', 'N'):
                break
        self.send_chigang(ifchigang, cptype)


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


    def handle_zimo(self, msg):
        hu_kind = msg.payload.decode()
        while True:
            ifzimo = input('自摸'+hu_kind+'？(输入y/n) ')
            if ifzimo in ('y', 'n', 'Y', 'N'):
                break
        self.send_zimo(ifzimo)


    def handle_showhucards(self, msg):
        msg = msg.payload.decode()
        id, handcards, pgcards, hu_kind = json.loads(msg)
        print(hu_kind+'!\n'+id+'号自摸了！\n胡牌牌面信息：')
        self.print_playercards(pgcards, handcards)


    def handle_dianpao(self, msg):
        hu_kind = msg.payload.decode()
        while True:
            ifdianpao = input('点炮'+hu_kind+'？(输入y/n) ')
            if ifdianpao in ('y', 'n', 'Y', 'N'):
                break
        self.send_dianpao(ifdianpao)


    def handle_showdianpaocards(self, msg):
        msg = msg.payload.decode()
        id, handcards, pgcards, hu_kind = json.loads(msg)
        print(hu_kind+'!\n'+id + '号点炮了！\n胡牌牌面信息：')
        self.print_playercards(pgcards, handcards)


    def handle_chigang_peng(self, msg):
        print('receive chigang_peng')
        cptype = msg.payload.decode()
        while True:
            flag = input('杠/碰/no？(输入1/2/n) ')
            if flag in ('1','2', 'n', 'N'):
                break
        self.send_chigang_peng(flag, cptype)


    def handle_dianpao_peng(self, msg):
        cptype = msg.payload.decode()
        while True:
            flag = input('点炮/碰/no？(输入1/2/n) ')
            if flag in ('1','2', 'n', 'N'):
                break
        self.send_dianpao_peng(flag, cptype)


    def handle_dianpao_chigang(self, msg):
        cptype = msg.payload.decode()
        while True:
            flag = input('点炮/杠/no？(输入1/2/n) ')
            if flag in ('1','2', 'n', 'N'):
                break
        self.send_dianpao_chigang(flag, cptype)


    def handle_dianpao_chigang_peng(self, msg):
        cptype = msg.payload.decode()
        while True:
            flag = input('点炮/杠/碰/no？(输入1/2/3/n) ')
            if flag in ('1','2', '3', 'n', 'N'):
                break
        self.send_dianpao_chigang_peng(flag, cptype)


    def handle_gameover(self, msg):
        msg = msg.payload.decode()
        print(msg)


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
    # print('filename:', filename)
    c = Client()
    with open(filename + '_clientInfo.txt', 'w', encoding = 'utf-8') as f:
        f.write(c.name + ',' + c.uniq_id)

    ip = input('输入目标ip：')
    if ip != 'n':
        c.set_natsaddr(ip)
    c.connect()

    try:
        c.send_join()
        # keyboard_thread = Thread(target = c.keyboard_listening)
        # keyboard_thread.start()
        c.receive()
    except:
        print_exc()


if __name__ == '__main__':
    # print(path.abspath(__file__))
    curpath = path.abspath(__file__)
    try:
        start(curpath)
    except:
        print_exc()
        sleep(30)
    # rejoin(curpath)   #   如果断线了运行此命令
