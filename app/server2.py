from pynats import NATSClient
from app.base import Mahjong, Player
from app.utils import *
import json
from copy import deepcopy
from time import sleep


class GameServer:
    def __init__(self, server_id, players, uniqid_players_map, id_players_map):
        self.server_id = server_id
        self.nats_addr = "nats://localhost:4222"
        self.connect()
        self.maj = Mahjong()
        self.table_cards = self.maj.shuffle_cards()  # 未被使用的牌堆
        # self.table_cards = ['6万']*50
        self.left_cards = []  # 被打掉的牌堆
        self.players = players
        self.kind = 2  # 游戏类型（双人、三人、四人等）
        self.last_leftcard = None
        self.peng_type = None  # 碰的牌的类型
        self.chigang_type = None
        self.bugang_card = None  # 补杠摸到的那张牌
        self.bugang_type = None
        self.angang_card = None  # 暗杠摸到的那张牌
        self.angang_type = None
        self.curplayer_id = 1  # 当前轮到摸牌的玩家id
        self.uniqid_players_map = uniqid_players_map  # uniq_id与玩家的映射
        self.id_players_map = id_players_map  # id与玩家的映射
        for player in self.players:
            print(player.id)
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
        self.kind = 2  # 游戏类型（双人、三人、四人等）
        self.last_leftcard = None
        self.peng_type = None  # 碰的牌的类型
        self.chigang_type = None
        self.bugang_card = None  # 补杠摸到的那张牌
        self.bugang_type = None
        self.angang_card = None  # 暗杠摸到的那张牌
        self.angang_type = None
        self.curplayer_id = 1  # 当前轮到摸牌的玩家id

        for p in self.players:
            p.hand_cards = {'筒子': [], '条子': [], '万字': [], '字牌': [], '花牌': []}
            p.pg_cards = []  # 碰、杠后的手牌
            p.pg_num = 0  # 碰、杠的次数
            p.angang_num = 0  # 暗杠的次数
            p.hu_kind = None  # 胡牌类型
            p.first_getcard = True
            self.send_cardsinfo(p)


    def set_kind(self, x):
        self.kind = x


    def distribute_cards(self):
        '''
        发牌
        '''
        for i in range(4):
            if i < 3:
                for player in self.players:
                    for j in range(4):
                        insert_card(self.table_cards, player.hand_cards, self.maj.cards, self.maj.abb_map)
            else:
                for j, player in enumerate(self.players):
                    if not j:
                        for k in range(2):
                            insert_card(self.table_cards, player.hand_cards, self.maj.cards, self.maj.abb_map)
                    else:
                        insert_card(self.table_cards, player.hand_cards, self.maj.cards, self.maj.abb_map)

        # 发完后洗牌（给牌排序）
        for player in self.players:
            for v in player.hand_cards.values():
                v.sort()

        return [player.hand_cards for player in self.players]


    def send_cardsinfo(self, player):
        '''
        每次操作都要给玩家发送更新卡牌信息
        '''
        mycards = [player.hand_cards, player.pg_cards]
        otherplayers_cards = []
        for p in self.players:
            if p != player:
                otherplayers_cards.append([p.id, p.pg_cards])
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
        self.client.publish(player.uniq_id + '.getcard', payload = card.encode())


    def send_throwcardinfo(self, player, player2, card):
        '''
        向玩家发送打掉的牌的信息
        '''
        msg = str(player2.id) + '号打掉：' + card
        self.client.publish(player.uniq_id + '.throwcardinfo', payload = msg.encode())


    def send_peng(self, player, cptype):
        '''
        向玩家发送可以碰牌的消息
        '''
        print('send_peng:', cptype, player.uniq_id)
        self.client.publish(player.uniq_id + '.peng', payload = cptype.encode())


    def send_penginfo(self, player1, player2, card):
        msg = str(player2.id) + '号碰掉了：' + card
        self.client.publish(player1.uniq_id + '.penginfo', payload = msg.encode())


    def send_chigang(self, player, cptype):
        '''
        向玩家发送可以吃杠的消息
        '''
        print('send_chigang')
        self.client.publish(player.uniq_id + '.chigang', payload = cptype.encode())


    def send_chiganginfo(self, player1, player2, card):
        msg = str(player2.id) + '号杠掉了：' + card
        self.client.publish(player1.uniq_id + '.chiganginfo', payload = msg.encode())


    def send_bugang(self, player):
        '''
        向玩家发送可以补杠的消息
        '''
        print('send_bugang')
        self.client.publish(player.uniq_id + '.bugang', payload = '可补杠'.encode())


    def send_buganginfo(self, player1, player2, card):
        msg = str(player2.id) + '号补杠：' + card
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


    def send_zimo(self, player):
        '''
        向玩家发送可以自摸的消息
        '''
        self.client.publish(player.uniq_id + '.zimo', payload = player.hu_kind.encode())


    def send_showhucards(self, p, player):
        id, handcards, pgcards, hu_kind = player.id, player.hand_cards, player.pg_cards, player.hu_kind
        msg = [str(id), handcards, pgcards, player.hu_kind]
        self.client.publish(p.uniq_id + '.showhucards', payload = json.dumps(msg).encode())


    def send_dianpao(self, player):
        '''
        向玩家发送可以点炮的消息
        '''
        self.client.publish(player.uniq_id + '.dianpao', payload = player.hu_kind.encode())


    def send_showdianpaocards(self, p, player):
        id, handcards, pgcards, hu_kind = player.id, player.hand_cards, player.pg_cards, player.hu_kind
        msg = [str(id), handcards, pgcards, hu_kind]
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


    def send_dianpao_peng(self, player, cptype):
        '''
        向玩家发送可点炮可碰的消息
        '''
        print('send_dianpao_peng')
        self.client.publish(player.uniq_id + '.dianpao_peng', payload = cptype.encode())


    def send_dianpao_chigang(self, player, cptype):
        '''
        向玩家发送可点炮可吃杠的消息
        '''
        print('send_dianpao_chigang')
        self.client.publish(player.uniq_id + '.dianpao_chigang', payload = cptype.encode())


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


    def init_start(self):
        '''
        初始开始游戏
        '''
        print('init_start')
        for player in self.players:
            self.send_serverid(player, str(self.server_id))
        self.reset()
        self.distribute_cards()  # 发牌
        # self.table_cards[:3]=['东风','东风','西风']
        # p1,p2 = self.players
        # p1.hand_cards = {'筒子': [],
        #                  '条子': ['1条', '2条', '3条', '4条', '5条', '8条', '8条', '8条'], '万字': [],
        #                  '字牌': ['东风', '东风','东风', '红中', '红中', '红中'], '花牌': []}
        # p2.hand_cards = {'筒子': ['3筒','3筒', '3筒'], '条子': ['2条', '3条','4条'],'万字': ['5万','6万','7万'], '字牌': ['发财','发财','发财','西风'], '花牌': []}

        # p3.hand_cards = {'筒子': [],
        #           '条子': ['1条', '2条', '3条', '4条', '5条','6条', '7条', '9条'], '万字': [], '字牌': ['东风','东风', '北风', '北风', '北风'], '花牌': []}
        for p in self.players:  # 给每个对局中的玩家发送卡牌信息
            self.send_cardsinfo(p)
            self.send_showmycards(p)

        curplayer = self.id_players_map[self.curplayer_id]  # 轮到打牌的玩家
        print('curplayer id:', curplayer.id)
        # 开局天胡/暗杠
        if not curplayer.hand_cards['花牌']:
            if curplayer.is_hu(curplayer.hand_cards):
                curplayer.hu_kind = curplayer.kind_check(curplayer.hand_cards, curplayer.pg_cards, curplayer.angang_num)
                for p in self.players:
                    self.send_tianhu(p)
                    # self.send_cardsinfo(p)
                    self.send_showhucards(p, curplayer)
                sleep(10)
                self.init_start()
                return
        if curplayer.is_angang():
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


    # def handle_join(self, msg):
    #     '''
    #     处理玩家加入请求
    #     '''
    #     name, uniq_id, ip = msg.payload.decode().split(',')
    #     player = Player(name, uniq_id)
    #     print('target ip is: ', ip)
    #
    #     if len(self.players) < self.kind:
    #         player.id = max([p.id for p in self.players]) + 1 if self.players else 1
    #         self.players.append(player)
    #         self.uniqid_players_map[uniq_id] = player
    #         self.id_players_map[player.id] = player
    #
    #         print('第' + str(player.id) + '位玩家"' + player.name + '"加入对局！')
    #         self.send_isjoin(player, '欢迎加入对局！')
    #
    #         if len(self.players) == self.kind:  # 玩家数量达到，开始游戏
    #             self.init_start()
    #     else:
    #         print('已达最大玩家数量')
    #         self.send_isjoin(player, '已达最大玩家数量！')


    def handle_getcard(self, id):
        '''
        处理摸牌操作
        '''
        print('get in handle_getcard')
        self.curplayer_id = id
        print('curplayer_id:', self.curplayer_id)
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
        if not curplayer.hand_cards['花牌']:
            hu_return = curplayer.is_hu(curplayer.hand_cards)
            if hu_return:
                curplayer.hu_kind = curplayer.kind_check(curplayer.hand_cards, curplayer.pg_cards, curplayer.angang_num)
                if curplayer.first_getcard:
                    for p in self.players:
                        self.send_dihu(p)
                        self.send_showhucards(p, curplayer)
                    sleep(10)
                    self.init_start()
                self.send_zimo(curplayer)
                print('currrrrrrrrrr',curplayer.hand_cards)
                return
        curplayer.first_getcard = False

        print(bugang_return, angang_return, hu_return)

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
            print('????')
            self.send_throwcard(curplayer)


    def handle_throwcard(self, msg):
        '''
        处理玩家打牌操作
        '''
        print('get in handle_throwcard')
        uniq_id, ind = msg.payload.decode().split(',')
        player = self.uniqid_players_map[uniq_id]

        # 正常下标
        if ind != 'x':
            leftcard = player.throw_card(self.left_cards, int(ind))
            self.last_leftcard = LastLeftCard(player, leftcard)

            for p in self.players:
                print('ppppppppp', p.id)
                self.send_throwcardinfo(p, player, leftcard)
                self.send_cardsinfo(p)  # 打牌后给每个玩家更新牌面信息
                print('hhh',p.hand_cards)
                if p == player:
                    self.send_showmycards(player)

            one_flag = True  # 判断循环里是否出现过点炮/吃杠/碰
            for p in self.players:
                tmp_list = [0, 0, 0]  # 分别代表点炮与否、吃杠与否、碰与否
                if self.last_leftcard.player != p:
                    lastcard = self.last_leftcard.card
                    if lastcard[1] in self.maj.abb_map:
                        card_type = self.maj.abb_map[lastcard[1]]
                    else:
                        card_type = '字牌'
                    tmp_handcards = deepcopy(p.hand_cards)
                    tmp_handcards[card_type].append(lastcard)
                    tmp_handcards[card_type].sort()
                    print('carddddddd:',tmp_handcards, p.id)

                    if not tmp_handcards['花牌'] and p.is_hu(tmp_handcards):
                        p.hu_kind = p.kind_check(tmp_handcards, p.pg_cards, p.angang_num)
                        print(p.hu_kind)
                        if p.hu_kind != '鸡胡':
                            tmp_list[0] = 1

                    cp_type = p.is_chigang(self.last_leftcard)
                    if cp_type:
                        tmp_list[1] = 1

                    cp_type = p.is_peng(self.last_leftcard)
                    if cp_type:
                        tmp_list[2] = 1

                    if tmp_list == [0, 0, 1]:
                        self.send_peng(p, cp_type)
                    elif tmp_list == [0, 1, 0]:
                        self.send_chigang(p, cp_type)
                    elif tmp_list == [1, 0, 0]:
                        self.send_dianpao(p)
                    elif tmp_list == [0, 1, 1]:
                        self.send_chigang_peng(p, cp_type)
                    elif tmp_list == [1, 0, 1]:
                        self.send_dianpao_peng(p, cp_type)
                    elif tmp_list == [1, 1, 0]:
                        self.send_dianpao_chigang(p, cp_type)
                    elif tmp_list == [1, 1, 1]:
                        self.send_dianpao_chigang_peng(p, cp_type)
                    else:
                        one_flag = False
                    print('tmp_list:', tmp_list)

            # 无碰无杠无点炮则轮到下一个玩家
            if not one_flag:
                print('no peng no gang no dianpao')
                tmp = (self.curplayer_id + 1) % self.kind
                id = tmp if tmp else self.kind
                self.handle_getcard(id)
                print('222222222222', self.curplayer_id)
        # 花牌
        else:
            player.pg_cards.extend(player.hand_cards['花牌'])
            hp_num = len(player.hand_cards['花牌'])
            player.hand_cards['花牌'] = []
            # 摸hp_num张牌
            for i in range(hp_num):
                type, card = player.get_card(self.table_cards)
                self.send_getcard(player, card)
            self.send_cardsinfo(player)
            self.send_showmycards(player)
            self.send_throwcard(player)


    def handle_peng(self, msg):
        '''
        处理玩家碰牌请求
        '''
        print('get in handle_peng')
        uniq_id, ifpeng, cptype = msg.payload.decode().split(',')
        player = self.uniqid_players_map[uniq_id]
        print('ifpeng:', ifpeng)
        if ifpeng in ('y', 'Y'):  # 碰了要打掉一张
            # 更新牌面信息
            player.peng(self.last_leftcard, self.left_cards, cptype)
            for p in self.players:
                if p.id != player.id:
                    self.send_penginfo(p, player, self.last_leftcard.card)
                self.send_cardsinfo(p)
            self.send_showmycards(player)
            self.curplayer_id = player.id
            # 给玩家发送打牌消息
            self.send_throwcard(player)
        elif ifpeng in ('n', 'N'):  # 不碰则发牌给下一个玩家
            tmp = (self.curplayer_id + 1) % self.kind
            id = tmp if tmp else self.kind
            print('noooooooooooopeng', id)
            self.handle_getcard(id)


    def handle_chigang(self, msg):
        '''
        处理玩家吃杠请求
        '''
        print('get in handle_chigang')
        uniq_id, ifchigang, cptype = msg.payload.decode().split(',')
        player = self.uniqid_players_map[uniq_id]
        if ifchigang in ('y', 'Y'):  # 杠了要摸一张再打掉一张
            # 更新牌面信息
            player.chigang(self.last_leftcard, self.left_cards, cptype)
            for p in self.players:
                if p.id != player.id:
                    self.send_chiganginfo(p, player, self.last_leftcard.card)
                self.send_cardsinfo(p)
            self.send_showmycards(player)
            id = player.id
            self.handle_getcard(id)
            # self.curplayer_id = player.id
        elif ifchigang in ('n', 'N'):  # 不杠则发牌给下一个玩家
            tmp = (self.curplayer_id + 1) % self.kind
            id = tmp if tmp else self.kind
            self.handle_getcard(id)


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
            for p in self.players:
                print(p.money)
                if p.id != player.id:
                    self.send_buganginfo(p, player, self.bugang_card)
                self.send_cardsinfo(p)
            self.send_showmycards(player)
            # 摸一张
            self.handle_getcard(self.curplayer_id)
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
            for p in self.players:
                print(p.money)
                if p.id != player.id:
                    self.send_anganginfo(p, player)
                self.send_cardsinfo(p)
            self.send_showmycards(player)
            # 摸一张
            self.handle_getcard(self.curplayer_id)
        elif ifangang in ('n', 'N'):  # 不杠则打掉一张
            self.send_throwcard(player)


    def handle_zimo(self, msg):
        '''
        处理玩家自摸请求
        '''
        print('get in handle_zimo')
        uniq_id, ifzimo = msg.payload.decode().split(',')
        player = self.uniqid_players_map[uniq_id]
        print('zimooooooooooooooooooo',player.hand_cards)
        if ifzimo in ('y', 'Y'):
            for p in self.players:
                self.send_cardsinfo(p)
                self.send_showhucards(p, player)
            sleep(10)
            self.init_start()
        elif ifzimo in ('n', 'N'):
            self.send_throwcard(player)


    def handle_dianpao(self, msg):
        '''
        处理玩家点炮请求
        '''
        print('get in handle_dianpao')
        uniq_id, ifdianpao = msg.payload.decode().split(',')
        player = self.uniqid_players_map[uniq_id]
        if ifdianpao in ('y', 'Y'):
            for p in self.players:
                self.send_cardsinfo(p)
                self.send_showdianpaocards(p, player)
            sleep(10)
            self.init_start()
        elif ifdianpao in ('n', 'N'):
            tmp = (self.curplayer_id + 1) % self.kind
            id = tmp if tmp else self.kind
            self.handle_getcard(id)


    def handle_chigang_peng(self, msg):
        '''
        处理玩家吃杠/碰请求
        '''
        print('get in handle_chigang_peng')
        uniq_id, flag, cptype = msg.payload.decode().split(',')
        player = self.uniqid_players_map[uniq_id]

        if flag == '1':  # 吃杠
            player.chigang(self.last_leftcard, self.left_cards, cptype)
            for p in self.players:
                if p.id != player.id:
                    self.send_chiganginfo(p, player, self.last_leftcard.card)
                self.send_cardsinfo(p)
            self.send_showmycards(player)
            id = player.id
            self.handle_getcard(id)

        elif flag == '2':  # 碰
            player.peng(self.last_leftcard, self.left_cards, cptype)
            for p in self.players:
                if p.id != player.id:
                    self.send_penginfo(p, player, self.last_leftcard.card)
                self.send_cardsinfo(p)
            self.send_showmycards(player)
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
            for p in self.players:
                self.send_cardsinfo(p)
                self.send_showdianpaocards(p, player)
            sleep(10)
            self.init_start()

        elif flag == '2':  # 碰
            player.peng(self.last_leftcard, self.left_cards, cptype)
            for p in self.players:
                if p.id != player.id:
                    self.send_penginfo(p, player, self.last_leftcard.card)
                self.send_cardsinfo(p)
            self.send_showmycards(player)
            self.curplayer_id = player.id
            # 给玩家发送打牌消息
            self.send_throwcard(player)

        elif flag in ('n', 'N'):
            tmp = (self.curplayer_id + 1) % self.kind
            id = tmp if tmp else self.kind
            self.handle_getcard(id)


    def handle_dianpao_chigang(self, msg):
        '''
        处理玩家点炮/吃杠请求
        '''
        print('get in handle_dianpao')
        uniq_id, flag, cptype = msg.payload.decode().split(',')
        player = self.uniqid_players_map[uniq_id]

        if flag == '1':  # 点炮
            for p in self.players:
                self.send_cardsinfo(p)
                self.send_showdianpaocards(p, player)
            sleep(10)
            self.init_start()

        elif flag == '2':  # 吃杠
            player.chigang(self.last_leftcard, self.left_cards, cptype)
            for p in self.players:
                if p.id != player.id:
                    self.send_chiganginfo(p, player, self.last_leftcard.card)
                self.send_cardsinfo(p)
            self.send_showmycards(player)
            id = player.id
            self.handle_getcard(id)

        elif flag in ('n', 'N'):
            tmp = (self.curplayer_id + 1) % self.kind
            id = tmp if tmp else self.kind
            self.handle_getcard(id)


    def handle_dianpao_chigang_peng(self, msg):
        '''
        处理玩家点炮/吃杠/碰请求
        '''
        print('get in handle_chigang_peng')
        uniq_id, flag, cptype = msg.payload.decode().split(',')
        player = self.uniqid_players_map[uniq_id]

        if flag == '1':  # 点炮
            for p in self.players:
                self.send_cardsinfo(p)
                self.send_showdianpaocards(p, player)
            sleep(10)
            self.init_start()

        elif flag == '2':  # 吃杠
            player.chigang(self.last_leftcard, self.left_cards, cptype)
            for p in self.players:
                if p.id != player.id:
                    self.send_chiganginfo(p, player, self.last_leftcard.card)
                self.send_cardsinfo(p)
            self.send_showmycards(player)
            id = player.id
            self.handle_getcard(id)

        elif flag == '3':  # 碰
            player.peng(self.last_leftcard, self.left_cards, cptype)
            for p in self.players:
                if p.id != player.id:
                    self.send_penginfo(p, player, self.last_leftcard.card)
                self.send_cardsinfo(p)
            self.send_showmycards(player)
            self.curplayer_id = player.id
            # 给玩家发送打牌消息
            self.send_throwcard(player)

        elif flag in ('n', 'N'):
            tmp = (self.curplayer_id + 1) % self.kind
            id = tmp if tmp else self.kind
            self.handle_getcard(id)


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
        # 订阅吃杠消息
        self.client.subscribe(str(self.server_id) + ".chigang", callback = self.handle_chigang)
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
        # 订阅点炮/吃杠消息
        self.client.subscribe(str(self.server_id) + '.dianpao_chigang', callback = self.handle_dianpao_chigang)
        # 订阅点炮/吃杠/碰消息
        self.client.subscribe(str(self.server_id) + '.dianpao_chigang_peng', callback = self.handle_dianpao_chigang_peng)
        self.client.wait()


if __name__ == '__main__':
    # maj = Mahjong()
    # print(maj.cards)
    # print(maj.all_cards)
    # print(maj.shuffle_cards())
    # sup = Supervisor()
    # sup.players = [Player(1), Player(2)]
    # sup.add_player(Player(5))
    # print(sup.distribute_cards())
    # sup.start()
    gs = GameServer()
    gs.set_kind(2)
