

from itertools import product
import json
import os
from config import config

for i, j in product(range(1, 11), range(1, 11)):
    print(f'({i},{j})')

list = [(2, 3), (2, 2), (2, 1), (1, 3), (1, 2), (1, 1), (3, 3), (3, 2), (3, 1)]
print(sorted(list))

scores = dict(A=1, B=3, C=4, D=1, E=1, F=4, G=2, H=2, I=1, J=6, K=4, L=2, M=3, N=1, O=2, P=4, Q=10, R=1, S=1, T=1,
              U=1, V=6, W=3, X=8, Y=10, Z=3, Ä=6, Ö=8, Ü=6, _=0)
bag = dict(A=5, B=2, C=2, D=4, E=15, F=2, G=3, H=4, I=6, J=1, K=2, L=3, M=4, N=9, O=3, P=1, Q=1, R=6, S=7, T=6,
           U=6, V=1, W=1, X=1, Y=1, Z=1, Ä=1, Ö=1, Ü=1, _=2)
tile_list = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
             'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
             'Ä', 'Ö', 'Ü']
filepath = (os.path.dirname(__file__) or '.') + '/img'

tile_config = [scores, bag, tile_list, filepath]

str_scores = json.dumps(scores)
print(str_scores)
str_bag = json.dumps(bag)
print(str_bag)
str_filepath = json.dumps(filepath)
print(str_filepath)
print('---')

lang = config.TILES_LANGUAGE
filepath = config.TILES_IMAGE_PATH
str_scores = config.config.get('en', 'scores')
str_bag = config.TILES_BAG
print(str_scores)
print(str_bag)
print(str_filepath)
print(__file__)
t_scores = json.loads(str_scores)
print(f'type: {type(t_scores)} val:{t_scores}')

# t_scores = dict(str_scores)

warp = [[58., 15.],
        [978., 16.],
        [955., 941.],
        [51., 908.]]
str_warp = json.dumps(warp)
print(str_warp)
w1 = json.loads(str_warp)
print(f'type: {type(w1)} val:{w1}')
