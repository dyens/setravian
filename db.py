#!/usr/bin/env python

from config import SQLALCHEMY_DATABASE_URI
from config import CHECK_TRADE_PERIOD
from config import ALLY_AIDS
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import Interval
from sqlalchemy import Text
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from datetime import timedelta
from datetime import date
from sqlalchemy.sql.expression import func
from sqlalchemy.types import TypeDecorator
from sqlalchemy.orm import relationship
from sqlalchemy import or_, and_
import json
import sqlite3
import requests
import email.utils as eut
import dateutil.parser
import logging
from config import HREF


def _to_int(value):
    numbers = [str(i) for i in range(10)]
    valid_symbols = []
    valid_symbols.extend(numbers)
    valid_symbols.append('-')
    if isinstance(value, int):
        return value
    elif isinstance(value, str):
        symbol_list = []
        for symbol in value:
            if symbol in valid_symbols:
                symbol_list.append(symbol)
        return int(''.join(symbol_list))
    else:
        raise ValueError('Wrong type of value: %s' % value)



Base = declarative_base()
engine = create_engine(SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)
session = Session()

class FarmVillage(Base):
    __tablename__ = 'farm_villages'

    id = Column(Integer, primary_key=True)
    x = Column(Integer)
    y = Column(Integer)
    army_string = Column(String) # Легионер:1,Преторианец:2
    from_village = Column(String)
    blocked = Column(Boolean)
    last_atacked = Column(DateTime)
    status = Column(String)

    def __init__(self, x, y, army_string, from_village, blocked=False):
        self.x = x
        self.y = y
        self.army_string = army_string
        self.from_village = from_village
        self.blocked = blocked

    def __repr__(self):
        return '<FarmVillage (%s, %s)>' % (self.x, self.y)

    def delete(self):
        session.delete(self)
        session.commit()

    @staticmethod
    def get_village(x, y):
        return session.query(FarmVillage).filter_by(x=x, y=y).first()

    @staticmethod
    def get_next_to_farm(from_village, available_troops):
        farm_villages = session.query(FarmVillage).filter_by(from_village=from_village, blocked=False).all()

        to_farm = []
        for farm_village in farm_villages:
            army = farm_village.army()
            can_be_farm = True
            for unit, count in army.items():
                available_unit = available_troops.get(unit, None)
                if available_unit is None:
                    can_be_farm = False
                    break
                else:
                    if available_unit < count:
                        can_be_farm = False
                        break
            if can_be_farm is True:
                to_farm.append(farm_village)
        if to_farm:
            return min(to_farm, key=lambda x: x.last_atacked if x.last_atacked else datetime(2000, 1, 1))


        scout_villages = session.query(FarmVillage).filter_by(from_village=from_village, status='NEED_SCOUT').all()
        to_scout = []
        for scout_village in scout_villages:
            army = scout_village.army()
            can_be_scout = True
            for unit, count in army.items():
                available_unit = available_troops.get(unit, None)
                if available_unit is None:
                    can_be_scout = False
                    break
                else:
                    if available_unit < count:
                        can_be_scout = False
                        break
            if can_be_scout is True:
                to_scout.append(scout_village)
        if to_scout:
            return min(to_scout, key=lambda x: x.last_atacked if x.last_atacked else datetime(2000, 1, 1))

        return None


    @staticmethod
    def get_all():
        farm_villages = list(session.query(FarmVillage).all())
        return farm_villages

    @staticmethod
    def add_to_list(x, y,
                   army_string='легионер:5',
                   from_village='dyens'):
        village = FarmVillage(x, y, army_string, from_village)
        village.blocked = True
        session.add(village)
        session.commit()

    @staticmethod
    def del_from_list(x, y):
        village = session.query(FarmVillage).filter_by(x=x, y=y).first()
        if village:
            session.delete(village)
            session.commit()

    def army(self):
        if self.status == 'NEED_SCOUT':
            return {'конный разведчик': 1}
        army_dict = {}
        for army in self.army_string.split(','):
            army_name, army_number = army.split(':')
            army_dict.update({army_name: int(army_number)})
        return army_dict

    def update_last_atack(self):
        if self.status == 'NEED_SCOUT':
            self.status = 'SCOUTED'
        self.last_atacked = datetime.now()
        session.add(self)
        session.commit()


    def block(self):
        self.blocked = True
        session.add(self)
        session.commit()

    def unblock(self):
        self.blocked = False
        session.add(self)
        session.commit()

    def need_scout(self):
        self.status = 'NEED_SCOUT'
        session.add(self)
        session.commit()

    def scouted(self):
        self.status = 'SCOUTED'
        session.add(self)
        session.commit()


    @staticmethod
    def block_all():
        villages = session.query(FarmVillage).all()
        for village in villages:
            village.block()



