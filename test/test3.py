import threading
import queue
import time

# 共享的队列
shared_queue = queue.Queue()


# 生产者线程函数
def producer():
    for i in range(1, 6):
        item = f"数据项 {i}"
        shared_queue.put(item)
        print(f"生产者生产了: {item}")
        time.sleep(0.5)


[[3, 11, 8, 9],
 [6, 1, 15, 5],
 [10, 7, 2, 12],
 [4, 14, 13, 0]]


# 消费者线程函数
def consumer():
    while True:
        item = shared_queue.get()
        if item is None:
            break
        print(f"消费者消费了: {item}")
        time.sleep(1)


# 创建生产者和消费者线程
producer_thread = threading.Thread(target = producer)
consumer_thread = threading.Thread(target = consumer)

# 启动线程
producer_thread.start()
consumer_thread.start()

# 等待生产者线程结束
producer_thread.join()

# 添加结束标志到队列，通知消费者线程退出
shared_queue.put(None)

# 等待消费者线程结束
consumer_thread.join()
