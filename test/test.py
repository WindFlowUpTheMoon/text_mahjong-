

l=['1筒', '发财', '发财', '西风', '6万', '9万', '2万', '红中', '4万', '2筒', '9条', '南风', '2条', '7筒', '2筒', '9筒', '4筒', '发财', '3万', '北风', '1万', '红中', '3筒', '1万', '1筒', '4万', '4万', '红中', '发财', '2条', '1万', '5条', '2筒', '红中', '9万', '北风', '南风', '8万', '5条', '1筒', '9筒', '2筒', '白板', '3筒', '5万', '东风', '2条', '6万', '2条', '北风', '北风', '8筒', '6条', '3筒']


from collections import Counter
from pprint import pprint

def print_pgcards(l):
    l.sort()
    c = Counter(l)
    maj_map = {'筒子':[],'条子':[],'万字':[],'字牌':[]}
    for k, v in c.items():
        if k[1] == '筒':
            maj_map['筒子'].append((k,v))
        elif k[1] == '条':
            maj_map['条子'].append((k,v))
        elif k[1] == '万':
            maj_map['万字'].append((k,v))
        else:
            maj_map['字牌'].append((k,v))
    pprint(maj_map)


def hepai(a):
    '''
    胡牌检测
    万：1-9，条：11-19，饼：21-29，东西南北风：31,33,35,37，中发白：41,43,45。
    '''
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
            print('i-',i)
            if a1.count(a1[0]) == 3:
                # 列表移除，可以使用remove,pop，和切片，这里切片更加实用。
                a2.append((a1[0],) * 3)
                a1 = a1[3:]
                print('1111',a1)
            elif a1[0] in a1 and a1[0] + 1 in a1 and a1[0] + 2 in a1:  # 这里注意，11,2222,33，和牌结果22,123,123，则连续的3个可能不是相邻的。
                a2.append((a1[0], a1[0] + 1, a1[0] + 2))
                a1.remove(a1[0] + 2)
                a1.remove(a1[0] + 1)
                a1.remove(a1[0])
                print('2222',a1)
            else:
                a1 = a.copy()
                a2 = []
                print('重置')
                break
        else:
            # print('和牌成功,结果：',a2)
            return True
    # 如果上述没有返回和牌成功，这里需要返回和牌失败。
    else:
        # print('和牌失败：遍历完成。')
        return False

a=[22,22,22,24,25,26,27,27,27,28,29]
print(hepai(a))

def handcards2numlist():
    '''
    将手牌转为序数列表
    '''
    d={'筒子':['1筒','1筒','2筒','2筒'],'条子':['1条','3条'],'万字':['4万'],'字牌':['东风','西风'],'花牌':[]}
    tong_map = {str(i)+'筒':i for i in range(1,10)}
    tiao_map = {str(i-10)+'条':i for i in range(11,20)}
    wan_map = {str(i-20)+'万':i for i in range(21,30)}
    s = '东风 南风 西风 北风 红中 白板 发财'
    inl = [31,33,35,37,41,43,45]
    zi_map = dict(zip(s.split(' '),inl))

    mmap = dict(**tong_map,**tiao_map,**wan_map,**zi_map)
    l=[]
    for k,v in d.items():
        l.extend([mmap[i] for i in v])
    return l

# print(handcards2numlist())


# l = {'筒子':['1筒','1筒','2筒','2筒'],'条子':['1条','3条'],'万字':['4万'],'字牌':['东风','西风'],'花牌':[]}
# mmap = {'筒': '筒子', '条': '条子', '万': '万字', '花': '花牌'}
# card = '4筒'
# cardtype = mmap[card[1]]
# print(cardtype)
# l[cardtype].append(card)
# print(l)

# from copy import deepcopy
#
# l = {'a':[1,2,3],'b':[4,5,6]}
# a = deepcopy(l)
# a['a'].append(3)
# print(a,l)