class Building(Base):
    __tablename__ = 'buildings'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    level = Column(Integer)
    wood = Column(Integer)
    clay = Column(Integer)
    rock = Column(Integer)
    corn = Column(Integer)
    crop = Column(Integer)

    def __init__(self, name, level,
                 wood, clay,
                 rock, corn, crop):
        self.name = name
        self.level = level
        self.wood = wood
        self.clay = clay
        self.rock = rock
        self.corn = corn
        self.crop = crop

    def __repr__(self):
        return '<Building (%s, %s)>' % (self.name, self.level)

    @staticmethod
    def get_by_name_and_level(name, level):
        return session.query(Building).filter_by(name=name, level=level).first()


    @staticmethod
    def set_new_building(name, level,
                         wood, clay,
                         rock, corn, crop):
        buiding = Building(name, level, wood, clay, rock, corn, crop)
        session.add(buiding)
        session.commit()





class Param(Base):
    __tablename__ = 'params'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    value = Column(String)
    village = Column(String)

    def __init__(self, name, value, village=None):
        self.name = name
        self.value = value
        self.village = village

    def __repr__(self):
        return '<Param (%s, %s, %s)>' % (self.name, self.value, self.village)

    @staticmethod
    def get_value(name, village=None):
        param = session.query(Param).filter_by(name=name, village=village).first()
        if param:
            value = param.value
            if value == 'True':
                return True
            elif value == 'False':
                return False
            else:
                return param.value
        else:
            return None

    @staticmethod
    def set_value(name, value, village=None):
        param = session.query(Param).filter_by(name=name, village=village).first()
        if value is True:
            value = 'True'
        elif value is False:
            value = 'False'
        if not param:
            param = Param(name, value, village)
        else:
            param.value = value
        session.add(param)
        session.commit()



class WorldVillage(Base):
    __tablename__ = 'world_villages'

    #ID: Number of the field, starts in the top left corner at the coordinate (-400|400) and ends in the bottom right corner at (400|-400).
    id = Column(Integer, primary_key=True)
    #X: X-Coordinate of the village.
    x = Column(Integer)
    #Y: Y-Coordinate of the village.
    y = Column(Integer)
    #TID: The tribe number. 1 = Roman, 2 = Teuton, 3 = Gaul, 4 = Nature and 5 = Natars
    tid = Column(Integer)
    #VID: Village number. The unique ID for the village.
    vid = Column(Integer)
    #Village: The name of the village.
    village_name = Column(String)
    #UID: The player’s unique ID, also known as User-ID.
    uid = Column(Integer)
    #Player: The player name.
    player_name = Column(String)
    #AID: The alliance’s unique ID.
    aid = Column(Integer)
    #Alliance: The alliance name.
    alliance_name = Column(String)
    #Population: The village’s number of inhabitants without the troops.
    population = relationship("Population")

    def __init__(self, x, y, tid, vid, village_name, uid, player_name, aid, alliance_name):
        self.x = x
        self.y = y
        self.tid = tid
        self.vid = vid
        self.village_name = village_name
        self.uid = uid
        self.player_name = player_name
        self.aid = aid
        self.alliance_name = alliance_name

    @property
    def population_now(self):
        return max([i for i in self.population], key=lambda x: x.actual_time)

    def population_dynamic(self, days=3):
        sorted_populations = sorted([i for i in self.population], key=lambda x: x.actual_time)

        try:
            end_population = sorted_populations[-1].population
        except IndexError:
            return 0


        start_population = end_population
        for day in reversed(range(1, days+1)):
            try:
                start_population = sorted_populations[-day].population
                break
            except IndexError:
                pass

        return end_population - start_population



    @staticmethod
    def get_farm(x, y, window=10):
        villages = session.query(WorldVillage).filter(and_(
            WorldVillage.x <= x + window,
            WorldVillage.x >= x - window,
            WorldVillage.y <= y + window,
            WorldVillage.y >= y - window,
        )).all()
        farm_villages = session.query(FarmVillage).all()
        farm_coords = [(i.x, i.y) for i in farm_villages]

        for_farm = []
        for village in villages:
            if (village.x, village.y) in farm_coords:
                continue
            if village.x == x and village.y == y:
                continue
            if village.population_now.population > 100:
                continue
