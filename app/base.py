from random import shuffle
from utils import LastLeftCard, handcards2numlist
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
        if card_got in self.pg_cards and card_got[1] != '花':
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


    def hu(self, hand_cards):
        '''
        胡牌检测
        万：1-9，条：11-19，饼：21-29，东西南北风：31,33,35,37，中发白：41,43,45。
        '''
        a = handcards2numlist(hand_cards)
        a = sorted(a)
        # print(a)

        # 是否有对子检查。
        double = []
        for x in set(a):
            if a.count(x) >= 2:
                double.append(x)
        # print(double)
        if len(double) == 0:
            # print('和牌失败：无对子')
            return False

        # 7对子检查（由于不常见，可以放到后面进行判断）
        # 对子的检查，特征1：必须是14张；特征2:一个牌型，有2张，或4张。特别注意有4张的情况。
        if len(a) == 14:
            for x in set(a):
                if a.count(x) not in [2, 4]:
                    break
            else:
                return True

        # 十三幺检查。
        if len(a) == 14:
            gtws = [1, 9, 11, 19, 21, 29, 31, 33, 35, 37, 41, 43,
                    45]  # [1,9,11,19,21,29]+list(range(31,38,2))+list(range(41,46,2)) #用固定的表示方法，计算速度回加快。
            # print(gtws)
            for x in gtws:
                if 1 <= a.count(x) <= 2:
                    pass
                else:
                    break
            else:
                print('和牌：国土无双，十三幺！')
                return True

        # 常规和牌检测。
        a1 = a.copy()
        a2 = []  # a2用来存放和牌后分组的结果。
        for x in double:
            # print('double',x)
            # print(a1[0] in a1 and (a1[0]+1) in a1 and (a1[0]+2) in a1)
            a1.remove(x)
            a1.remove(x)
            a2.append((x, x))
            for i in range(int(len(a1) / 3)):
                # print('i-',i)
                if a1.count(a1[0]) == 3:
                    # 列表移除，可以使用remove,pop，和切片，这里切片更加实用。
                    a2.append((a1[0],) * 3)
                    a1 = a1[3:]
                    # print(a1)
                elif a1[0] in a1 and a1[0] + 1 in a1 and a1[
                    0] + 2 in a1:  # 这里注意，11,2222,33，和牌结果22,123,123，则连续的3个可能不是相邻的。
                    a2.append((a1[0], a1[0] + 1, a1[0] + 2))
                    a1.remove(a1[0] + 2)
                    a1.remove(a1[0] + 1)
                    a1.remove(a1[0])
                    # print(a1)
                else:
                    a1 = a.copy()
                    a2 = []
                    # print('重置')
                    break
            else:
                # print('和牌成功,结果：',a2)
                return True
        # 如果上述没有返回和牌成功，这里需要返回和牌失败。
        else:
            # print('和牌失败：遍历完成。')
            return False


    def dianpao(self):
        '''
        点炮
        '''
        pass


if __name__=='__main__':
    hand_cards = {'筒子':[],'条子':['1条','2条','2条','3条','3条','3条','4条','4条','5条','6条','6条','6条',],'万字':['5万','6万'],'字牌':[]}
    player=Player('test','1')
    player.hand_cards = hand_cards
    print(player.hu(hand_cards))