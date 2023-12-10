from ..client import start
from os import path


if __name__ == '__main__':
    # print(path.abspath(__file__))
    curpath = path.abspath(__file__)
    try:
        start(curpath)
    except:
        print_exc()