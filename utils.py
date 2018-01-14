from db import WorldVillage
from db import session
from datetime import timedelta
from config import ALLY_AIDS


def get_friends():
    friends = []
    for aid in ALLY_AIDS:
        friends.extend(list(session.query(WorldVillage).filter_by(aid=aid).all()))
    return friends


description = '''
Расстояние до цели:
=(МИН(ABS(E3-A8);801-ABS(E3-A8))^2+МИН(ABS(E4-A9);801-ABS(E4-A9))^2)^(1/2) (с) Romas, Atsijungti где,
E3 - координата атакующего Х
Е4 – координата атакующего У
А8 – координата жертвы Х
А9 – координата жертвы У

Время пути:
для 3.6: =((ЕСЛИ(E7>30;(E7-30)/(1+0,1*E$5)+30;E7))/$A$2)/24
для Т4: =((ЕСЛИ(E7>20;(E7-20)/(1+0,1*E$5)+20;E7))/$A$2)/24
где,
Е7 – расстояние до цели
Е5 – уровень арены
А2 – скорость самого медленного юнита (катапульты)
'''


def distance(x1, y1, x2, y2):
    x1 = float(x1)
    x2 = float(x2)
    y1 = float(y1)
    y2 = float(y2)
    d = (min(abs(x1 - x2), 801 - abs(x1 - x2))**2  + min(abs(y1 - y2), 801 - abs(y1 - y2))**2) ** 0.5
    return d



def travel_time(x1, y1, x2, y2, v, arena=1):
    d =  distance(x1, y1, x2, y2)
    if d > 20:
        t_time = ((d - 20) / (1 + 0.1 * arena) + 20) / v
    else:
        t_time = d / v
    return t_time


def get_help(x, y, atack_timedelta):
    friends = get_friends()
    helpers = []
    for friend in friends:
        if friend.x == x and friend.y == y:
            continue
        if friend.population_now.population < 150:
            continue
        if friend.tid == 1:
            v = 6
        elif friend.tid == 2:
            v = 7
        elif friend.tid == 3:
            v = 7
        else:
            v = 6
        help_time = timedelta(hours=travel_time(x, y, friend.x, friend.y, v))
        reaction_time = timedelta(minutes=5)
        if atack_timedelta <= help_time + reaction_time:
            continue
        helpers.append(friend.player_name)
    return list(set(helpers))



def get_av_friends_help_time(my_x, my_y):
    friends = get_friends()
    counter = 0
    travel_times = []
    for friend in friends:
        if friend.x == my_x and friend.y == my_y:
            continue
        counter+=1
        travel_times.append(travel_time(my_x, my_y, friend.x, friend.y, 5))
    return sum(travel_times) / counter

if __name__ == '__main__':
    #11:44:20
    print('distance dyens - dyens2')
    print(distance(-40, -61, -54, -118))

    print('time dyens - dyens2')
    print(travel_time(-40, -61, -54, -118, 5))

    av_time = get_av_friends_help_time(-40, -61)
    print('help time to dyens')
    print(av_time)

    av_time = get_av_friends_help_time(-54, -118)
    print('help time to dyens2')
    print(av_time)

    av_times = []
    counter = 0
    ps = get_friends()
    min_time = None
    for p in ps:
        counter+=1
        av_time = get_av_friends_help_time(p.x, p.y)
        if min_time is None:
            min_time = (av_time, p)
        if min_time[0] > av_time:
            min_time = (av_time, p)
        av_times.append(av_time)

    print(sum(av_times) / counter)
    print(min_time[0], min_time[1].player_name)



