###
a = 2
b = 3
c = a * b + a ** b
###
#$#$
### 1, 2
def sum(a, b):
	rez = a + b
	return rez
###
#$#$
### [1, 2, 3, 4], 3
def shift(lst, delta):
	for i in range(len(lst)):
		lst[i] += delta
	lst.append(delta)
	return lst
###
