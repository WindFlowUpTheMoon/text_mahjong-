from random import shuffle
from app.utils import LastLeftCard, handcards2numlist
from collections import Counter
from app.config import MINGGANG, ANGANG, PLAYER_INIT_MONEY


class Mahjong:
    def __init__(self):
        self.types = ['筒子', '条子', '万字', '字牌', '花牌']
        self.cards = {self.types[0]: list(range(1, 10)), self.types[1]: list(range(1, 10)),
                      self.types[2]: list(range(1, 10)), \
                      self.types[3]: ['东风', '南风', '西风', '北风', '红中', '发财', '白板'],
                      self.types[4]: [1, 2, 3, 4]}
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
        self.pg_cards = {'viewable':[],'unviewable':[]}  # 碰、杠后的手牌
        self.pg_num = 0  # 碰、杠的次数
        self.angang_num = 0  # 暗杠的次数
        self.money = PLAYER_INIT_MONEY  # 筹码
        self.money_gang = 0 # 杠得到的钱
        self.hu_kind = None  # 胡牌类型
        self.first_getcard = True


    def get_card(self, table_cards):
        '''
        摸牌
        '''
        # nonlocal table_cards
        if not table_cards:
            return 'empty', ''
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
        l = []
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
        if leftcard[1] in self.maj.abb_map:
            type = self.maj.abb_map[leftcard[1]]
        else:
            type = '字牌'
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
        if card_got[1] in self.maj.abb_map:
            type = self.maj.abb_map[card_got[1]]
        else:
            type = '字牌'
        if card_got in self.pg_cards['viewable'] and card_got[1] != '花':
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
        print(card_got, type)
        print(self.hand_cards)
        for i in range(4):
            self.hand_cards[type].remove(card_got)
        self.pg_cards['unviewable'].extend([card_got] * 4)
        self.money_gang += (len(players) - 1) * ANGANG
        for player in players:
            if player != self:
                player.money_gang -= ANGANG


    def is_hu(self, hand_cards):
        '''
        胡牌检测
        筒：1-9，条：11-19，万：21-29，东南西北风：31,33,35,37，中白发：41,43,45。
        '''
        a = handcards2numlist(hand_cards)
        a = sorted(a)
        # print(a)

        # 七星不靠检查
        l = {'东风', '南风', '西风', '北风', '红中', '发财', '白板'}
        ln = []
        if set(hand_cards['字牌']) == l and len(Counter(a)) == 14:
            for type in ('筒子', '条子', '万字'):
                ln.extend(hand_cards[type])
            ln = [i[0] for i in ln]
            if len(Counter(ln)) == 7:
                for type in ('筒子', '条子', '万字'):
                    if not (all(i[0] in ('1', '4', '7') for i in hand_cards[type]) or all(
                            i[0] in ('2', '5', '8') for i in hand_cards[type]) \
                            or all(i[0] in ('3', '6', '9') for i in hand_cards[type])):
                        break
                else:
                    return '七星不靠'

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
        if len(a) == 14:
            gtws = [1, 9, 11, 19, 21, 29, 31, 33, 35, 37, 41, 43,
                    45]  # [1,9,11,19,21,29]+list(range(31,38,2))+list(range(41,46,2)) #用固定的表示方法，计算速度回加快。
            for x in gtws:
                if 1 <= a.count(x) <= 2:
                    pass
                else:
                    break
            else:
                return '十三幺'

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
                elif a1[0] in a1 and a1[0] + 1 in a1 and a1[
                    0] + 2 in a1:  # 这里注意，11,2222,33，和牌结果22,123,123，则连续的3个可能不是相邻的。
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


    def kind_check(self, hand_cards, pgcards, angang_num):
        '''
        番型检测
        '''
        handcards = hand_cards.copy()
        handcards.pop('花牌')

        numlist = handcards2numlist(handcards)
        pg = pgcards.copy()
        pg = pg['viewable'] + pg['unviewable']
        print('pggggggggggg:', pg)
        for i in range(len(pgcards) - 1, -1, -1):
            if pg and pg[i][1] == '花':
                pg.remove(pg[i])

        # 九宝莲灯
        l1 = [str(i) for i in range(2, 9)]
        for type, cards in handcards.items():
            if len(cards) == 14 and all(i[0] == '1' for i in cards[:3]) and all(i[0] == '9' for i in cards[-3:]):
                c = [i[0] for i in cards]
                if all(i in c for i in l1):
                    return '九宝莲灯'

        # 连七对
        for type, cards in handcards.items():
            c = Counter(cards)
            if len(cards) == 14 and all(v == 2 for k, v in c.items()) and int(cards[-1][0]) - int(cards[0][0]) == 6:
                return '连七对'

        # 大四喜
        target = {'东风', '南风', '西风', '北风'}
        s = set(pgcards)
        target -= s
        c = Counter(handcards['字牌'])
        for i in target:
            if c[i] != 3:
                break
        else:
            return '大四喜'

        # 大三元
        target = {'红中', '发财', '白板'}
        s = set(pgcards)
        target -= s
        c = Counter(handcards['字牌'])
        for i in target:
            if c[i] != 3:
                break
        else:
            return '大三元'

        # 十八罗汉
        c = Counter(pgcards)
        if sum([i == 4 for i in c.values()]) == 4:
            return '十八罗汉'

        # 绿一色
        if not handcards['筒子'] and not handcards['万字'] and not any(i != '发财' for i in handcards['字牌']):
            if (handcards['字牌'] or '发财' in pg) and all(
                    i[0] in ('2', '3', '4', '6', '8', '发') for i in handcards['条子'] + pg):
                return '绿一色'

        # 豪华七小对
        c = Counter(numlist)
        if len(numlist) == 14 and len(c) == 6 and all(i in (2, 4) for i in c.values()):
            return '豪华七小对'

        # 清幺九
        # print(pg)
        for i in pg:
            if i[0] not in ('1', '9'):
                break
        else:
            flag = False
            for k, v in handcards.items():
                for j in v:
                    if j[0] not in ('1', '9'):
                        flag = True
                        break
                if flag:
                    break
            else:
                return '清幺九'

        # 四暗刻
        c = Counter(numlist)
        if sum(i == 3 for i in c.values()) == 4 and any(i == 2 for i in c.values()):
            return '四暗刻'

        # 小四喜
        target = {'东风', '南风', '西风', '北风'}
        s = set(pgcards)
        target -= s
        c = Counter(handcards['字牌'])
        l = []
        for i in target:
            l.append(c[i])
        if sum(l) == (2 + (len(target) - 1) * 3):
            return '小四喜'

        # 小三元
        target = {'红中', '发财', '白板'}
        s = set(pgcards)
        target -= s
        c = Counter(handcards['字牌'])
        l = []
        for i in target:
            l.append(c[i])
        if sum(l) == (2 + (len(target) - 1) * 3):
            return '小三元'

        # 字一色
        if all(i >= 31 for i in numlist) and all(i[1] in '花风中财板' for i in pgcards):
            return '字一色'

        # 一色双龙会
        if not handcards['字牌'] and sum([len(handcards[i]) > 0 for i in ('筒子', '条子', '万字')]) == 1:
            for type, cards in handcards.items():
                if cards and [i[0] for i in cards] == ['1', '1', '2', '2', '3', '3', '5', '5', '7', '7', '8', '8', '9',
                                                       '9']:
                    return '一色双龙会'

        # 混幺九
        for i in pg:
            if i[0] not in '19' and i[1] not in '风中财板':
                break
        else:
            flag = False
            for k, v in handcards.items():
                for j in v:
                    if j[0] not in '19' and j[1] not in '风中财板':
                        flag = True
                        break
                if flag:
                    break
            else:
                return '混幺九'

        # 三杠
        c = Counter(pgcards)
        if sum([i == 4 for i in c.values()]) == 3:
            return '三杠'

        # 清一色
        if sum(len(i) > 0 for i in handcards.values()) == 1:
            for type, cards in handcards.items():
                if cards:
                    break
            for i in pg:
                if i[1] != type[0]:
                    break
            else:
                return '清一色'

        # 七小对
        c = Counter(numlist)
        if len(numlist) == 14 and all(i == 2 for i in c.values()):
            return '七小对'

        # 全小/全中/全大/全双刻
        ln0 = []
        for type in ('筒子', '条子', '万字'):
            ln0.extend(handcards[type])
        ln = [i[0] for i in ln0]
        if not handcards['字牌'] and all(i[0] not in '东南西北红发白' for i in pg):
            if all(i in ('1', '2', '3') for i in ln + [j[0] for j in pg]):
                return '全小'
            if all(i in ('4', '5', '6') for i in ln + [j[0] for j in pg]):
                return '全中'
            if all(i in ('7', '8', '9') for i in ln + [j[0] for j in pg]):
                return '全大'
            c1, c2 = Counter(ln0), Counter(pg)
            if all(k[0] in ('2', '4', '6', '8') and v in (2, 3) for k, v in c1.items()) and all(
                    k[0] in ('2', '4', '6', '8') and v in (3, 4) for k, v in c2.items()):
                return '全双刻'

        # 清龙
        if len(numlist) >= 9:
            for type, cards in handcards.items():
                if len(cards) >= 9:
                    l = [j[0] for j in cards]
                    for i in [str(j) for j in range(1, 10)]:
                        if i not in l:
                            break
                    else:
                        return '清龙'

        # 三暗刻
        c = Counter(numlist)
        # 考虑手牌是111 222 45556和111 222 45556 777的情况
        if sum(i == 3 for i in c.values()) == 3 and any(i == 2 for i in c.values()) or \
                sum(i == 3 for i in c.values()) == 4:
            return '三暗刻'

        # 三同刻
        c1, c2 = Counter(ln0), Counter(pg)
        l = [k for k, v in c1.items() if v == 3] + [k for k, v in c2.items() if v in (3, 4)]
        c = Counter([i[0] for i in l])
        if any(i == 3 for i in c.values()):
            return '三同刻'

        # 三风刻
        c1, c2 = Counter(handcards['字牌']), Counter(pg)
        l = [k for k, v in c1.items() if v == 3] + [k for k, v in c2.items() if v in (3, 4)]
        if sum([i[0] in '东南西北' for i in l]) == 3:
            return '三风刻'

        # 碰碰胡
        for type, cards in handcards.items():
            c = Counter(cards)
            if not all(i >= 2 for i in c.values()):
                break
        else:
            return '碰碰胡'

        # 混一色
        for type, cards in handcards.items():
            if cards:
                break
        t = type
        if t != '字牌':
            for type, cards in handcards.items():
                if type != '字牌' and t != type and cards:
                    break
            else:
                if all(i[1] == t[0] for i in pg if i[1] not in '风中财板'):
                    return '混一色'

        # 双暗杠
        if self.angang_num == 2:
            return '双暗杠'

        # 双箭刻
        target = {'红中', '发财', '白板'}
        c1 = Counter(handcards['字牌'])
        c2 = Counter(pg)
        num = 0
        for i in target:
            if c1[i] == 3 or c2[i] == 3:
                num += 1
        if num == 2:
            return '双箭刻'

        # 五门齐
        for type, cards in handcards.items():
            if not cards:
                if type == '字牌':
                    if not any(i[1] in '风中财板' for i in pg):
                        break
                else:
                    if not any(i[1] == type[0] for i in pg):
                        break
        else:
            return '五门齐'

        # 推不倒
        l = (1, 2, 3, 4, 5, 8, 9, 12, 14, 15, 16, 18, 19, 43)
        if all(i in l for i in numlist) and all(i[0] in l for i in pg):
            return '推不倒'

        return '鸡胡'


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
    hand_cards = {'筒子': ['3筒', '3筒', '3筒'], '条子': ['2条', '2条', '2条'], '万字': ['5万', '6万', '6万', '6万', '7万'],
                  '字牌': [], '花牌': []}
    pgcards = ['3花', '3条', '3条', '3条']
    player = Player('test', '1')
    player.hand_cards = hand_cards
    # print(player.is_hu(hand_cards))
    # cards = [i[0] for i in cards]
    # print(cards)
    # l1 = [str(i) for i in range(2,9)]
    # f=all(i in cards for i in l1)
    # print(f)
    # c = Counter(cards)
    # print(c)
    # print(all(v==2 for k,v in c.items()))
    print(player.is_hu(hand_cards))
    kind = player.kind_check(hand_cards, pgcards, 1)
    print(kind)
