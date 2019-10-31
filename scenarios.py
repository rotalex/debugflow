a = 2
b = 3
c = a * b + a ** b
#$#$
def sum(a, b):
	"1, 2"
	rez = a + b
	return rez
#$#$
def shift(lst, delta):
	"[1, 2, 3, 4], 3"
	for i in range(len(lst)):
		lst[i] += delta
	lst.append(delta)
	return lst
#$#$
