# coding=utf-8
import copy
import heapq
import numpy as np
import time

# 最终状态
node_num = 0
end_state = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 0)

# 初始状态测例集
init_state = [
    # (1, 15, 7, 10, 9, 14, 4, 11, 8, 5, 0, 6, 13, 3, 2, 12),
    # (1, 7, 8, 10, 6, 9, 15, 14, 13, 3, 0, 4, 11, 5, 12, 2),
    # (5, 6, 4, 12, 11, 14, 9, 1, 0, 3, 8, 15, 10, 7, 2, 13),
    # (14, 2, 8, 1, 7, 10, 4, 0, 6, 15, 11, 5, 9, 3, 13, 12),
    (12, 8, 11, 9, 5, 13, 14, 1, 3, 15, 2, 4, 6, 7, 10, 0),
    # (11, 3, 1, 7, 4, 6, 8, 2, 15, 9, 10, 13, 14, 12, 5, 0),  # Dif_IDA_Starresult.txt
    # (14, 10, 6, 0, 4, 9, 1, 8, 2, 3, 5, 11, 12, 13, 7, 15),
    # (0, 5, 15, 14, 7, 9, 6, 13, 1, 2, 12, 10, 8, 11, 4, 3),
    # (6, 10, 3, 15, 14, 8, 7, 11, 5, 1, 0, 2, 13, 12, 9, 4)

]

# 方向数组
dx = [0, -1, 0, 1]
dy = [1, 0, -1, 0]

OPEN = []

CLOSE = set()  # close表，用于判重

path = []


def print_path(node):
    if node.parent != None:
        print_path(node.parent)
    path.append(node.state)
    return path


# 状态结点
class Node(object):
    def __init__(self, gn = 0, hn = 0, state = None, parent = None):
        self.gn = gn
        self.hn = hn
        self.fn = self.gn + self.hn
        self.state = state
        self.parent = parent


    def __lt__(self, node):  # heapq的比较函数
        if self.fn == node.fn:
            return self.gn > node.gn
        return self.fn < node.fn


# 曼哈顿距离（注意：不需要计算‘0’的曼哈顿值，否则不满足Admittable)
def manhattan(state):
    M = 0
    for t in range(16):
        if state[t] == end_state[t] or state[t] == 0:
            continue
        else:
            x = (state[t] - 1) // 4  # 最终坐标
            y = state[t] - 4 * x - 1
            dx = t // 4  # 实际坐标
            dy = t % 4
            M += (abs(x - dx) + abs(y - dy))
    return M


def generateChild():  # 生成子结点
    movetable = []  # 针对数码矩阵上每一个可能的位置，生成其能够移动的方向列表
    for i in range(16):
        x, y = i % 4, i // 4
        moves = []
        if x > 0: moves.append(-1)  # 左移
        if x < 3: moves.append(+1)  # 右移
        if y > 0: moves.append(-4)  # 上移
        if y < 3: moves.append(+4)  # 下移
        movetable.append(moves)


    def children(state):
        idxz = state.index(0)  # 寻找数码矩阵上0的坐标
        l = list(state)  # 将元组转换成list，方便进行元素修改
        for m in movetable[idxz]:
            l[idxz] = l[idxz + m]  # 数码交换位置
            l[idxz + m] = 0
            yield (1, tuple(l))  # 临时返回
            l[idxz + m] = l[idxz]
            l[idxz] = 0


    return children


def A_star(start, Fx):  # start 为起始结点，Fx为启发式函数（这里采用曼哈顿距离）
    root = Node(0, 0, start, None)  # 参数分别为 gn, hn,state, parent

    OPEN.append(root)
    heapq.heapify(OPEN)

    CLOSE.add(start)

    while len(OPEN) != 0:
        top = heapq.heappop(OPEN)
        global node_num  # 扩展的结点数
        node_num += 1
        if top.state == end_state:  # 目标检测
            return print_path(top)  # 对路径进行打印

        generator = generateChild()  # 生成子结点
        for cost, state in generator(top.state):
            if state in CLOSE:  # CLOSE表为set容器，这里进行环检测
                continue
            CLOSE.add(state)
            child = Node(top.gn + cost, Fx(state), state, top)
            heapq.heappush(OPEN, child)  # 将child加入优先队列中


if __name__ == '__main__':
    f = open('DifAStar_Result_M.txt', 'w')
    for idx, test in enumerate(init_state):
        time1 = time.time()
        PATH = np.asarray(A_star(test, manhattan))
        time2 = time.time()

        test = np.asarray(test)

        for i, p in enumerate(PATH):  # 路径打印
            if i == 0:
                print("15-Puzzle initial state:")
                print(p)
                f.write("15-Puzzle initial state:\n")
                f.write('%s\n\n' % (str(p)))
            else:
                print('Move: %d' % (i))
                print(p)
                f.write('Move: %d \n' % (i))
                f.write("%s \n" % (str(p)))

        print('Test %d, Total Step %d' % (idx + 1, len(path) - 1))
        print("Used Time %f" % (time2 - time1), "sec")
        print("Expanded %d nodes" % (node_num))

        f.write('Test %d, Total Step %d \n' % (idx + 1, len(path) - 1))
        f.write("Used Time %f sec\n" % (time2 - time1))
        f.write("Expanded %d nodes\n\n" % (node_num))

        OPEN.clear()
        CLOSE.clear()
        path.clear()
