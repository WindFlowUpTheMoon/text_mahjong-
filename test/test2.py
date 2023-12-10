import pandas as pd


class Excel:
    def __init__(self, path, header_num=1):
        self.path = path
        self.header_num = header_num
        self.df = pd.read_excel(self.path, header = list(range(self.header_num)))


    # 复合表头根据列名获取相应列节点元组
    def get_column_tuple(self, target_column):
        header_columns = self.df.columns.tolist()
        for i in header_columns:
            if target_column in i:
                return i


    # 找出数组里面的所有叶子节点
    def find_leaf_nodes(self, arr):
        root_nodes = {i: [] for i in arr if '.' not in i}
        for i in arr:
            for node in root_nodes:
                if node in i and node != i:
                    root_nodes[node].append(i)
        print(root_nodes)
        for k, v in root_nodes.items():
            if v:
                tmp = [i.split('.') for i in v]
                l = [len(i) for i in tmp]
                max_len = max(l)
                for i in range(len(l)-1, -1, -1):
                    if l[i] < max_len:
                        v.pop(i)
        target_nodes = []
        for i in root_nodes.values():
            target_nodes.extend(i)
        return target_nodes


    # 将target_nodes对应的行保存到指定excel文件
    def save2excel(self, target_nodes, target_path=None):
        lines = []
        for node in target_nodes:
            lines.append(self.df[self.df.iloc[:, 0] == node])
        merge_lines = pd.concat(lines)
        merge_lines.to_excel(target_path, index=True, )


if __name__=='__main__':
    excel_path = r'D:\hk\kayakwise\ziguan\276030估值表.xls'
    excel = Excel(excel_path, 7)
    column_tuple = excel.get_column_tuple('科目代码')
    if column_tuple:
        column_df = excel.df[column_tuple]
    else:
        print('找不到对应列')
    columns = [i for i in column_df.tolist() if isinstance(i, str)]
    print(columns)
    target_nodes = excel.find_leaf_nodes(columns)
    print(target_nodes)
    excel.save2excel(target_nodes, r'D:\hk\kayakwise\ziguan\276030估值表_extract.xlsx')