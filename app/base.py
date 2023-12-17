from collections import Counter
from random import shuffle
from app.utils import LastLeftCard, handcards2numlist
from app.config import MINGGANG, ANGANG, PLAYER_INIT_MONEY
# from utils import LastLeftCard, handcards2numlist
# from config import MINGGANG, ANGANG, PLAYER_INIT_MONEY


class Mahjong:
    def __init__(self):
        self.types = ['筒', '条', '万', '字', '花']
        # 筒：0-8  条：9-17  万：18-26  字：27-33  花：34-37
        self.cards_num = [*list(range(1, 10)), *list(range(11, 20)), *list(range(21, 30)), 31, 33, 35, 37, \
                          41, 43, 45, *list(range(-4, 0))[::-1]]
        self.cards_text = ['一筒', '二筒', '三筒', '四筒', '五筒', '六筒', '七筒', '八筒', '九筒', '一条', '二条', '三条', '四条', \
                           '五条', '六条', '七条', '八条', '九条', '一万', '二万', '三万', '四万', '五万', '六万', '七万', '八万', \
                           '九万', '东风', '南风', '西风', '北风', '红中', '发财', '白板', '一花', '二花', '三花', '四花']
        self.tong_range = self.cards_num[0:9]
        self.tiao_range = self.cards_num[9:18]
        self.wan_range = self.cards_num[18:27]
        self.zi_range = self.cards_num[27:34]
        self.hua_range = self.cards_num[34:]
        self.cards_map = dict(zip(self.cards_num, self.cards_text))
        self.all_cards = self.cards_num[:34] * 4 + self.cards_num[34:] * 2


    def shuffle_cards(self):
        new_cards = self.all_cards.copy()
        shuffle(new_cards)
        return new_cards


