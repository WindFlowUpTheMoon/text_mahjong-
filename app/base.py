from random import shuffle
from utils import LastLeftCard
from collections import Counter


class Mahjong:
    def __init__(self):
        self.types = ['筒子', '条子', '万字', '字牌', '花牌']
        self.cards = {self.types[0]: list(range(1, 10)), self.types[1]: list(range(1, 10)),
                      self.types[2]: list(range(1, 10)), \
                      self.types[3]: ['东风', '南风', '西风', '北风', '红中', '发财', '白板'], self.types[4]: [1, 2, 3, 4]}
        self.abb_map = {'筒': '筒子', '条': '条子', '万': '万字', '花': '花牌'}
        self.all_cards = []
        for k, v in self.cards.items():
            if k in self.types[:3]:
                for i in v:
                    self.all_cards.extend([str(i) + k[0]] * 4)
            elif k == self.types[3]:
                for i in v:
                    self.all_cards.extend([i] * 4)
            else:
                for i in v:
                    self.all_cards.extend([str(i) + '花'] * 2)


    def shuffle_cards(self):
        '''
        洗牌
        '''
        newcards = self.all_cards.copy()
        shuffle(newcards)
        return newcards


class Player:
    def __init__(self, name, uniq_id):
        self.maj = Mahjong()
        self.name = name
        self.id = 0
        self.uniq_id = uniq_id
        self.hand_cards = {'筒子': [], '条子': [], '万字': [], '字牌': [], '花牌': []}
        self.pg_cards = []  # 碰、杠后的手牌
        self.pg_num = 0  # 碰、杠的次数
        self.money = 0  # 筹码


    def get_card(self, table_cards):
        '''
        摸牌
        '''
        # nonlocal table_cards
        card = table_cards.pop(0)
        if card[1] in self.maj.abb_map:
            type = self.maj.abb_map[card[1]]
        else:
            type = '字牌'
        self.hand_cards[type].append(card)
        self.hand_cards[type].sort()
        return type, card


    def throw_card(self, left_cards, ind):
        '''
        打牌
        '''
        # nonlocal left_cards
        l=[]
        for type, cards in self.hand_cards.items():
            l.extend(cards)
        card = l.pop(ind)

        if card[1] in self.maj.abb_map:
            type = self.maj.abb_map[card[1]]
        else:
            type = '字牌'

        self.hand_cards[type].remove(card)
        left_cards.append(card)
        return card


    def is_peng(self, last_left_card: LastLeftCard):
        '''
        判断是否可碰
        '''
        leftcard = last_left_card.card
        if leftcard[1] in self.maj.abb_map:
            type = self.maj.abb_map[leftcard[1]]
        else:
            type = '字牌'
        c = Counter(self.hand_cards[type])
        if c[leftcard] == 2:
            return type
        return False


    def peng(self, last_left_card: LastLeftCard, left_cards, type):
        '''
        碰
        '''
        leftcard = last_left_card.card
        left_cards.remove(leftcard)
        self.hand_cards[type].remove(leftcard)
        self.hand_cards[type].remove(leftcard)
        self.pg_cards.extend([leftcard] * 3)
        self.pg_num += 1


    def is_chigang(self, last_left_card: LastLeftCard):
        '''
        判断是否可吃杠
        '''
        leftcard = last_left_card.card
        if leftcard[1] in self.maj.abb_map:
            type = self.maj.abb_map[leftcard[1]]
        else:
            type = '字牌'
        c = Counter(self.hand_cards[type])
        print('ccccc', c)
        if c[leftcard] == 3:
            return type
        return False


    def chigang(self, last_left_card: LastLeftCard, left_cards, type):
        '''
        吃杠
        '''
        leftcard = last_left_card.card
        left_cards.remove(leftcard)
        self.hand_cards[type].remove(leftcard)
        self.hand_cards[type].remove(leftcard)
        self.hand_cards[type].remove(leftcard)
        self.pg_cards.extend([leftcard] * 4)
        self.pg_num += 1
        self.money += 3
        last_left_card.player.money -= 3


    def is_bugang(self, card_got):
        '''
        判断是否可补杠
        '''
        if card_got[1] in self.maj.abb_map:
            type = self.maj.abb_map[card_got[1]]
        else:
            type = '字牌'
        if card_got in self.pg_cards:
            return type
        return False


    def bugang(self, card_got, type, players):
        '''
        补杠
        '''
        self.hand_cards[type].remove(card_got)
        ind = self.pg_cards.index(card_got)
        self.pg_cards.insert(ind, card_got)
        self.money += (len(players)-1)
        for player in players:
            if player != self:
                player.money -= 1


    def is_angang(self, card_got, type):
        '''
        判断是否可暗杠
        '''
        c = Counter(self.hand_cards[type])
        if c[card_got] == 4:
            return True
        return False


    def angang(self, card_got, type, players):
        '''
        暗杠
        '''
        for i in range(4):
            self.hand_cards[type].remove(card_got)
        self.pg_cards.extend([card_got] * 4)
        self.money += (len(players)-1) * 2
        for player in players:
            if player != self:
                player.money -= 2


    def hu(self):
        '''
        胡
        '''
        # 3*4+2 平胡

        # 2*7 七对
        for type, cards in self.hand_cards.items():
            c = Counter(cards)
            return all(v in (2, 4) for k, v in c.items())
        # 12*1+2 十三幺
        thirteen_cards = ['1筒', '9筒', '1条', '9条', '1万', '9万', '东风', '南风', '西风', '北风', '红中', '发财', '白板']
        flatten_cards = [card for type, cards in self.hand_cards.items() for card in cards]
        if set(flatten_cards) == set(thirteen_cards):
            return True

        # 鸡胡 1

        # 碰碰胡 2
        # 混一色

        # 清龙 3
        # 三暗刻

        # 清一色 4
        # 七小对

        # 混幺九 5
        # 三杠

        # 豪华七小对 7
        # 清幺九
        # 四暗刻
        # 小四喜
        # 小三元
        # 字一色

        # 大四喜 13
        # 大三元
        # 九宝莲灯
        # 十三幺
        # 十八罗汉
        # 连七对
        pass


    def dianpao(self):
        '''
        点炮
        '''
        pass