
def test(f):
    print(f.__name__)

def func():
    print('hello')

test(func)