class Player:
    def __init__(self, name, uniq_id):
        self.maj = Mahjong()
        self.name = name
        self.id = 0
        self.uniq_id = uniq_id
        self.type_map = {'筒': self.maj.tong_range, '条': self.maj.tiao_range, '万': self.maj.wan_range, \
                         '字': self.maj.zi_range, '花': self.maj.hua_range}
        self.hand_cards = {'筒': [], '条': [], '万': [], '字': [], '花': []}
        self.pg_cards = {'viewable': [], 'unviewable': []}  # 碰、杠后的手牌
        self.pg_num = 0  # 碰、杠的次数
        self.angang_num = 0  # 暗杠的次数
        self.money = PLAYER_INIT_MONEY  # 筹码
        self.money_gang = 0  # 杠得到的钱
        self.hu_kinds = None  # 胡牌类型
        self.first_getcard = True
        self.dianpaoable = False  # 是否可点炮
        self.dianpao = -1  # 点炮状态，-1表示未处理，0表示不点，1表示点
        self.qgh = False  # 是否抢杠胡


    def judge_card_type(self, card):
        '''
        判断牌的类型
        '''
        for type, rng in self.type_map.items():
            if card in rng:
                return type
        return False


    def get_card(self, table_cards):
        '''
        摸牌
        '''
        if not table_cards:
            return 'empty', ''
        card = table_cards.pop(0)
        type = self.judge_card_type(card)
        self.hand_cards[type].append(card)
        self.hand_cards[type].sort()
        return type, card


    def throw_card(self, left_cards, ind):
        '''
        打牌
        '''
        l = []
        for type, cards in self.hand_cards.items():
            l.extend(cards)
        card = l.pop(ind)
        type = self.judge_card_type(card)
        self.hand_cards[type].remove(card)
        left_cards.append(card)
        return card


    def is_peng(self, last_left_card: LastLeftCard):
        '''
        判断是否可碰
        '''
        leftcard = last_left_card.card
        type = self.judge_card_type(leftcard)
        c = Counter(self.hand_cards[type])
        if c[leftcard] >= 2:
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
        self.pg_cards['viewable'].extend([leftcard] * 3)
        self.pg_num += 1


    def is_chigang(self, last_left_card: LastLeftCard):
        '''
        判断是否可吃杠
        '''
        leftcard = last_left_card.card
        type = self.judge_card_type(leftcard)
        c = Counter(self.hand_cards[type])
        if c[leftcard] == 3:
            return type
        return False


    def chigang(self, last_left_card: LastLeftCard, left_cards, type, players):
        '''
        吃杠
        '''
        leftcard = last_left_card.card
        left_cards.remove(leftcard)
        self.hand_cards[type].remove(leftcard)
        self.hand_cards[type].remove(leftcard)
        self.hand_cards[type].remove(leftcard)
        self.pg_cards['viewable'].extend([leftcard] * 4)
        self.pg_num += 1
        self.money_gang += (len(players) - 1) * MINGGANG
        last_left_card.player.money_gang -= (len(players) - 1) * MINGGANG


    def is_bugang(self, card_got):
        '''
        判断是否可补杠
        '''
        type = self.judge_card_type(card_got)
        if card_got in self.pg_cards['viewable'] and card_got not in self.maj.hua_range:
            return type
        return False


    def bugang(self, card_got, type, players):
        '''
        补杠
        '''
        self.hand_cards[type].remove(card_got)
        ind = self.pg_cards['viewable'].index(card_got)
        self.pg_cards['viewable'].insert(ind, card_got)
        self.money_gang += (len(players) - 1) * MINGGANG
        for player in players:
            if player != self:
                player.money_gang -= MINGGANG


    def is_angang(self):
        '''
        判断是否可暗杠
        '''
        for type, cards in self.hand_cards.items():
            c = Counter(self.hand_cards[type])
            for card, num in c.items():
                if num == 4:
                    return type, card
        return False


    def angang(self, card_got, type, players):
        '''
        暗杠
        '''
        for i in range(4):
            self.hand_cards[type].remove(card_got)
        self.pg_cards['unviewable'].extend([card_got] * 4)
        self.money_gang += (len(players) - 1) * ANGANG
        self.angang_num += 1
        for player in players:
            if player != self:
                player.money_gang -= ANGANG


    def is_hu(self, hand_cards):
        '''
        胡牌检测
        筒：1-9，条：11-19，万：21-29，东南西北风：31,33,35,37，中白发：41,43,45。
        '''
        a = []
        for cards in hand_cards.values():
            a.extend(cards)
        a = sorted(a)
        # print(a)

        # 七星不靠检查
        if set(hand_cards['字']) == set(self.maj.zi_range) and len(Counter(a)) == 14:
            l = []
            for type, cards in hand_cards.items():
                if type in ('筒', '条', '万'):
                    l.extend(cards)
            l = [str(i)[-1] for i in l]
            if len(Counter(l)) == 7:
                for type in ('筒', '条', '万'):
                    if not (all(str(i)[-1] in ('1', '4', '7') for i in hand_cards[type]) or all(
                            str(i)[-1] in ('2', '5', '8') for i in hand_cards[type]) \
                            or all(str(i)[-1] in ('3', '6', '9') for i in hand_cards[type])):
                        break
                else:
                    return ['七星不靠']

        # 是否有对子检查。
        double = []
        for x in set(a):
            if a.count(x) >= 2:
                double.append(x)
        if len(double) == 0:
            return False

        # 七对胡牌
        if len(a) == 14:
            for x in set(a):
                if a.count(x) not in [2, 4]:
                    break
            else:
                return True

        # 十三幺检查
        if set(a) == {1, 9, 11, 19, 21, 29, 31, 33, 35, 37, 41, 43, 45}:
            return ['十三幺']

        # 常规和牌检测。
        a1 = a.copy()
        a2 = []  # a2用来存放和牌后分组的结果。
        for x in double:
            a1.remove(x)
            a1.remove(x)
            a2.append((x, x))
            for i in range(int(len(a1) / 3)):
                if a1.count(a1[0]) == 3:
                    # 列表移除，可以使用remove,pop，和切片，这里切片更加实用。
                    a2.append((a1[0],) * 3)
                    a1 = a1[3:]
                # 这里注意，11,2222,33，和牌结果22,123,123，则连续的3个可能不是相邻的
                elif a1[0] in a1 and a1[0] + 1 in a1 and a1[0] + 2 in a1:
                    a2.append((a1[0], a1[0] + 1, a1[0] + 2))
                    a1.remove(a1[0] + 2)
                    a1.remove(a1[0] + 1)
                    a1.remove(a1[0])
                else:
                    a1 = a.copy()
                    a2 = []
                    break
            else:
                return True
        else:
            return False


    def kind_check(self, hand_cards, pgcards, angang_num, lastcard = None):
        '''
        番型检测
        '''
        print('angang_num:', angang_num)
        handcards = hand_cards.copy()
        handcards.pop('花')

        numlist = []
        for cards in handcards.values():
            numlist.extend(cards)
        numlist = sorted(numlist)

        pg = pgcards.copy()
        pg = pg['viewable'] + pg['unviewable']
        print('pggggggggggg:', pg)
        for i in range(len(pg) - 1, -1, -1):
            if pg and pg[i] < 0:
                pg.remove(pg[i])

        kinds = []
        c_zi = Counter(handcards['字'])
        c_pg = Counter(pg)
        gang_num = sum([i == 4 for i in c_pg.values()])
        facai = 43  # 发财
        feng = self.maj.zi_range[:4]  # 风
        jian = self.maj.zi_range[4:]  # 箭
        c_numlist = Counter(numlist)
        all_num = numlist + pg
        all_num.sort()
        c_allnum = Counter(all_num)
        l_zi_kezi = [k for k, v in c_zi.items() if v == 3] + \
                    [k for k, v in c_pg.items() if k in self.maj.zi_range]  # 字刻子列表

        anke_num = sum([v == 3 for v in c_numlist.values()]) + angang_num
        anke_num -= 1 if anke_num > 0 and sum([v == 2 for v in c_numlist.values()]) not in (1,4) else 0 # 4 5 5 5 6 7 7 8 8 9 9
        # 考虑特殊形式：2 3 4 5 5 5 6 6 6 7 7 8 8 8 / 1 2 3 4 5 5 5 6 6 6 7 7 8 8
        if anke_num >= 2 and sum([v == 2 for v in c_numlist.values()]) == 2:
            anke_num -= 2
        kezi_num = anke_num + len(c_pg) - angang_num
        for k, v in c_numlist.items():
            if v == 3 and lastcard == k:
                anke_num -= 1

        print('hhh', anke_num, kezi_num)

        # 九宝莲灯
        for type, cards in handcards.items():
            if len(cards) == 14 and all(i % 10 == 1 for i in cards[:3]) and all(i % 10 == 9 for i in cards[-3:]):
                if set([i % 10 for i in cards]) == set(range(1, 10)):
                    return ['九宝莲灯']

        # 连七对
        for type, cards in handcards.items():
            c = Counter(cards)
            if len(cards) == 14 and all(v == 2 for k, v in c.items()) and cards[-1] - cards[0] == 6:
                return ['连七对']

        # 大四喜
        if sum([i in l_zi_kezi for i in feng]) == 4:
            kinds.append('大四喜')

        # 大三元
        if sum([i in l_zi_kezi for i in jian]) == 3:
            kinds.append('大三元')

        # 十八罗汉
        if gang_num == 4:
            kinds.append('十八罗汉')

        # 绿一色
        if not handcards['筒'] and not handcards['万'] and not any(i != facai for i in handcards['字']):
            if (handcards['字'] or facai in pg) and all(
                    i in (12, 13, 14, 16, 18, facai) for i in all_num):
                kinds.append('绿一色')

        # 豪华七小对
        if len(numlist) == 14 and len(c_numlist) <= 6 and all(i in (2, 4) for i in c_numlist.values()):
            kinds.append('豪华七小对')

        # 清幺九
        if all(i % 10 in (1, 9) for i in all_num):
            kinds.append('清幺九')

        # 四暗刻
        if anke_num == 4:
            kinds.append('四暗刻')

        # 小四喜
        if sum([i in feng for i in l_zi_kezi]) == 3 and \
                any(v == 2 for k, v in c_zi.items() if k in feng):
            kinds.append('小四喜')

        # 小三元
        if sum([i in jian for i in l_zi_kezi]) == 2 and \
                any(v == 2 for k, v in c_zi.items() if k in jian):
            kinds.append('小三元')

        # 字一色
        if all(i >= 31 for i in all_num):
            kinds.append('字一色')

        # 一色双龙会
        if not handcards['字'] and not pg and numlist[-1] - numlist[0] == 8:
            if [i % 10 for i in numlist] == [1, 1, 2, 2, 3, 3, 5, 5, 7, 7, 8, 8, 9, 9]:
                return ['一色双龙会']

        # 混幺九
        if all(i in [1, 9, 11, 19, 21, 29] + self.maj.zi_range for i in all_num):
            if any(i in [1, 11, 21] for i in all_num) and any(i in [9, 19, 29] for i in all_num) and \
                    any(i in self.maj.zi_range for i in all_num):
                kinds.append('混幺九')

        # 三杠
        if gang_num == 3:
            kinds.append('三杠')

        # 清一色
        if all_num[-1] < 31:
            for rng in (self.maj.tong_range, self.maj.tiao_range, self.maj.wan_range):
                if all_num[-1] in rng and all_num[0] not in rng:
                    break
            else:
                kinds.append('清一色')

        # 七小对
        if len(numlist) == 14 and all(i == 2 for i in c_numlist.values()):
            kinds.append('七小对')

        # 全小/全中/全大/全双刻
        if not handcards['字']:
            if all(i % 10 <= 3 for i in all_num):
                kinds.append('全小')
            elif all(3 < i % 10 <= 6 for i in all_num):
                kinds.append('全中')
            elif all(i % 10 > 6 for i in all_num):
                kinds.append('全大')
            elif all(i & 1 == 0 for i in all_num) and kezi_num == 4:
                kinds.append('全双刻')

        # 清龙
        for type, cards in handcards.items():
            if len(cards) >= 9 and set(i % 10 for i in cards) == set(range(1, 10)) and \
                    all(v in (1, 3) for v in Counter(cards).values()):
                kinds.append('清龙')
                break

        # 三暗刻
        if anke_num == 3:
            kinds.append('三暗刻')

        # 三同刻
        l = [k for k, v in c_numlist.items() if v == 3] + list(c_pg.keys())
        c = Counter([i % 10 for i in l])
        for k, v in c.items():
            if v == 3:
                for i in range(3):  # 1 2 2 2 3 12 12 12 22 22 22
                    if c_numlist[10 * i + k - 1] == 1 and c_numlist[10 * i + k + 1] == 1:
                        break
                else:
                    kinds.append('三同刻')

        # 三风刻
        if sum([i in l_zi_kezi for i in feng]) == 3:
            kinds.append('三风刻')

        # 碰碰胡
        if kezi_num == 4:
            kinds.append('碰碰胡')

        # 混一色
        l = [i for i in all_num if i not in self.maj.zi_range]
        l.sort()
        for rng in (self.maj.tong_range, self.maj.tiao_range, self.maj.wan_range):
            if l[-1] in rng and l[0] not in rng:
                break
        else:
            kinds.append('混一色')

        # 双暗杠
        if self.angang_num == 2:
            kinds.append('双暗杠')

        # 双箭刻
        if sum([i in l_zi_kezi for i in jian]) == 2:
            kinds.append('双箭刻')

        # 五门齐
        sum_func = lambda x: sum([i in x for i in all_num])
        t = (self.maj.tong_range, self.maj.tiao_range, self.maj.wan_range, feng, jian)
        l = [sum_func(i) for i in t]
        if all(i >= 2 for i in l) and sum([i == 2 for i in l]) == 1:
            kinds.append('五门齐')

        # 推不倒
        l = (1, 2, 3, 4, 5, 8, 9, 12, 14, 15, 16, 18, 19, 45)
        if all(i in l for i in all_num):
            kinds.append('推不倒')

        if kinds:
            absolute_relation = {'大四喜': ['混一色', '碰碰胡'], '小四喜': ['混一色', '三风刻'], '绿一色': ['混一色'],
                                 '四暗刻': ['三暗刻', '碰碰胡'], '混幺九': ['碰碰胡'], '小三元': ['双箭刻'],
                                 '全双刻': ['碰碰胡'], '清一色': ['混一色'], '字一色': ['碰碰胡']}
            for i in kinds:
                if i in absolute_relation:
                    for j in absolute_relation[i]:
                        if j in kinds:
                            kinds.remove(j)
            return kinds
        else:
            return ['鸡胡']


