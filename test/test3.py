from collections import Counter

l = [1,1,2,3,4,3,5,2,1]
c = Counter(l)
print(c.keys())
print(list(c.keys()))