
try:
    print(3/0)
except Exception as e:
    print(type(e), str(e))