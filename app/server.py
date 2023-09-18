from pynats import NATSClient
from base import Mahjong, Player
from utils import insert_card
import json


class GameServer:
    def __init__(self):
        self.nats_addr = "nats://localhost:4222"
        self.maj = Mahjong()
        self.table_cards = self.maj.shuffle_cards()  # 未被使用的牌堆
        # self.table_cards = ['2筒']*2+['1筒']*50
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
        with NATSClient(self.nats_addr) as client:
            client.publish(player.uniq_id + '.showmycards', payload = 'showmycards'.encode())


    def send_throwcard(self, player):
        '''
        向玩家发送可以打牌的消息
        '''
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
        :param player:
        :param card:
        :return:
        '''
        with NATSClient(self.nats_addr) as client:
            msg = str(player2.id) + '号打掉：' + card
            client.publish(player.uniq_id + '.throwcardinfo', payload = msg.encode())


    def send_peng(self, player):
        '''
        向玩家发送可以碰牌的消息
        '''
        with NATSClient(self.nats_addr) as client:
            client.publish(player.uniq_id + '.peng', payload = '可碰'.encode())


    def send_penginfo(self, player1, player2, card):
        with NATSClient(self.nats_addr) as client:
            msg = str(player2.id) + '号碰掉了：' + card
            client.publish(player1.uniq_id + '.penginfo', payload = msg.encode())


    def send_chigang(self, player):
        '''
        向玩家发送可以吃杠的消息
        '''
        with NATSClient(self.nats_addr) as client:
            client.publish(player.uniq_id + '.chigang', payload = '可吃杠'.encode())


    def send_chiganginfo(self, player1, player2, card):
        with NATSClient(self.nats_addr) as client:
            msg = str(player2.id) + '号杠掉了：' + card
            client.publish(player1.uniq_id + '.chiganginfo', payload = msg.encode())


    def send_bugang(self, player):
        '''
        向玩家发送可以补杠的消息
        '''
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
        with NATSClient(self.nats_addr) as client:
            client.publish(player.uniq_id + '.angang', payload = '可暗杠'.encode())


    def send_anganginfo(self):
        pass


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

            with NATSClient(self.nats_addr) as client:
                client.publish('enable', payload='enable'.encode())
            self.send_isjoin(player, '欢迎加入对局！')

            if len(self.players) == self.kind:  # 玩家数量达到，开始游戏
                self.send_startgame()
                self.distribute_cards()  # 发牌
                # test
                # p1, p2 = self.players
                # p1.hand_cards = {'筒子':['1筒','1筒','2筒','2筒'],'条子':['1条'],'万字':[],'字牌':[],'花牌':[]}
                # p2.hand_cards = {'筒子': ['1筒'], '条子':['5条'],'万字':[],'字牌':[],'花牌':[]}
                for p in self.players:  # 给每个对局中的玩家发送卡牌信息
                    self.send_cardsinfo(p)
                    self.send_showmycards(p)

                curplayer = self.id_players_map[self.curplayer_id]  # 轮到打牌的玩家
                self.send_throwcard(curplayer)
        else:
            print('已达最大玩家数量')

            with NATSClient(self.nats_addr) as client:
                client.publish('enable', payload='enable'.encode())
            self.send_isjoin(player, '已达最大玩家数量！')


    def handle_getcard(self):
        '''
        处理玩家摸牌请求
        '''
        pass


    def handle_throwcard(self, msg):
        '''
        处理玩家打牌操作
        '''
        uniq_id, ind = msg.payload.decode().split(',')
        player = self.uniqid_players_map[uniq_id]

        # 正常下标
        if ind != 'x':
            leftcard = player.throw_card(self.left_cards, int(ind))
            self.last_leftcard = LastLeftCard(player, leftcard)
            self.send_cardsinfo(player)
            self.send_showmycards(player)

            for p in self.players:
                if p.id != player.id:
                    self.send_throwcardinfo(p, player, leftcard)
                self.send_cardsinfo(p)  # 打牌后给每个玩家更新牌面信息
                # 碰判断
                peng_return = p.is_peng(self.last_leftcard)
                print('peng_return:', peng_return)
                # 吃杠判断
                chigang_return = p.is_chigang(self.last_leftcard)
                print('chigang_return', chigang_return)
                # 点炮判断
                pass

                if peng_return:  # 向玩家发送可碰消息
                    self.peng_type = peng_return
                    self.send_peng(p)
                    break
                if chigang_return:  # 向玩家发送可吃杠消息
                    self.chigang_type = chigang_return
                    self.send_chigang(p)
                    break
            # 无碰无杠则轮到下一个玩家
            if not peng_return and not chigang_return:
                print('no peng no gang')
                tmp = (self.curplayer_id + 1) % self.kind
                self.curplayer_id = tmp if tmp else self.kind
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
                if bugang_return:
                    self.bugang_card = card
                    self.bugang_type = bugang_return
                    self.send_bugang(curplayer)
                if angang_return:
                    self.angang_card = card
                    self.angang_type = angang_return
                    self.send_angang(curplayer)
                if not bugang_return and not angang_return:
                    self.send_throwcard(curplayer)
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
        uniq_id, ifpeng = msg.payload.decode().split(',')
        player = self.uniqid_players_map[uniq_id]
        if ifpeng in ('y', 'Y'):  # 碰了要打掉一张
            # 更新牌面信息
            player.peng(self.last_leftcard, self.left_cards, self.peng_type)
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
            self.curplayer_id = tmp if tmp else self.kind
            curplayer = self.id_players_map[self.curplayer_id]
            # 先摸后打
            type, card = curplayer.get_card(self.table_cards)
            self.send_getcard(curplayer, card)
            for p in self.players:
                self.send_cardsinfo(p)
            self.send_showmycards(curplayer)
            self.send_throwcard(curplayer)


    def handle_chigang(self, msg):
        '''
        处理玩家吃杠请求
        '''
        uniq_id, ifchigang = msg.payload.decode().split(',')
        player = self.uniqid_players_map[uniq_id]
        if ifchigang in ('y', 'Y'):  # 杠了要摸一张再打掉一张
            # 更新牌面信息
            player.chigang(self.last_leftcard, self.left_cards, self.chigang_type)
            for p in self.players:
                if p.id != player.id:
                    self.send_chiganginfo(p, player, self.last_leftcard.card)
                self.send_cardsinfo(p)
            self.send_showmycards(player)
            self.curplayer_id = player.id
            # 摸一张
            type, card = player.get_card(self.table_cards)
            self.send_getcard(player, card)
            for p in self.players:
                self.send_cardsinfo(p)
            self.send_showmycards(player)
            # 打一张
            self.send_throwcard(player)
            self.curplayer_id = player.id
        elif ifchigang in ('n', 'N'):  # 不杠则发牌给下一个玩家
            tmp = (self.curplayer_id + 1) % self.kind
            self.curplayer_id = tmp if tmp else self.kind
            curplayer = self.id_players_map[self.curplayer_id]
            # 先摸后打
            type, card = curplayer.get_card(self.table_cards)
            self.send_getcard(curplayer, card)
            for p in self.players:
                self.send_cardsinfo(p)
            self.send_showmycards(curplayer)
            self.send_throwcard(curplayer)


    def handle_bugang(self, msg):
        '''
        处理玩家补杠请求
        '''
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
            type, card = player.get_card(self.table_cards)
            self.send_getcard(player, card)
            for p in self.players:
                self.send_cardsinfo(p)
            self.send_showmycards(player)
            # 打一张
            self.send_throwcard(player)
        elif ifbugang in ('n', 'N'):  # 不杠则打掉一张
            self.send_throwcard(player)


    def handle_angang(self):
        '''
        处理玩家暗杠请求
        '''
        pass


    def handle_zimo(self):
        '''
        处理玩家自摸请求
        '''
        pass


    def handle_dianpao(self):
        '''
        处理玩家点炮请求
        '''
        pass


    # 启动游戏服务器
    def run(self):
        with NATSClient(self.nats_addr) as client:
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