#            if village.population_dynamic() > 10:
#                continue
            if village.aid != 0:
                continue
            for_farm.append(village)
        return for_farm


    POPULATION_HISTORY = 10 # 10 days

    @staticmethod
    def update_world():
        URL = '%s/map.sql' % HREF
        now = datetime.now()

        req = requests.get(URL)
        if req.ok is not True:
            logging.warning('Cant download map.sql.')
            return

        last_modified = req.headers['Last-Modified']
        last_modified = eut.parsedate_to_datetime(last_modified).replace(tzinfo=None)

        world_modified = Param.get_value('world_modified')
        if world_modified is None:
            Param.set_value('world_modified', str(now))
            world_modified = Param.get_value('world_modified')
        world_modified = dateutil.parser.parse(world_modified)

        if last_modified <= world_modified:
            logging.info('World do not need updated.')
            return


        conn = sqlite3.connect(":memory:")  
        conn.execute("create table x_world (id, x, y, tid, vid, village_name, uid, player_name, aid, alliance_name, population);")
        conn.executescript(req.text)

        for world_village in session.query(WorldVillage).all():
            x = world_village.x
            y = world_village.y
            village = list(conn.execute("select * from x_world where x=%s and y=%s" % (x, y)))
            if not village:
                for p in world_village.population:
                    session.delete(p)
                session.delete(world_village)
            else:
                populations = world_village.population
                for p in populations:
                    if (now - p.actual_time).days >= 10:
                        session.delete(p)
        session.commit()

        parsed_rows = list(conn.execute("select * from x_world"))
        for data in parsed_rows:
            _, x, y, tid, vid, village_name, uid, player_name, aid, alliance_name, _population = data
            world_village = session.query(WorldVillage).filter_by(x=x, y=y).first()
            if world_village is None:
                world_village = WorldVillage(x, y, tid, vid, village_name, uid, player_name, aid, alliance_name)
                session.add(world_village)
            else:
                world_village.tid = tid
                world_village.vid = vid
                world_village.village_name = village_name
                world_village.uid = uid
                world_village.player_name = player_name
                world_village.aid = aid
                world_village.alliance_name = alliance_name
                session.add(world_village)

            population = Population()
            population.actual_time = now
            population.population = _population
            world_village.population.append(population)
        session.commit()

        conn.close()
        Param.set_value('world_modified', str(now))
        logging.info('World updated')


class Population(Base):
    __tablename__ = 'populations'

    id = Column(Integer, primary_key=True)
    village_id = Column(Integer, ForeignKey('world_villages.id'))
    population = Column(Integer)
    actual_time = Column(DateTime)


