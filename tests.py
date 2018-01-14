from data import rome_units, gaul_units, german_units
units  = {}
units.update(rome_units)
units.update(gaul_units)
units.update(german_units)


def up(value, level, crop):
    return value + (value + 300 * crop / 7.0) * (1.007 ** level - 1)

def p(l):
    for i in l:
        print(i)

u = [(i, j[0]/j[7], j[1]/j[7], j[2]/j[7], sum([j[3], j[4], j[5], j[6]])/j[7], j[7]) for i,j in units.items()]

print('Horse def:')
a = sorted([(i[0], i[3], i[4]/i[3], i[5]) for i in u], key = lambda x: x[1])
p(a)


print('Army def:')
a = sorted([(i[0], i[2], i[4]/i[2], i[5]) for i in u], key = lambda x: x[1])
p(a)


print('Upped Horse def:')
a = sorted([(i[0], up(i[3], 20, i[5]), i[4]/i[3], i[5]) for i in u], key = lambda x: x[1])
p(a)


print('Upped Army def:')
a = sorted([(i[0], up(i[2], 20, i[5]), i[4]/i[2], i[5]) for i in u], key = lambda x: x[1])
p(a)



print('Army atack:')
a = sorted([(i[0], i[1], i[4]/i[1] if i[1] else 0, i[5]) for i in u], key = lambda x: x[1])
p(a)

print('Upped Army atack:')
a = sorted([(i[0], up(i[1], 20, i[5]), i[4]/i[1] if i[1] else 0, i[5]) for i in u], key = lambda x: x[1])
p(a)


#players = ['vyk.', 'VANDAL', 'Fl0k', 'Кельталаз', 'scrw', 'иван777', 'Varrkan', 'Drknss', 'РУБИ', 'сова', 'Aldaris', 'колян7', 'romario7821', 'SirSlavko', 'adler', 'sirboss', 'BIGTAN', 'Чужая', 'Abral', 'FSWL', 'zesar777', 'MarkLucius', 'TeaKiLLeR', 'габен', 'ruslan561067', 'радио', 'misterproper', 'dimstikYU', 'Спрут', 'Schmid_Ts', 'gradUS_xD', 'Карамбуль', 'Gorb', 'kam13', 'mig68', 'amadicus', 'djoker', 'bratishka', 'диман', 'ttr2', 'Bolton', 'Мэриэнн', 'Tashka', 'shehen', 'поп', 'стилус', 'Dex', 'scrw', 'feziks', 'sirboss', 'Steve_Vai', 'Rus42SVD', 'zusca', 'Mantikora', 'tovchiga', 'MaMa_XoXoTaLa', 'Бурат', 'колхоз', 'ploki', 'Kat', 'Ларс', 'небо', 'OkMonday', 'swetik33', 'BoonHead', 'krabis', 'alex_l_1989', 'Ванчовски', 'Clipper', 'Dankow58', 'COMYDA', 'bezdelnik', 'etre', 'vfndq', 'pix', 'oxy', 'zamdir', 'Михаилорковка', 'Цензор', 'stas', 'Ars', 'Xrystt', 'kora', 'Udud', 'safka', 'Станислав777', 'bOB', 'Иvan', 'alexs76', 'byzon80', 'Люстра', 'Pandora', 'Zero', 'Vitamin', 'GuzLo', 'sax4', 'Eiteri', 'yadren4', 'Dmitrich12', 'mops', 'fischer', 'Juls', 'skrol', 'Maxon666', 'zamdir', 'Sir', 'Neuron89', 'NiKToc', 'winzip', 'GKO_Never', 'ДЕЙВ', 'Sibiryak', 'Limited', 'anzelika_', 'dyens', 'warer', 'Salamandr', 'utro', 'Sкif-next', 'Dictator']
#
#from utils import get_friends
#from db import session, WorldVillage
#
#friends = [i.player_name for i in get_friends()]
#f_all = {i.player_name: i for i in get_friends()}
#
#players = set(players)
#friends = set(friends)
#
#out =  players.difference(friends)
#for i in out:
#    village = session.query(WorldVillage).filter_by(player_name=i).first()
#    if village is None:
#        print('%s: None' % i)
#    else:
#        if village.alliance_name:
#            print('%s: %s' % (i, village.alliance_name))
#        else:
#            print('%s: Без альянса' % i)
#
#
#
#out =  friends.difference(players)
#print('В альянсе, но не в gt. Всего %s' % len(out))
#print([i for i in out])