if __name__ == '__main__':
    # hand_cards = {'筒子':[],'条子':['1条','1条','1条','2条','3条','4条','5条','5条','6条','7条','8条','9条','9条','9条'],'万字':[],'字牌':[]}
    # hand_cards = {'筒子':[],'条子':['2条','2条','2条','2条','3条','3条','4条','4条','5条','5条','6条','6条','8条','8条'],'万字':[],'字牌':[]}
    # hand_cards = {'筒子':['1筒','9筒'],'条子':['1条','9条'],'万字':['1万','9万'],'字牌':['东风','南风','西风','北风',cc]}
    # hand_cards = {'筒子':['5筒','5筒'],'条子':[],'万字':[],'字牌':[]}
    # hand_cards = {'筒子': ['1筒', '1筒', '1筒'], '条子': ['1条', '1条', '1条', '9条', '9条', '9条'],
    #               '万字': ['5万', '5万', '5万'], '字牌': ['发财', '发财']}
    # hand_cards = {'筒子': ['1筒', '1筒', '1筒'], '条子': [ '9条', '9条', '9条'],
    #               '万字': [], '字牌': ['发财', '发财','发财','白板','白板']}
    # hand_cards = {'筒子': [], '条子': [],'万字': [], '字牌': ['发财', '发财','发财','东风','东风','东风','南风','南风','西风','西风','西风']}
    # hand_cards = {'筒子': [], '条子': ['1条', '2条', '3条'], '万字': [],
    #               '字牌': [ '南风', '南风']}
    # hand_cards = {'筒子': ['5筒','5筒','7筒','7筒'],
    #               '条子': ['2条', '2条', '5条', '5条', '7条', '7条'], '万字': [], '字牌': ['东风','东风','南风','南风']}
    # hand_cards = {'筒子': [],
    #               '条子': ['1条', '2条', '3条', '4条', '5条','6条', '7条', '8条', '9条'], '万字': [], '字牌': ['东风','东风']}
    # hand_cards = {'筒子': [],
    #               '条子': ['2条', '2条', '2条', '4条', '5条','6条'], '万字': [], '字牌': ['发财','发财']}
    # hand_cards = {'筒子': ['1筒', '2筒', '3筒'], '条子': [],
    #                             '万字': ['5万', '5万', '5万'], '字牌': ['发财', '发财']}

    # hand_cards = {'筒子': ['1筒', '1筒', '1筒'], '条子': ['1条', '1条', '1条', '9条', '9条', '9条'],
    #               '万字': ['5万', '5万', '5万'], '字牌': ['发财', '发财'], '花牌': []}
    # pgcards = {'viewable': ['1花','1花','3花','3花',], 'unviewable': []}
    #
    # hand_cards = {'筒子': ['2筒','2筒','2筒','2筒','3筒','3筒','5筒','5筒',], '条子': ['7条', '7条','3条', '3条', '3条', '3条'], '万字': [],
    #               '字牌': [], '花牌': []}
    # pgcards = {'viewable': ['1花','1花','3花','4花','3花',], 'unviewable': []}
    #
    # player = Player('test', '1')
    # player.hand_cards = hand_cards
    # print(player.is_hu(hand_cards))
    # cards = [i[0] for i in cards]
    # print(cards)
    # l1 = [str(i) for i in range(2,9)]
    # f=all(i in cards for i in l1)
    # print(f)
    # c = Counter(cards)
    # print(c)
    # print(all(v==2 for k,v in c.items()))
    # print(player.is_hu(hand_cards))
    # kind = player.kind_check(hand_cards, pgcards, 0, '7条')
    # print(kind)

    from pprint import pprint

    a = '一 二 三 四 五 六 七 八 九'.split(' ')
    l1 = [i + '筒' for i in a]
    l2 = [i + '条' for i in a]
    l3 = [i + '万' for i in a]
    l4 = ['东风', '南风', '西风', '北风', '红中', '发财', '白板']
    l5 = ['一花', '二花', '三花', '四花']
    # print(l1+l2+l3+l4+l5)
    maj = Mahjong()
    # pprint(maj.cards_map)
    # print(len(maj.cards_map))
    # print(len(maj.all_cards))
    # print(maj.all_cards)
    # print(maj.cards_num[0:9])
    # print(maj.cards_num[9:18])
    # print(maj.cards_num[18:27])
    # print(maj.cards_num[27:34])
    # print(maj.cards_num[34:])
    player = Player('test', 1)
    cards = maj.shuffle_cards()
    print(player.get_card(cards))
    hc = {'筒': [2,2,2,2], '条': [12,12,12,12], '万': [22,22,], '字': [31,31,41,41], '花': []}
    print(player.is_hu(hc))
    pg_cards = {'viewable': [], 'unviewable': []}
    print(player.kind_check(hc, pg_cards, 0,))
