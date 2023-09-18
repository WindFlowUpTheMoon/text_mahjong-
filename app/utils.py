def insert_card(table_cards, hand_cards, cards, abb_map):
    card = table_cards.pop(0)
    if card in cards['字牌']:
        hand_cards['字牌'].append(card)
    elif card[1] in abb_map:
        hand_cards[abb_map[card[1]]].append(card)


class LastLeftCard:
    def __init__(self, player, card):
        self.player = player
        self.card = card


def print_playercards(player):
    '''
    漂亮打印玩家手牌和碰/杠后的牌
    '''
    handcards, pgcards = player.hand_cards, player.pg_cards

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
    print(' ' * 19, end = '')
    for i in lp1:
        print(i + ' ', end = '')
    print()
    for i in l2:
        print(i + ' ', end = '')
    print(' ' * 18, end = '')
    for i in lp2:
        print(i + ' ', end = '')
    print()


if __name__ == '__main__':
    hc = {'筒子': [], '条子': ['1条', '3条', '3条'], '万字': ['1万', '1万', '4万', '9万', '9万'], '字牌': ['东风', '白板'],
          '花牌': ['2花']}
    pgc = ['8筒', '8筒', '8筒']
    print_playercards(hc, pgc)