class TradeRoute(Base):
    __tablename__ = 'trade_routes'

    id = Column(Integer, primary_key=True)
    village = Column(String)
    x = Column(Integer)
    y = Column(Integer)
    wood = Column(Integer)
    clay = Column(Integer)
    rock = Column(Integer)
    corn = Column(Integer)
    add_interval = Column(Interval)
    next_date = Column(DateTime)

    def __init__(self, village, x, y, wood, clay, rock, corn, add_interval):
        now = datetime.now()
        self.village = village
        self.x = x
        self.y = y
        self.wood = wood
        self.clay = clay
        self.rock = rock
        self.corn = corn
        self.add_interval = add_interval
        self.next_date = now


    def __repr__(self):
        return '<TradeRoute (%s -> (%s, %s))>' % (self.village, self.x, self.y)

    @staticmethod
    def get_trade_route(village):
        now = datetime.now()
        return session.query(TradeRoute).filter(and_(TradeRoute.village==village, TradeRoute.next_date<=now)).first()

    def set_next(self, travel_time):
        now = datetime.now()
        trade_period = travel_time * 2 + self.add_interval
        self.next_date = now + trade_period
        session.add(self)
        session.commit()

    def wait(self):
        now = datetime.now()
        self.next_date = CHECK_TRADE_PERIOD + now
        session.add(self)
        session.commit()


class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True)
    travian_id = Column(Integer)
    from_id = Column(Integer)
    from_name = Column(String)
    header = Column(String)
    body = Column(Text)
    date_time = Column(DateTime)
    message_type = Column(String)
    message_status = Column(String)

    def __init__(self, travian_id, from_id, from_name, header, body, date_time, message_type='GENERAL'):
        self.travian_id = travian_id
        self.from_id = from_id
        self.from_name = from_name
        self.header = header
        self.body = body
        self.date_time = date_time
        self.message_type = message_type
        self.message_status = 'NEW'


    def __repr__(self):
        return '<Message %d: %s "%s">' % (self.travian_id, self.from_name, self.header)

    @staticmethod
    def create_new(travian_id, from_id, from_name, header, body, date_time):
        message = Message(travian_id, from_id, from_name, header, body, date_time)
        if header.lower().strip() == 'help':
            message.message_type = 'NEED_DEF'
        session.add(message)
        session.commit()

    def valid_def_message(self):
        village = session.query(WorldVillage).filter(WorldVillage.uid==self.from_id).first()
        if village.aid in ALLY_AIDS:
            return True
        else:
            return False

    @staticmethod
    def get_need_def_messages():
        messages = session.query(Message).filter(and_(Message.message_type=='NEED_DEF', Message.message_status=='NEW')).all()
        return messages

    def get_def_params(self):
        '''
        format:
            -12,14
            12:34:10
        '''
        lines = self.body.split('\n')
        x = None
        y = None
        atack_time_delta = None
        counter = 0
        for line in lines:
            if not line:
                continue
            counter += 1
            if counter == 1:
                try:
                    x, y = line.split(',')
                    x = _to_int(x)
                    y = _to_int(y)
                except ValueError:
                    logging.warning('Wrong def message (wrong x, y) id = %d' % self.id)
                    return None
            if counter == 2:
                try:
                    date_params = line.split(':')
                    if len(date_params) == 3:
                        h, m, s = date_params
                        h = _to_int(h)
                        m = _to_int(m)
                        s = _to_int(s)
                        today = date.today()
                        ye = today.year
                        mo = today.month
                        da = today.day
                        atack_time = datetime(ye, mo, da, h, m, s)
                    elif len(date_params) == 6:
                        ye, mo, da, h, m, s = date_params
                        ye = _to_int(ye)
                        mo = _to_int(mo)
                        da = _to_int(da)
                        h = _to_int(h)
                        m = _to_int(m)
                        s = _to_int(s)
                        atack_time = datetime(ye, mo, da, h, m, s)
                    else:
                        raise ValueError
                except ValueError:
                    logging.warning('Wrong def message (wrong date time) id = %d' % self.id)
                    return None

        if not (x and y and atack_time):
            logging.warning('Wrong def message (some params is missed) id = %d' % self.id)
            return None

        return x, y, atack_time


    def readed(self):
        self.message_status = 'READED'
        session.add(self)
        session.commit()




def create_all():
    Base.metadata.create_all(engine)



if __name__ == '__main__':
    create_all()
