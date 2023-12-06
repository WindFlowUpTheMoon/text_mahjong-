import msvcrt
import time

# 清空输入缓冲区
def clear_buffer():
    while msvcrt.kbhit():
        msvcrt.getch()

# 等待3秒
print("等待3秒...")
time.sleep(3)

# 清空任何在等待期间输入的内容
clear_buffer()

# 现在接收用户输入
user_input = input("请输入: ")
print(f"您输入的内容是: {user_input}")