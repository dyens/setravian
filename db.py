#!/usr/bin/env python

from config import SQLALCHEMY_DATABASE_URI
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, DateTime
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from sqlalchemy.sql.expression import func


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

    def __init__(self, x, y, army_string, from_village, blocked=False):
        self.x = x
        self.y = y
        self.army_string = army_string
        self.from_village = from_village
        self.blocked = blocked

    def __repr__(self):
        return '<FarmVillage (%s, %s)>' % (self.x, self.y)

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
        if not to_farm:
            return None
        else:
            return min(to_farm, key=lambda x: x.last_atacked if x.last_atacked else datetime(2000, 1, 1))


    @staticmethod
    def add_to_list(x, y,
                   army_string='Легионер:5',
                   from_village='dyens'):
        village = FarmVillage(x, y, army_string, from_village)
        session.add(village)
        session.commit()

    @staticmethod
    def del_from_list(x, y):
        village = session.query(FarmVillage).filter_by(x=x, y=y).first()
        if village:
            session.delete(job)
            session.commit()

    def army(self):
        army_dict = {}
        for army in self.army_string.split(','):
            army_name, army_number = army.split(':')
            army_dict.update({army_name: int(army_number)})
        return army_dict

    def update_last_atack(self):
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


def create_all():
    Base.metadata.create_all(engine)

if __name__ == '__main__':
    create_all()
