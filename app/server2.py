from pynats import NATSClient
from base import Mahjong, Player
from utils import *
import json
from copy import deepcopy


class GameServer:
    def __init__(self):
        self.nats_addr = "nats://localhost:4222"
        self.maj = Mahjong()
        self.table_cards = self.maj.shuffle_cards()  # 未被使用的牌堆
        # self.table_cards = ['6万']*50
        self.left_cards = []  # 被打掉的牌堆
        self.players = []
        self.kind = 2  # 游戏类型（双人、三人、四人等）
        self.last_leftcard = None
        self.peng_type = None  # 碰的牌的类型
        self.chigang_type = None
        self.bugang_card = None  # 补杠摸到的那张牌
        self.bugang_type = None
        self.angang_card = None  # 暗杠摸到的那张牌
        self.angang_type = None
        self.curplayer_id = 1  # 当前轮到摸牌的玩家id
        self.uniqid_players_map = {}  # uniq_id与玩家的映射
        self.id_players_map = {}  # id与玩家的映射


    def set_kind(self, x):
        self.kind = x


    def nohu_ending_judge(self):
        '''
        流局判断
        '''
        if not self.table_cards:
            return True
        return False


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


    def awaken_client(self, player):
        # 唤醒客户端
        with NATSClient(self.nats_addr) as client:
            client.publish('awake', payload = 'enable'.encode())


    def send_isjoin(self, player, msg):
        '''
        给玩家发送加入请求的返回信息
        '''
        with NATSClient(self.nats_addr) as client:
            client.publish(player.uniq_id + '.isjoin', payload = msg.encode())


    def send_startgame(self):
        '''
        向对局中的每个玩家发送游戏开始消息
        '''
        with NATSClient(self.nats_addr) as client:
            client.publish('startgame', payload = '游戏开始'.encode())


    def send_cardsinfo(self, player):
        '''
        每次操作都要给玩家发送更新卡牌信息
        '''
        with NATSClient(self.nats_addr) as client:
            mycards = [player.hand_cards, player.pg_cards]
            otherplayers_cards = []
            for p in self.players:
                if p != player:
                    otherplayers_cards.append([p.id, p.pg_cards])
            tablecards_num = len(self.table_cards)
            leftcards = self.left_cards
            cardsinfo = [mycards, otherplayers_cards, tablecards_num, leftcards]
            client.publish(player.uniq_id + '.cardsinfo', payload = json.dumps(cardsinfo).encode())


    def send_showmycards(self, player):
        '''
        给玩家发送消息让玩家打印自己的手牌信息
        '''
        print(player.uniq_id)
        with NATSClient(self.nats_addr) as client:
            client.publish(player.uniq_id + '.showmycards', payload = 'showmycards'.encode())


    def send_throwcard(self, player):
        '''
        向玩家发送可以打牌的消息
        '''
        print('send_throwcard')
        with NATSClient(self.nats_addr) as client:
            client.publish(player.uniq_id + '.throwcard', payload = 'throwcard'.encode())


    def send_getcard(self, player, card):
        '''
        向玩家发送摸牌消息
        '''
        with NATSClient(self.nats_addr) as client:
            client.publish(player.uniq_id + '.getcard', payload = card.encode())


    def send_throwcardinfo(self, player, player2, card):
        '''
        向玩家发送打掉的牌的信息
        '''
        with NATSClient(self.nats_addr) as client:
            msg = str(player2.id) + '号打掉：' + card
            client.publish(player.uniq_id + '.throwcardinfo', payload = msg.encode())


    def send_peng(self, player, cptype):
        '''
        向玩家发送可以碰牌的消息
        '''
        print('send_peng:', cptype, player.uniq_id)
        with NATSClient(self.nats_addr) as client:
            client.publish(player.uniq_id + '.peng', payload = cptype.encode())


    def send_penginfo(self, player1, player2, card):
        with NATSClient(self.nats_addr) as client:
            msg = str(player2.id) + '号碰掉了：' + card
            client.publish(player1.uniq_id + '.penginfo', payload = msg.encode())


    def send_chigang(self, player, cptype):
        '''
        向玩家发送可以吃杠的消息
        '''
        print('send_chigang')
        with NATSClient(self.nats_addr) as client:
            client.publish(player.uniq_id + '.chigang', payload = cptype.encode())


    def send_chiganginfo(self, player1, player2, card):
        with NATSClient(self.nats_addr) as client:
            msg = str(player2.id) + '号杠掉了：' + card
            client.publish(player1.uniq_id + '.chiganginfo', payload = msg.encode())


    def send_bugang(self, player):
        '''
        向玩家发送可以补杠的消息
        '''
        print('send_bugang')
        with NATSClient(self.nats_addr) as client:
            client.publish(player.uniq_id + '.bugang', payload = '可补杠'.encode())


    def send_buganginfo(self, player1, player2, card):
        with NATSClient(self.nats_addr) as client:
            msg = str(player2.id) + '号补杠：' + card
            client.publish(player1.uniq_id + '.buganginfo', payload = msg.encode())


    def send_angang(self, player):
        '''
        向玩家发送可以暗杠的消息
        '''
        print('send_angang')
        with NATSClient(self.nats_addr) as client:
            client.publish(player.uniq_id + '.angang', payload = '可暗杠'.encode())


    def send_anganginfo(self, player1, player2):
        with NATSClient(self.nats_addr) as client:
            msg = str(player2.id) + '号暗杠！'
            client.publish(player1.uniq_id + '.anganginfo', payload = msg.encode())


    def send_zimo(self, player):
        '''
        向玩家发送可以自摸的消息
        '''
        with NATSClient(self.nats_addr) as client:
            client.publish(player.uniq_id + '.zimo', payload = player.hu_kind.encode())


    def send_showhucards(self, p, player):
        id, handcards, pgcards, hu_kind = player.id, player.hand_cards, player.pg_cards, player.hu_kind
        with NATSClient(self.nats_addr) as client:
            msg = [str(id), handcards, pgcards, player.hu_kind]
            client.publish(p.uniq_id + '.showhucards', payload = json.dumps(msg).encode())


    def send_dianpao(self, player):
        '''
        向玩家发送可以点炮的消息
        '''
        with NATSClient(self.nats_addr) as client:
            client.publish(player.uniq_id + '.dianpao', payload = player.hu_kind.encode())


    def send_showdianpaocards(self, p, player):
        id, handcards, pgcards, hu_kind = player.id, player.hand_cards, player.pg_cards, player.hu_kind
        with NATSClient(self.nats_addr) as client:
            msg = [str(id), handcards, pgcards, hu_kind]
            client.publish(p.uniq_id + '.showdianpaocards', payload = json.dumps(msg).encode())


    def send_barkinfo(self, player, msg):
        '''
        广播玩家狗叫信息
        '''
        with NATSClient(self.nats_addr) as client:
            client.publish(player.uniq_id + '.barkinfo', payload = msg.encode())


    def send_chigang_peng(self, player, cptype):
        '''
        向玩家发送可吃杠可碰的消息
        '''
        print('send_chigang_peng')
        print('send_chigang_peng')
        with NATSClient(self.nats_addr) as client:
            client.publish(player.uniq_id + '.chigang_peng', payload = cptype.encode())


    def send_dianpao_peng(self, player, cptype):
        '''
        向玩家发送可点炮可碰的消息
        '''
        print('send_dianpao_peng')
        with NATSClient(self.nats_addr) as client:
            client.publish(player.uniq_id + '.dianpao_peng', payload = cptype.encode())


    def send_dianpao_chigang(self, player, cptype):
        '''
        向玩家发送可点炮可吃杠的消息
        '''
        print('send_dianpao_chigang')
        with NATSClient(self.nats_addr) as client:
            client.publish(player.uniq_id + '.dianpao_chigang', payload = cptype.encode())


    def send_dianpao_chigang_peng(self, player, cptype):
        '''
        向玩家发送可点炮可吃杠可碰的消息
        '''
        print('send_dianpao_chigang_peng')
        with NATSClient(self.nats_addr) as client:
            client.publish(player.uniq_id + '.dianpao_chigang_peng', payload = cptype.encode())


    def handle_bark(self, msg):
        '''
        处理玩家狗叫信息
        '''
        uniq_id, info = msg.payload.decode().split(',')
        bark_player = self.uniqid_players_map[uniq_id]
        print(str(bark_player.id) + '号:' + info)
        msg = str(bark_player.id) + ',' + info
        for p in self.players:
            if p != bark_player:
                self.send_barkinfo(p, msg)


    def handle_join(self, msg):
        '''
        处理玩家加入请求
        '''
        name, uniq_id, ip = msg.payload.decode().split(',')
        player = Player(name, uniq_id)
        print('target ip is: ', ip)

        if len(self.players) < self.kind:
            player.id = max([p.id for p in self.players]) + 1 if self.players else 1
            self.players.append(player)
            self.uniqid_players_map[uniq_id] = player
            self.id_players_map[player.id] = player

            print('第' + str(player.id) + '位玩家"' + player.name + '"加入对局！')

            # 激活状态，否则第一次send_isjoin会丢失
            self.awaken_client(player)
            self.send_isjoin(player, '欢迎加入对局！')

            if len(self.players) == self.kind:  # 玩家数量达到，开始游戏
                self.send_startgame()
                self.distribute_cards()  # 发牌
                # test
                # p1, p2 = self.players
                # p1.hand_cards = {'筒子': [],
                #                  '条子': ['1条', '1条', '1条', '2条', '3条', '4条', '5条', '6条', '7条', '8条', '9条', '9条', '9条'],
                #                  '万字': ['1万'], '字牌': [], '花牌': []}
                # p2.hand_cards = {'筒子': ['1筒', '4筒', '8筒'], '条子': ['3条', '3条', '8条'],
                #                  '万字': ['2万', '5万', '5万', '8万', '9万'], '字牌': ['北风', '北风'], '花牌': []}
                # p3.hand_cards = {'筒子': ['9筒', '9筒'], '条子': ['1条', '9条'], '万字': ['3万', '3万', '4万', '4万', '8万'], '字牌': ['南风', '白板', '红中', '红中'], '花牌': []}
                for p in self.players:  # 给每个对局中的玩家发送卡牌信息
                    self.awaken_client(p)
                    self.send_cardsinfo(p)
                    self.send_showmycards(p)

                curplayer = self.id_players_map[self.curplayer_id]  # 轮到打牌的玩家
                self.send_throwcard(curplayer)
        else:
            print('已达最大玩家数量')
            # 激活状态，否则第一次send_isjoin会丢失
            self.awaken_client(player)
            self.send_isjoin(player, '已达最大玩家数量！')


    def handle_getcard(self, id):
        '''
        处理摸牌操作
        '''
        print('get in handle_getcard')
        self.curplayer_id = id
        print('curplayer_id:', self.curplayer_id)
        curplayer = self.id_players_map[self.curplayer_id]

        # 先摸后打
        type, card = curplayer.get_card(self.table_cards)
        self.send_getcard(curplayer, card)
        self.send_cardsinfo(curplayer)  # 摸牌后给该玩家发送牌面信息
        self.send_showmycards(curplayer)
        # 判断是否补杠
        bugang_return = curplayer.is_bugang(card)
        # 判断是否暗杠
        angang_return = curplayer.is_angang(card, type)
        # 判断是否自摸
        hu_return = False
        if not curplayer.hand_cards['花牌']:
            hu_return = curplayer.is_hu(curplayer.hand_cards)
            if hu_return:
                curplayer.hu_kind = curplayer.kind_check(curplayer.hand_cards, curplayer.pg_cards, curplayer.angang_num)
                self.send_zimo(curplayer)
                return

        print(bugang_return, angang_return, hu_return)

        if bugang_return:
            self.bugang_card = card
            self.bugang_type = bugang_return
            self.send_bugang(curplayer)
            return
        if angang_return:
            self.angang_card = card
            self.angang_type = type
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
                if p == player:
                    self.send_showmycards(player)

            one_flag = False  # 判断循环里是否出现过点炮/吃杠/碰
            for p in self.players:
                tmp_list = [0, 0, 0]  # 分别代表点炮与否、吃杠与否、碰与否
                if self.last_leftcard.player != p:
                    # 点炮判断
                    lastcard = self.last_leftcard.card
                    if lastcard[1] in self.maj.abb_map:
                        card_type = self.maj.abb_map[lastcard[1]]
                    else:
                        card_type = '字牌'
                    tmp_handcards = deepcopy(p.hand_cards)
                    tmp_handcards[card_type].append(lastcard)
                    tmp_handcards[card_type].sort()
                    if not tmp_handcards['花牌']:
                        if p.is_hu(tmp_handcards):
                            p.hu_kind = p.kind_check(tmp_handcards, p.pg_cards, p.angang_num)
                            if p.hu_kind != '鸡胡':
                                tmp_list[0] = 1

                    # 吃杠判断
                    cp_type = p.is_chigang(self.last_leftcard)
                    if cp_type:
                        tmp_list[1] = 1

                    # 碰判断
                    cp_type = p.is_peng(self.last_leftcard)
                    if cp_type:
                        tmp_list[2] = 1

                    if tmp_list == [0, 0, 1]:
                        one_flag = True
                        self.send_peng(p, cp_type)
                    elif tmp_list == [0, 1, 0]:
                        one_flag = True
                        self.send_chigang(p, cp_type)
                    elif tmp_list == [1, 0, 0]:
                        one_flag = True
                        self.send_dianpao(p)
                    elif tmp_list == [0, 1, 1]:
                        one_flag = True
                        self.send_chigang_peng(p, cp_type)
                    elif tmp_list == [1, 0, 1]:
                        one_flag = True
                        self.send_dianpao_peng(p, cp_type)
                    elif tmp_list == [1, 1, 0]:
                        one_flag = True
                        self.send_dianpao_chigang(p, cp_type)
                    elif tmp_list == [1, 1, 1]:
                        one_flag = True
                        self.send_dianpao_chigang_peng(p, cp_type)
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
        print('zimooooooooooooooooooo')
        if ifzimo in ('y', 'Y'):
            for p in self.players:
                self.send_cardsinfo(p)
                self.send_showhucards(p, player)
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


    # 启动游戏服务器
    def run(self):
        with NATSClient(self.nats_addr) as client:
            # 订阅狗叫消息
            client.subscribe("bark", callback = self.handle_bark)
            # 订阅加入消息
            client.subscribe("join", callback = self.handle_join)
            # 订阅摸牌消息
            client.subscribe("getcard", callback = self.handle_getcard)
            # 订阅打牌消息
            client.subscribe("throwcard", callback = self.handle_throwcard)
            # 订阅碰牌消息
            client.subscribe("peng", callback = self.handle_peng)
            # 订阅吃杠消息
            client.subscribe("chigang", callback = self.handle_chigang)
            # 订阅补杠消息
            client.subscribe("bugang", callback = self.handle_bugang)
            # 订阅暗杠消息
            client.subscribe("angang", callback = self.handle_angang)
            # 订阅自摸消息
            client.subscribe("zimo", callback = self.handle_zimo)
            # 订阅点炮消息
            client.subscribe("dianpao", callback = self.handle_dianpao)
            # 订阅吃杠/碰消息
            client.subscribe('chigang_peng', callback = self.handle_chigang_peng)
            # 订阅点炮/碰消息
            client.subscribe('dianpao_peng', callback = self.handle_dianpao_peng)
            # 订阅点炮/吃杠消息
            client.subscribe('dianpao_chigang', callback = self.handle_dianpao_chigang)
            # 订阅点炮/吃杠/碰消息
            client.subscribe('dianpao_chigang_peng', callback = self.handle_dianpao_chigang_peng)
            client.wait()


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
    gs.run()
