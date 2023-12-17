import sys

from pynats import NATSClient

from os import path
import sys
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from app.base import Mahjong, Player
from app.utils import *
import json
from copy import deepcopy
from time import sleep
from app.config import KIND_VALUE_MAP, HAIDILAOYUE, TIANHU, DIHU, MINGGANG


class GameServer:
    def __init__(self, server_id, players, uniqid_players_map, id_players_map):
        self.server_id = server_id
        self.nats_addr = "nats://localhost:4222"
        self.connect()
        self.maj = Mahjong()
        self.table_cards = self.maj.shuffle_cards()  # 未被使用的牌堆
        self.left_cards = []  # 被打掉的牌堆
        self.players = players
        self.kind = len(players)  # 游戏类型（双人、三人、四人等）
        self.last_leftcard = None
        self.peng_type = None  # 碰的牌的类型
        self.chigang_type = None
        self.bugang_card = None  # 补杠摸到的那张牌
        self.bugang_type = None
        self.angang_card = None  # 暗杠摸到的那张牌
        self.angang_type = None
        self.curplayer_id = 1  # 当前轮到摸牌的玩家id
        self.hdly = '0' # 海底捞月
        self.gangbao = False    # 杠爆
        self.bugang_player = None
        self.uniqid_players_map = uniqid_players_map  # uniq_id与玩家的映射
        self.id_players_map = id_players_map  # id与玩家的映射
        self.action_map = {'001': self.send_peng,
                           '100': self.send_dianpao,
                           '011': self.send_chigang_peng,
                           '101': self.send_dianpao_peng,
                           '111': self.send_dianpao_chigang_peng}
        self.subscribe()


    def connect(self):
        self.client = NATSClient(self.nats_addr)
        self.client.connect()


    def disconnect(self):
        self.client.close()


    def reset(self):
        self.maj = Mahjong()
        self.table_cards = self.maj.shuffle_cards()  # 未被使用的牌堆
        # self.table_cards = ['6万']*50
        self.left_cards = []  # 被打掉的牌堆
        self.last_leftcard = None
        self.peng_type = None  # 碰的牌的类型
        self.chigang_type = None
        self.bugang_card = None  # 补杠摸到的那张牌
        self.bugang_type = None
        self.angang_card = None  # 暗杠摸到的那张牌
        self.angang_type = None
        self.curplayer_id = 1  # 当前轮到摸牌的玩家id
        self.hdly = '0'
        self.gangbao = False
        self.bugang_player = None
        for p in self.players:
            p.hand_cards = {'筒': [], '条': [], '万': [], '字': [], '花': []}
            p.pg_cards = {'viewable':[],'unviewable':[]}  # 碰、杠后的手牌
            p.pg_num = 0  # 碰、杠的次数
            p.angang_num = 0  # 暗杠的次数
            p.money_gang = 0
            p.hu_kinds = None  # 胡牌类型
            p.first_getcard = True
            p.dianpaoable = False
            p.dianpao = -1
            p.qgh = False
            self.send_cardsinfo(p)


    def distribute_cards(self):
        '''
        发牌
        '''
        for i in range(3):
            for player in self.players:
                for j in range(4):
                    card = self.table_cards.pop(0)
                    type = player.judge_card_type(card)
                    player.hand_cards[type].append(card)
        for j, player in enumerate(self.players):
            if not j:
                for k in range(2):
                    card = self.table_cards.pop(0)
                    type = player.judge_card_type(card)
                    player.hand_cards[type].append(card)
            else:
                card = self.table_cards.pop(0)
                type = player.judge_card_type(card)
                player.hand_cards[type].append(card)

        # 发完后洗牌（给牌排序）
        for player in self.players:
            for v in player.hand_cards.values():
                v.sort()

        return [player.hand_cards for player in self.players]


    def send_cardsinfo(self, player):
        '''
        每次操作都要给玩家发送更新卡牌信息
        '''
        mycards = [player.hand_cards, player.pg_cards, player.money, player.money_gang]
        otherplayers_cards = []
        for p in self.players:
            if p != player:
                otherplayers_cards.append([p.id, p.pg_cards, p.money, p.money_gang])
        tablecards_num = len(self.table_cards)
        leftcards = self.left_cards
        cardsinfo = [mycards, otherplayers_cards, tablecards_num, leftcards]
        self.client.publish(player.uniq_id + '.cardsinfo', payload = json.dumps(cardsinfo).encode())


    def send_showmycards(self, player):
        '''
        给玩家发送消息让玩家打印自己的手牌信息
        '''
        print(player.uniq_id)
        self.client.publish(player.uniq_id + '.showmycards', payload = 'showmycards'.encode())


    def send_throwcard(self, player):
        '''
        向玩家发送可以打牌的消息
        '''
        print('send_throwcard')
        self.client.publish(player.uniq_id + '.throwcard', payload = 'throwcard'.encode())


    def send_getcard(self, player, card):
        '''
        向玩家发送摸牌消息
        '''
        self.client.publish(player.uniq_id + '.getcard', payload = self.maj.cards_map[card].encode())


    def send_throwcardinfo(self, player, player2, card):
        '''
        向玩家发送打掉的牌的信息
        '''
        msg = str(player2.id) + '号打掉：' + self.maj.cards_map[card]
        self.client.publish(player.uniq_id + '.throwcardinfo', payload = msg.encode())


    def send_peng(self, player, cptype):
        '''
        向玩家发送可以碰牌的消息
        '''
        print('send_peng:', cptype, player.uniq_id)
        self.client.publish(player.uniq_id + '.peng', payload = cptype.encode())


    def send_penginfo(self, player1, player2, card):
        msg = str(player2.id) + '号碰掉了：' + self.maj.cards_map[card]
        self.client.publish(player1.uniq_id + '.penginfo', payload = msg.encode())


    def send_bugang(self, player):
        '''
        向玩家发送可以补杠的消息
        '''
        print('send_bugang')
        self.client.publish(player.uniq_id + '.bugang', payload = '可补杠'.encode())


    def send_buganginfo(self, player1, player2, card):
        msg = str(player2.id) + '号补杠：' + self.maj.cards_map[card]
        self.client.publish(player1.uniq_id + '.buganginfo', payload = msg.encode())


    def send_angang(self, player):
        '''
        向玩家发送可以暗杠的消息
        '''
        print('send_angang')
        self.client.publish(player.uniq_id + '.angang', payload = '可暗杠'.encode())


    def send_anganginfo(self, player1, player2):
        msg = str(player2.id) + '号暗杠！'
        self.client.publish(player1.uniq_id + '.anganginfo', payload = msg.encode())


    def send_zimo(self, player, hdly = '0'):
        '''
        向玩家发送可以自摸的消息
        '''
        msg = ','.join(player.hu_kinds) + ',' + hdly
        self.client.publish(player.uniq_id + '.zimo', payload = msg.encode())


    def send_showhucards(self, p, player, hdly = '0'):
        id, handcards, pgcards, hu_kinds = player.id, player.hand_cards, player.pg_cards, player.hu_kinds
        msg = [str(id), handcards, pgcards, player.hu_kinds, hdly]
        self.client.publish(p.uniq_id + '.showhucards', payload = json.dumps(msg).encode())


    def send_dianpao(self, player, *args):
        '''
        向玩家发送可以点炮的消息
        '''
        msg = ','.join(player.hu_kinds) + ',' + str(player.qgh)
        self.client.publish(player.uniq_id + '.dianpao', payload = msg.encode())


    def send_showdianpaocards(self, p, player):
        id, handcards, pgcards, hu_kinds = player.id, player.hand_cards, player.pg_cards, player.hu_kinds
        msg = [str(id), handcards, pgcards, hu_kinds, player.qgh]
        self.client.publish(p.uniq_id + '.showdianpaocards', payload = json.dumps(msg).encode())


    def send_barkinfo(self, player, msg):
        '''
        广播玩家狗叫信息
        '''
        self.client.publish(player.uniq_id + '.barkinfo', payload = msg.encode())


    def send_chigang_peng(self, player, cptype):
        '''
        向玩家发送可吃杠可碰的消息
        '''
        print('send_chigang_peng')
        self.client.publish(player.uniq_id + '.chigang_peng', payload = cptype.encode())


    def send_chiganginfo(self, player1, player2, card):
        msg = str(player2.id) + '号杠掉了：' + self.maj.cards_map[card]
        self.client.publish(player1.uniq_id + '.chiganginfo', payload = msg.encode())


    def send_dianpao_peng(self, player, cptype):
        '''
        向玩家发送可点炮可碰的消息
        '''
        print('send_dianpao_peng')
        self.client.publish(player.uniq_id + '.dianpao_peng', payload = cptype.encode())


    def send_dianpao_chigang_peng(self, player, cptype):
        '''
        向玩家发送可点炮可吃杠可碰的消息
        '''
        print('send_dianpao_chigang_peng')
        self.client.publish(player.uniq_id + '.dianpao_chigang_peng', payload = cptype.encode())


    def send_tianhu(self, player):
        self.client.publish(player.uniq_id + '.tianhu', payload = '天胡'.encode())


    def send_dihu(self, player):
        self.client.publish(player.uniq_id + '.dihu', payload = '地胡'.encode())


    def send_gameover(self, player, msg):
        self.client.publish(player.uniq_id + '.gameover', payload = msg.encode())


    def send_serverid(self, player, msg):
        self.client.publish(player.uniq_id + '.serverid', payload = msg.encode())


    def send_leftmoney(self, player):
        '''
        结算剩余筹码
        '''
        self.client.publish(player.uniq_id + '.leftmoney', payload = str(player.money).encode())


    def tianhu_dihu(self, curplayer, kind, func):
        curplayer.money += (kind + self.count_hukinds_value(curplayer.hu_kinds)) * (len(self.players) - 1)
        for p in self.players:
            if p != curplayer:
                p.money -= (kind + self.count_hukinds_value(curplayer.hu_kinds))
            func(p)
            self.send_showhucards(p, curplayer)
            self.send_leftmoney(p)
        sleep(10)
        self.init_start()


    def init_start(self):
        '''
        初始开始游戏
        '''
        print('init_start')
        for player in self.players:
            self.send_serverid(player, str(self.server_id))
        self.reset()
        self.distribute_cards()  # 发牌

        self.table_cards=[18,6,31,31]
        p1,p2 = self.players
        p1.hand_cards = {'筒': [1,2,2,3,4,4,5,7,], '条': [13,13,17,17,18], '万': [23],
                  '字': [], '花': []}
        p2.hand_cards = {'筒': [3,3,4,4], '条': [],'万': [], '字': [], '花': []}
        p2.pg_cards = {'viewable':[-2,-2,6,6,6,11,11,11,11,24,24,24,24], 'unviewable':[]}

        # self.table_cards=['7条','5万','东风','8条','8条','6筒','东风','8条','西风','西风',]
        # p1,p2,p3 = self.players
        # p1.hand_cards = {'筒子': ['2筒','2筒','3筒','3筒','4筒','4筒','5筒','6筒','7筒'], '条子': ['7条', '7条', '8条'], '万字': [],
        #           '字牌': ['东风','东风'], '花牌': []}
        # p2.hand_cards = {'筒子': ['3筒','3筒'], '条子': ['8条', '8条',],'万字': ['5万','5万','5万','6万'], '字牌': ['发财','发财','西风','西风', '东风'], '花牌': []}

        #
        # p3.hand_cards = {'筒子': [],
        #           '条子': ['1条', '2条', '3条', '4条', '5条','6条', '7条', '9条'], '万字': [], '字牌': ['东风','东风', '北风', '北风', '北风'], '花牌': []}
        for p in self.players:  # 给每个对局中的玩家发送卡牌信息
            self.send_cardsinfo(p)
            self.send_showmycards(p)

        curplayer = self.id_players_map[self.curplayer_id]  # 轮到打牌的玩家
        # 开局天胡
        if not curplayer.hand_cards['花']:
            hu_return = curplayer.is_hu(curplayer.hand_cards)
            if hu_return:
                if hu_return != True:
                    curplayer.hu_kinds = hu_return
                else:
                    curplayer.hu_kinds = curplayer.kind_check(curplayer.hand_cards, curplayer.pg_cards, curplayer.angang_num)
                self.tianhu_dihu(curplayer, TIANHU, self.send_tianhu)
                return

        # 开局暗杠
        angang_return = curplayer.is_angang()
        if angang_return:
            self.angang_type, self.angang_card = angang_return
            self.send_angang(curplayer)
            return

        self.send_throwcard(curplayer)


    def handle_startserver(self, msg):
        msg = msg.payload.decode()
        self.init_start()


    def handle_bark(self, msg):
        '''
        处理玩家狗叫信息
        '''
        uniq_id, info = msg.payload.decode().split('./?,*')
        bark_player = self.uniqid_players_map[uniq_id]
        print(str(bark_player.id) + '号:' + info)
        msg = str(bark_player.id) + './?,*' + info
        for p in self.players:
            if p != bark_player:
                self.send_barkinfo(p, msg)


    def handle_getcard(self, id, bg = False, cg = False):
        '''
        处理摸牌操作
        '''
        print('get in handle_getcard')
        self.curplayer_id = id
        curplayer = self.id_players_map[self.curplayer_id]

        type, card = curplayer.get_card(self.table_cards)
        if type == 'empty':
            msg = '流局！一群草包。'
            for p in self.players:
                self.send_gameover(p, msg)
            self.init_start()
            return
        self.send_getcard(curplayer, card)
        self.send_cardsinfo(curplayer)  # 摸牌后给该玩家发送牌面信息
        self.send_showmycards(curplayer)

        bugang_return = curplayer.is_bugang(card)
        angang_return = curplayer.is_angang()
        hu_return = False
        if not curplayer.hand_cards['花']:
            hu_return = curplayer.is_hu(curplayer.hand_cards)
            if hu_return:
                if hu_return != True:
                    curplayer.hu_kinds = hu_return
                else:
                    curplayer.hu_kinds = curplayer.kind_check(curplayer.hand_cards, curplayer.pg_cards, curplayer.angang_num)
                if bg:  # 补杠
                    curplayer.hu_kinds.append('杠上开花')
                if cg:  # 吃杠
                    self.gangbao = True
                    curplayer.hu_kinds.append('杠爆')

                # 地胡
                if curplayer.first_getcard:
                    self.tianhu_dihu(curplayer, DIHU, self.send_dihu)
                    return

                if not self.table_cards:
                    self.hdly = '1'
                self.send_zimo(curplayer, self.hdly)
                return

        if bugang_return:
            self.bugang_card = card
            self.bugang_type = bugang_return
            self.send_bugang(curplayer)
            return
        if angang_return:
            self.angang_type, self.angang_card = angang_return
            self.send_angang(curplayer)
            return

        if not bugang_return and not angang_return and not hu_return:
            self.send_throwcard(curplayer)


    def handle_throwcard(self, msg):
        '''
        处理玩家打牌操作
        '''
        print('get in handle_throwcard')
        uniq_id, ind = msg.payload.decode().split(',')
        player = self.uniqid_players_map[uniq_id]
        player.first_getcard = False

        # 正常下标
        if ind != 'x':
            leftcard = player.throw_card(self.left_cards, int(ind))
            self.last_leftcard = LastLeftCard(player, leftcard)

            for p in self.players:
                self.send_throwcardinfo(p, player, leftcard)
                self.send_cardsinfo(p)  # 打牌后给每个玩家更新牌面信息
                if p == player:
                    self.send_showmycards(player)

            self.players_action = dict(zip(self.players, [['000', None] for i in range(len(self.players))]))   # '000'分别代表点炮与否、吃杠与否、碰与否
            for p in self.players:
                if self.last_leftcard.player != p:
                    lastcard = self.last_leftcard.card
                    card_type = p.judge_card_type(lastcard)
                    tmp_handcards = deepcopy(p.hand_cards)
                    tmp_handcards[card_type].append(lastcard)
                    tmp_handcards[card_type].sort()

                    if not tmp_handcards['花']:
                        hu_return = p.is_hu(tmp_handcards)
                        print('hu_return:', hu_return)
                        if hu_return:
                            if hu_return != True:
                                p.hu_kinds = hu_return
                            else:
                                p.hu_kinds = p.kind_check(tmp_handcards, p.pg_cards, p.angang_num, lastcard)
                            print('hu_kinds:',p.hu_kinds)
                            if p.hu_kinds != ['鸡胡']:
                                p.dianpaoable = True
                                self.players_action[p][0] = '1' + self.players_action[p][0][1:]

                    cp_type = p.is_peng(self.last_leftcard)
                    if cp_type:
                        self.players_action[p][0] = self.players_action[p][0][:2] + '1'
                        self.players_action[p][1] = cp_type

                    cp_type = p.is_chigang(self.last_leftcard)
                    if cp_type:
                        self.players_action[p][0] = self.players_action[p][0][0] + '1' + self.players_action[p][0][2]
                        self.players_action[p][1] = cp_type

            print(self.players_action.values())
            # 无碰无杠无点炮则轮到下一个玩家
            if all(i[0]=='000' for i in self.players_action.values()):
                tmp = (self.curplayer_id + 1) % self.kind
                id = tmp if tmp else self.kind
                self.handle_getcard(id)
            else:
                if all(i[0][0] == '0' for i in self.players_action.values()):
                    for p, (action, cptype) in self.players_action.items():
                        if action != '000':
                            self.action_map[action](p, cptype)
                else:   # 有人可点炮
                    if sum([i[0][0] == '1' for i in self.players_action.values()]) == 1:    # 仅一人可点炮/碰/杠
                        for p, (action, cptype) in self.players_action.items():
                            if action[0] == '1':
                                self.action_map[action](p, cptype)
                    else:
                        for p, (action, cptype) in self.players_action.items():
                            if action == '100':
                                self.action_map[action](p, cptype)
        # 花牌
        else:
            player.pg_cards['viewable'].extend(player.hand_cards['花'])
            hp_num = len(player.hand_cards['花'])
            player.hand_cards['花'] = []
            # 摸hp_num张牌
            for i in range(hp_num):
                type, card = player.get_card(self.table_cards)
                self.send_getcard(player, card)
            self.send_cardsinfo(player)
            self.send_showmycards(player)
            self.send_throwcard(player)


    def update_info(self, player, func, card = None):
        for p in self.players:
            if p.id != player.id:
                if card:
                    func(p, player, card)
                else:
                    func(p, player)
            self.send_cardsinfo(p)
        self.send_showmycards(player)


    def handle_peng(self, msg):
        '''
        处理玩家碰牌请求
        '''
        print('get in handle_peng')
        uniq_id, ifpeng, cptype = msg.payload.decode().split(',')
        player = self.uniqid_players_map[uniq_id]
        if ifpeng in ('y', 'Y'):  # 碰了要打掉一张
            # 更新牌面信息
            player.peng(self.last_leftcard, self.left_cards, cptype)
            self.update_info(player, self.send_penginfo, self.last_leftcard.card)
            self.curplayer_id = player.id
            # 给玩家发送打牌消息
            self.send_throwcard(player)
        elif ifpeng in ('n', 'N'):  # 不碰则发牌给下一个玩家
            tmp = (self.curplayer_id + 1) % self.kind
            id = tmp if tmp else self.kind
            self.handle_getcard(id)


    def qianggang_hu(self, player):
        '''
        抢杠胡
        '''
        flag = False
        for p in self.players:
            if p != player:
                tmp_handcards = deepcopy(p.hand_cards)
                tmp_handcards[self.bugang_type].append(self.bugang_card)
                tmp_handcards[self.bugang_type].sort()

                if not tmp_handcards['花']:
                    hu_return = p.is_hu(tmp_handcards)
                    if hu_return:
                        flag = True
                        p.dianpaoable = True
                        p.qgh = True
                        if hu_return != True:
                            p.hu_kinds = hu_return
                        else:
                            p.hu_kinds = p.kind_check(tmp_handcards, p.pg_cards, p.angang_num, self.bugang_card)
                        self.send_dianpao(p)
        return flag


    def handle_bugang(self, msg):
        '''
        处理玩家补杠请求
        '''
        print('get in handle_bugang')
        uniq_id, ifbugang = msg.payload.decode().split(',')
        player = self.uniqid_players_map[uniq_id]
        if ifbugang in ('y', 'Y'):  # 杠了要摸一张再打掉一张
            # 更新牌面信息
            player.bugang(self.bugang_card, self.bugang_type, self.players)
            self.bugang_player = player
            self.update_info(player, self.send_buganginfo, self.bugang_card)
            # 判断是否有人可以抢杠胡
            if not self.qianggang_hu(player):
                # 摸一张
                self.handle_getcard(self.curplayer_id, bg = True)
        elif ifbugang in ('n', 'N'):  # 不杠则打掉一张
            self.send_throwcard(player)


    def handle_angang(self, msg):
        '''
        处理玩家暗杠请求
        '''
        print('get in handle_angang')
        uniq_id, ifangang = msg.payload.decode().split(',')
        player = self.uniqid_players_map[uniq_id]
        if ifangang in ('y', 'Y'):
            # 更新牌面信息
            player.angang(self.angang_card, self.angang_type, self.players)
            self.update_info(player, self.send_anganginfo)
            # 摸一张
            self.handle_getcard(self.curplayer_id)
        elif ifangang in ('n', 'N'):  # 不杠则打掉一张
            self.send_throwcard(player)


    def count_hukinds_value(self, kinds):
        money = 0
        for kind in kinds:
            money += KIND_VALUE_MAP[kind]
        return money


    def handle_zimo(self, msg):
        '''
        处理玩家自摸请求
        '''
        print('get in handle_zimo')
        uniq_id, ifzimo, hdly = msg.payload.decode().split(',')
        player = self.uniqid_players_map[uniq_id]
        if ifzimo in ('y', 'Y'):
            n = (len(self.players) - 1)
            money_hua = sum([i == -player.id for i in player.pg_cards['viewable']])
            player.money += (self.count_hukinds_value(player.hu_kinds) + HAIDILAOYUE[hdly] + money_hua) * n
            if self.gangbao:
                self.last_leftcard.player.money -= n * (self.count_hukinds_value(player.hu_kinds) + money_hua)
                for p in self.players:
                    p.money += p.money_gang
                    self.send_cardsinfo(p)
                    self.send_showhucards(p, player, hdly)
                    self.send_leftmoney(p)
            else:
                for p in self.players:
                    if p != player:
                        p.money -= (self.count_hukinds_value(player.hu_kinds) + HAIDILAOYUE[hdly] + money_hua)
                    p.money += p.money_gang
                    self.send_cardsinfo(p)
                    self.send_showhucards(p, player, hdly)
                    self.send_leftmoney(p)
            sleep(10)
            self.init_start()
            return
        elif ifzimo in ('n', 'N'):
            self.send_throwcard(player)


    def dianpao(self, player):
        print('qgh:', player.qgh)
        n = len(self.players) - 1
        money_hua = sum([i == -player.id for i in player.pg_cards['viewable']])
        if player.qgh:  # 抢杠胡被抢的人赔三家
            player.money += n * (self.count_hukinds_value(player.hu_kinds) + money_hua)
            for p in self.players:
                if p != self.bugang_player:
                    p.money += MINGGANG
            self.bugang_player.money -= n * (self.count_hukinds_value(player.hu_kinds) + MINGGANG + money_hua)
        else:
            player.money += (self.count_hukinds_value(player.hu_kinds) + money_hua)
            self.last_leftcard.player.money -= (self.count_hukinds_value(player.hu_kinds) + money_hua)
        for p in self.players:
            p.money += p.money_gang
            self.send_cardsinfo(p)
            self.send_showdianpaocards(p, player)
            self.send_leftmoney(p)

        if all(not i.dianpaoable or i.dianpaoable and i.dianpao != -1 for i in self.players):
            print('done')
            sleep(10)
            self.init_start()
        else:
            for p, (action, cptype) in self.players_action.items():
                if action in ('101', '111'):
                    self.action_map[action](p, cptype)


    def handle_dianpao(self, msg):
        '''
        处理玩家点炮请求，包含一个玩家可碰/吃杠/点炮，另外多个玩家可点炮的特殊情况
        '''
        print('get in handle_dianpao')
        uniq_id, ifdianpao = msg.payload.decode().split(',')
        player = self.uniqid_players_map[uniq_id]
        print(self.players_action.values())
        if ifdianpao in ('y', 'Y'):
            player.dianpao = 1
            self.dianpao(player)
            return
        elif ifdianpao in ('n', 'N'):
            player.dianpao = 0
            for p in self.players:
                if p.dianpaoable and p.dianpao == -1:
                    break
            else:
                for p, (action, cptype) in self.players_action.items():
                    if p != player and (action[1]=='1' or action[2]=='1'):
                        self.action_map[action](p, cptype)
                        break
                else:
                    tmp = (self.curplayer_id + 1) % self.kind
                    id = tmp if tmp else self.kind
                    id = self.curplayer_id if player.qgh else id
                    self.handle_getcard(id)


    def handle_chigang_peng(self, msg):
        '''
        处理玩家吃杠/碰请求
        '''
        print('get in handle_chigang_peng')
        uniq_id, flag, cptype = msg.payload.decode().split(',')
        player = self.uniqid_players_map[uniq_id]

        if flag == '1':  # 吃杠
            player.chigang(self.last_leftcard, self.left_cards, cptype, self.players)
            self.update_info(player, self.send_chiganginfo, self.last_leftcard.card)
            id = player.id
            self.handle_getcard(id, cg = True)
        elif flag == '2':  # 碰
            player.peng(self.last_leftcard, self.left_cards, cptype)
            self.update_info(player, self.send_penginfo, self.last_leftcard.card)
            self.curplayer_id = player.id
            # 给玩家发送打牌消息
            self.send_throwcard(player)
        elif flag in ('n', 'N'):
            tmp = (self.curplayer_id + 1) % self.kind
            id = tmp if tmp else self.kind
            self.handle_getcard(id)


    def handle_dianpao_peng(self, msg):
        '''
        处理玩家点炮/碰请求
        '''
        print('get in handle_dianpao_peng')
        uniq_id, flag, cptype = msg.payload.decode().split(',')
        player = self.uniqid_players_map[uniq_id]

        if flag == '1':  # 点炮
            player.dianpao = 1
            self.dianpao(player)
            return
        else:
            player.dianpao = 0
            if all(not i.dianpaoable or i.dianpaoable and i.dianpao == 0 for i in self.players):
                if flag == '2':
                    player.peng(self.last_leftcard, self.left_cards, cptype)
                    self.update_info(player, self.send_penginfo, self.last_leftcard.card)
                    self.curplayer_id = player.id
                    # 给玩家发送打牌消息
                    self.send_throwcard(player)
                elif flag ('n', 'N'):
                    tmp = (self.curplayer_id + 1) % self.kind
                    id = tmp if tmp else self.kind
                    self.handle_getcard(id)
            else:
                sleep(10)
                self.init_start()


    def handle_dianpao_chigang_peng(self, msg):
        '''
        处理玩家点炮/吃杠/碰请求
        '''
        print('get in handle_chigang_peng')
        uniq_id, flag, cptype = msg.payload.decode().split(',')
        player = self.uniqid_players_map[uniq_id]

        if flag == '1':  # 点炮
            player.dianpao = 1
            self.dianpao(player)
            return
        else:
            player.dianpao = 0
            if all(not i.dianpaoable or i.dianpaoable and i.dianpao == 0 for i in self.players):
                if flag == '2':
                    player.chigang(self.last_leftcard, self.left_cards, cptype, self.players)
                    self.update_info(player, self.send_chiganginfo, self.last_leftcard.card)
                    id = player.id
                    self.handle_getcard(id)
                elif flag == '3':  # 碰
                    player.peng(self.last_leftcard, self.left_cards, cptype)
                    self.update_info(player, self.send_penginfo, self.last_leftcard.card)
                    self.curplayer_id = player.id
                    # 给玩家发送打牌消息
                    self.send_throwcard(player)
                elif flag in ('n', 'N'):
                    tmp = (self.curplayer_id + 1) % self.kind
                    id = tmp if tmp else self.kind
                    self.handle_getcard(id)
            else:
                sleep(10)
                self.init_start()


    # 订阅消息
    def subscribe(self):
        # 订阅服务启动消息
        self.client.subscribe(str(self.server_id) + '.startserver', callback = self.handle_startserver)
        # 订阅狗叫消息
        self.client.subscribe(str(self.server_id) + ".bark", callback = self.handle_bark)
        # 订阅摸牌消息
        self.client.subscribe(str(self.server_id) + ".getcard", callback = self.handle_getcard)
        # 订阅打牌消息
        self.client.subscribe(str(self.server_id) + ".throwcard", callback = self.handle_throwcard)
        # 订阅碰牌消息
        self.client.subscribe(str(self.server_id) + ".peng", callback = self.handle_peng)
        # 订阅补杠消息
        self.client.subscribe(str(self.server_id) + ".bugang", callback = self.handle_bugang)
        # 订阅暗杠消息
        self.client.subscribe(str(self.server_id) + ".angang", callback = self.handle_angang)
        # 订阅自摸消息
        self.client.subscribe(str(self.server_id) + ".zimo", callback = self.handle_zimo)
        # 订阅点炮消息
        self.client.subscribe(str(self.server_id) + ".dianpao", callback = self.handle_dianpao)
        # 订阅吃杠/碰消息
        self.client.subscribe(str(self.server_id) + '.chigang_peng', callback = self.handle_chigang_peng)
        # 订阅点炮/碰消息
        self.client.subscribe(str(self.server_id) + '.dianpao_peng', callback = self.handle_dianpao_peng)
        # 订阅点炮/吃杠/碰消息
        self.client.subscribe(str(self.server_id) + '.dianpao_chigang_peng', callback = self.handle_dianpao_chigang_peng)
        self.client.wait()


if __name__=='__main__':
    p1 = Player('test1', 1)
    p2 = Player('test2', 2)
    players = [p1,p2]
    uniqid_players_map, id_players_map = dict(), dict()
    for i, player in enumerate(players):
        uniqid_players_map[player.uniq_id] = player
        player.id = i + 1
        id_players_map[i + 1] = player
    gs = GameServer(0, players, uniqid_players_map, id_players_map)
    cards = gs.distribute_cards()
    for i in cards:
        print(i)