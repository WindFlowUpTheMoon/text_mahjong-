每次发牌都要进行以下判断：
    是否补杠，是的话牌堆尾部再摸一张
    是否暗杠，是的话牌堆尾部再摸一张
    是否自摸，是的游戏结束进行结算
若都没有，则向玩家发送打牌消息

每次有人打牌都要进行以下判断：
    是否碰，是的话要打掉一张
    是否吃杠，是的话牌堆尾部再摸一张
    是否点炮，是的话游戏结束进行结算
若都没有，则发牌给下一个玩家

GameServer作为服务端，玩家为客户端，服务端给客户端发送指令，客户端根据指令发送请求

可碰不一定可杠，可杠一定可碰，但按照利益优先度考虑，叼毛们能杠绝对不碰，因此暂时可不考虑杠还是碰的问题

正常输出玩家自个牌面相关信息，输入c键可查看其他玩家和牌面信息

连接维护，若玩家断线可根据uniq_id重连