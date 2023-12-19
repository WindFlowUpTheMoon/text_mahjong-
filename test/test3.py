import re

text = """
自营账户开户通知书（非法人产品用）
产品名称   开心麻花
根据你巴拉巴拉：
巴拉巴拉
"""

pattern = r'产品名称(?::|：)?\s*(.*?)[\n.]'
match = re.search(pattern, text, re.S)

if match:
    product = match.group(1)
    print("匹配到的产品名称", product)
else:
    print("未匹配到产品名称")