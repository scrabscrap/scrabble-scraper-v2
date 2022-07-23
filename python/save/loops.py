

from itertools import product

for i, j in product(range(1, 11), range(1, 11)):
    print(f'({i},{j})')
