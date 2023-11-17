
def f1(x):
    print('hello',x)


def f2(f):
    f(3)
    print('world')


f2(f1)