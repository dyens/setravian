import logging
from itertools import cycle
from datetime import timedelta
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config import ANALYSE_DELTA
from selenium.common.exceptions import NoSuchElementException
from vk_message import send_message
from functools import cmp_to_key
from db import Param
from db import Building
from db import FarmVillage
from data import mine_names
from data import hero_unit
from data import rome_units
from data import german_units
from data import gaul_units
from data import nature_units
from data import natar_units
from data import units




class Player(object):


    @staticmethod
    def _to_int(value):
        numbers = [str(i) for i in range(10)]
        if isinstance(value, int):
            return value
        elif isinstance(value, str):
            symbol_list = []
            for symbol in value:
                if symbol in numbers:
                    symbol_list.append(symbol)
            return int(''.join(symbol_list))
        else:
            raise ValueError('Wrong type of value.')




    @staticmethod
    def get_data(driver):
        storage = driver.wait.until(EC.presence_of_element_located(
            (By.ID, "stockBarWarehouse"))).text

        wood = driver.wait.until(EC.presence_of_element_located(
            (By.ID, "l1"))).text

        clay = driver.wait.until(EC.presence_of_element_located(
            (By.ID, "l2"))).text

        rock = driver.wait.until(EC.presence_of_element_located(
            (By.ID, "l3"))).text

        granary = driver.wait.until(EC.presence_of_element_located(
            (By.ID, "stockBarGranary"))).text


        corn = driver.wait.until(EC.presence_of_element_located(
            (By.ID, "l4"))).text

        gold = driver.wait.until(EC.presence_of_element_located(
            (By.CLASS_NAME, "ajaxReplaceableGoldAmount"))).text

        silver = driver.wait.until(EC.presence_of_element_located(
            (By.CLASS_NAME, "ajaxReplaceableSilverAmount"))).text

        free_crop = driver.wait.until(EC.presence_of_element_located(
            (By.ID, "stockBarFreeCrop"))).text

        table_production = driver.wait.until(EC.presence_of_element_located(
            (By.ID, "production"))).text
        wood_v = 0
        clay_v = 0
        rock_v = 0
        corn_v = 0
        for production_string in table_production.split('\n'):
            try:
                text, value = production_string.split(': ')
            except ValueError:
                continue
            if text.startswith('Древесина'):
                wood_v = value
            elif text.startswith('Глина'):
                clay_v = value
            elif text.startswith('Железо'):
                rock_v = value
            elif text.startswith('Зерно'):
                corn_v = value


        table_troops = driver.wait.until(EC.presence_of_element_located((By.ID, "troops"))).text
        troops = {}
        for troop_string in table_troops.split('\n'):
            for unit_name in units:
                if unit_name[:4] in troop_string.lower():
                    unit_number = Player._to_int(troop_string.split(' ')[0])
                    troops[unit_name] = unit_number

        try:
            quests = driver.find_element_by_xpath("//div[@id='sidebarBoxHero']/div/div/button/div/div[@class='speechBubbleContent']")
            quests = quests.text
        except NoSuchElementException:
            quests = '0'


        try:
            reports = driver.find_element_by_xpath("//li[@id='n5']/div/div[@class='speechBubbleContent']")
            reports = reports.text
        except NoSuchElementException:
            reports = '0'


        builds = []
        build_elements = driver.find_elements_by_xpath("//div[@class='boxes buildingList']/div/ul/li")
        for build_element in build_elements:
            build_name, build_period = build_element.text.split('\n')
            build_delta_string = build_period.split(' ')[0]
            build_hours, build_minutes, build_seconds = build_delta_string.split(':')
            build_hours = Player._to_int(build_hours)
            build_minutes = Player._to_int(build_minutes)
            build_seconds = Player._to_int(build_seconds)
            build_timedelta = timedelta(hours=build_hours, minutes=build_minutes, seconds=build_seconds)
            build_name, build_level = build_name.split(' Уровень ')
            builds.append({
                'name': build_name,
                'level': build_level,
                'delta': build_timedelta
            })

        try:
            loyality = driver.find_element_by_xpath("//div[@id='sidebarBoxActiveVillage']/div/div/div/span")
            loyality = Player._to_int(loyality.text)
        except NoSuchElementException:
            loyality = None

        active_village = driver.wait.until(EC.presence_of_element_located(
            (By.ID, "villageNameField"))).text

        mines_fields = driver.find_elements_by_xpath("//map[@id='rx']/area")
        mines = []
        for mines_field in mines_fields:
            href = mines_field.get_attribute('href')
            alt = mines_field.get_attribute('alt')
            try:
                mine_name, mine_level = alt.split(' Уровень ')
            except ValueError:
                continue
            mine_level = Player._to_int(mine_level)
            mines.append({
                'href': href,
                'name': mine_name,
                'level': mine_level
            })

        #TODO: культура
        #TODO: письма
        #TODO: отчеты

        moves = {'in': [], 'out': []}
        try:
            moves_table = driver.find_element_by_xpath("//table[@id='movements']/tbody")
            table_text = moves_table.text
            tokens = table_text.split('\n')

            in_army = False
            moves_type = None
            moves_number = None
            for token in tokens:
                if 'Исходящие' in token:
                    in_army = False
                    continue
                elif 'Приходящие' in token:
                    in_army = True
                else:
                    if 'Нап' in token:
                        # Нападение
                        moves_type = 'Нап'
                        moves_number = token.split(' ')[0]
                    elif 'Прик' in token:
                        # Приключение
                        moves_type = 'Прик'
                        moves_number = token.split(' ')[0]
                    elif 'Под' in token:
                        # Подкрепление
                        moves_type = 'Под'
                        moves_number = token.split(' ')[0]
                    elif 'Пос' in token:
                        # Поселенцы
                        moves_type = 'Пос'
                        moves_number = token.split(' ')[0]
                    else:
                        d_h, d_m, d_s = token.split(' ')[0].split(':')
                        d_h = Player._to_int(d_h)
                        d_m = Player._to_int(d_m)
                        d_s = Player._to_int(d_s)
                        duration = timedelta(hours=d_h, minutes=d_m, seconds=d_s)
                        if in_army is True:
                            moves['in'].append({
                                'type': moves_type,
                                'number': moves_number,
                                'duration': duration
                            })
                        else:
                            moves['out'].append({
                                'type': moves_type,
                                'number': moves_number,
                                'duration': duration
                            })

        except NoSuchElementException:
            pass

        href_villages = driver.find_elements_by_xpath("//div[@id='sidebarBoxVillagelist']/div/div/ul/li/a")
        name_villages = driver.find_elements_by_xpath("//div[@id='sidebarBoxVillagelist']/div/div/ul/li/a/div")
        href_villages = [i.get_attribute('href') for i in href_villages]
        name_villages = [i.text for i in name_villages]
        villages = zip(name_villages, href_villages)

        data = {
            'storage': Player._to_int(storage),
            'wood': Player._to_int(wood),
            'clay': Player._to_int(clay),
            'rock': Player._to_int(rock),
            'granary': Player._to_int(granary),
            'corn': Player._to_int(corn),
            'gold': Player._to_int(gold),
            'silver': Player._to_int(silver),
            'free_crop': Player._to_int(free_crop),
            'wood_v': Player._to_int(wood_v),
            'clay_v': Player._to_int(clay_v),
            'rock_v': Player._to_int(rock_v),
            'corn_v': Player._to_int(corn_v),
            'troops': troops,
            'quests': Player._to_int(quests),
            'reports': Player._to_int(reports),
            'builds': builds,
            'loyality': loyality,
            'active_village': active_village,
            'mines': mines,
            'moves': moves,
            'villages': villages
        }

        #print(data)
        return data

    PAGES = {
        'RESOURCES': 'http://ts4.travian.ru/dorf1.php',
        'CENTER': 'http://ts4.travian.ru/dorf2.php',
    }

    @staticmethod
    def _get_next_village_href(data):
        active_village = data['active_village']
        villages = cycle(data['villages'])
        save_counter = 0
        while True:
            save_counter += 1
            name_village, _ = next(villages)
            if name_village == active_village or save_counter > 20:
                break
        _, href = next(villages)
        return href

    @staticmethod
    def go_to_village(driver, name, data):
        active_village = data['active_village']
        if name == active_village:
            return
        else:
            villages = data['villages']
            for village_name, village_href in villages:
                if village_name == name:
                    driver.get(village_href)
                    break

    @staticmethod
    def go_to_next_village(driver, data):
        next_village_href = Player._get_next_village_href(data)
        driver.get(next_village_href)
        time.sleep(5)


    @staticmethod
    def analyse(driver, queue, **params):
        driver.get(Player.PAGES['RESOURCES'])
        data = Player.get_data(driver)
        nothing_to_do = True
        active_village = data['active_village']

        # постройка шахт
        need_build_mine = Param.get_value('need_build_mine', active_village)
        if need_build_mine is None:
            Param.set_value('need_build_mine', True, active_village)
            need_build_mine = Param.get_value('need_build_mine', active_village)

        build_mine_time_delta = None
        if need_build_mine is True:
            builds = data['builds']
            for build in builds:
                if build['name'] in mine_names:
                    build_mine_time_delta = build['delta']
            free_crop = data['free_crop']
            if build_mine_time_delta is None and 'BUILD_MINE' not in queue.get_all_job_names():
                wood = data['wood']
                clay = data['clay']
                rock = data['rock']
                corn = data['corn']

                quantities = {
                    'Лесопилка': wood,
                    'Глиняный карьер': clay,
                    'Железный рудник': rock,
                    'Ферма': corn,
                }

                min_production = min(wood, clay, rock, corn)
                min_mine_name = [i for i,j in quantities.items() if j == min_production][0]
                mines = data['mines']
                if free_crop >= 5:
                    min_mine = min([i for i in mines if i['name']==min_mine_name],
                                         key=lambda x: x['level'])
                else:
                    min_mine = min([i for i in mines if i['name']=='Ферма'],
                                        key=lambda x: x['level'])


                building = Building.get_by_name_and_level(min_mine['name'], min_mine['level'])

                if building and building.wood <= wood and \
                   building.clay <= clay and \
                   building.rock <= rock and \
                   building.corn <= corn and building.crop <= free_crop:
                    queue.add(('BUILD_MINE', {'mine_href': min_mine['href']}))
                    nothing_to_do = False
                elif not building:
                    queue.add(('BUILD_MINE', {'mine_href': min_mine['href']}))
                    nothing_to_do = False


        # проверка нападения
        param_disabled = Param.get_value('message_on_atack')
        if param_disabled is None:
            Param.set_value('message_on_atack', True)
            param_disabled = Param.get_value('message_on_atack')

        if param_disabled is True:
            in_moves = data['moves']['in']
            for move in in_moves:
                if move['type'] == 'Нап':
                    message = 'Нападение: количество: %s, через: %s' % (move['number'], move['duration'])
                    send_message(message)
                    Param.set_value('message_on_atack', 'False')
                    break

        # фарм
        need_farm = Param.get_value('need_farm', active_village)
        if need_farm is None:
            Param.set_value('need_farm', True, active_village)
            need_farm = Param.get_value('need_farm', active_village)
        if need_farm is True:

            friends_army_str = Param.get_value('friends_army', active_village)
            if friends_army_str is None:
                Param.set_value('friends_army', '', active_village)
                friends_army_str = Param.get_value('friends_army', active_village)
            friends_army = Player._str_army_to_dict(friends_army_str)

            def_army_str = Param.get_value('def_army', active_village)
            if def_army_str is None:
                Param.set_value('def_army', '', active_village)
                def_army_str = Param.get_value('def_army', active_village)
            def_army = Player._str_army_to_dict(def_army_str)


            troops = data['troops']

            available_troops = {}
            for name, number in troops.items():
                friens_number = friends_army.get(name, 0)
                def_number = def_army.get(name, 0)
                available_troops[name] = number - friens_number - def_number

            farm_village = FarmVillage.get_next_to_farm(active_village, available_troops)
            if farm_village is not None:
                queue.add(('ATACK', {'atack_type': 'RAID', 'farm_village': farm_village}))
                nothing_to_do = False


        work_times = [ANALYSE_DELTA, build_mine_time_delta,]
        analyse_time = min([i for i in work_times if i is not None])
        queue.add_wait(analyse_time, [('ANALYSE', params)])

        if nothing_to_do is True:
            Player.go_to_next_village(driver, data)

        return queue

    @staticmethod
    def get_center_data(driver):
        buildings = []
        areas = driver.find_elements_by_xpath("//map[@id='clickareas']/area")
        for area in areas:
            alt = area.get_attribute('alt')
            href = area.get_attribute('href')
            if alt == 'Стройплощадка':
                name = alt
                level = 0
            else:
                name = alt.split(' <span')[0]
                level = alt.split('Уровень ')[1].split('<')[0]
                level = Player._to_int(level)
            buildings.append({'name': name, 'level': level, 'href': href})
        return buildings

    @staticmethod
    def _str_army_to_dict(army_string):
        if not army_string:
            return {}
        army_dict = {}
        for army in army_string.split(','):
            army_name, army_number = army.split(':')
            army_dict.update({army_name: int(army_number)})
        return army_dict

    @staticmethod
    def _dict_army_to_str(army_dict):
        armys = ['%s:%s' % (name, number) for name, number in army_dict.items()]
        return ','.join(armys)


    @staticmethod
    def atack(driver, queue, **params):
        atack_type = params['atack_type'] 
        farm_village = params.get('farm_village', None)
        if farm_village is None:
            logging.error('Atack not supprted atack on x,y yet.')
            return queue
        x = farm_village.x
        y = farm_village.y
        army_dict = farm_village.army()
        driver.get(Player.PAGES['CENTER'])
        active_village = driver.wait.until(EC.presence_of_element_located(
            (By.ID, "villageNameField"))).text
        buildings = Player.get_center_data(driver)
        point_href = None
        for building in buildings:
            if building['name'] == 'Пункт сбора':
                point_href = building['href']
                break
        if point_href is None:
            logging.warning('Collection point not available in village')
            return queue
        atack_tab_url_param = 'tt=2'
        driver.get('%s&%s' %(point_href, atack_tab_url_param))
        time.sleep(2)
        fields = driver.find_elements_by_xpath("//table[@id='troops']/tbody/tr/td")

        friends_army_str = Param.get_value('friends_army', active_village)
        if friends_army_str is None:
            Param.set_value('friends_army', '', active_village)
            friends_army_str = Param.get_value('friends_army', active_village)
        friends_army = Player._str_army_to_dict(friends_army_str)

        def_army_str = Param.get_value('def_army', active_village)
        if def_army_str is None:
            Param.set_value('def_army', '', active_village)
            def_army_str = Param.get_value('def_army', active_village)
        def_army = Player._str_army_to_dict(def_army_str)


        army_fields = {}
        for field in fields:
            try:
                # Данные войска пока недоступны
                span_f = field.find_element_by_tag_name('span')
                continue
            except NoSuchElementException:
                pass

            try:
                a_f = field.find_element_by_tag_name('a')
                available_army = Player._to_int(a_f.text)
            except NoSuchElementException:
                continue


            input_f = field.find_element_by_tag_name('input')
            img_f = field.find_element_by_tag_name('img')
            army_name = img_f.get_attribute('alt').lower()
            army_fields.update({army_name: (input_f, available_army)})

        wrong_atack = False
        for name, number in army_dict.items():
            army_params = army_fields.get(name, None)
            if army_params is None:
                farm_village.block()
                logging.warning('Wrong army name "%s" in farm list id="%s"' % (name, farm_village.id))
                return queue
            input_f, available_army = army_params

            def_number = def_army.get(name, 0)
            if available_army < number + def_number:
                wrong_atack = True
                if name not in friends_army:
                    friends_army.update({name: number + def_number - available_army})
                else:
                    friends_army[name] = friends_army[name] + number + def_numbre - available_army
            else:
                if wrong_atack is False:
                    input_f.send_keys('%s' % number)
        friends_army_str = Player._dict_army_to_str(friends_army)
        Param.set_value('friends_army', friends_army_str, active_village)
        if wrong_atack is True:
            return queue

        OPTIONS = {
            'HELP': '2',
            'ATACK': '3',
            'RAID': '4'
        }
        type_value = OPTIONS[atack_type]
        input_type_field = driver.find_element_by_xpath('//input[@class="radio" and @value="%s"]' % type_value)
        input_type_field.click()
        x_field = driver.find_element_by_xpath('//input[@id="xCoordInput"]')
        x_field.send_keys(str(x))

        y_field = driver.find_element_by_xpath('//input[@id="yCoordInput"]')
        y_field.send_keys(str(y))

        submit_button = driver.find_element_by_xpath('//button[@id="btn_ok" and @type="submit"]')
        submit_button.click()
        farm_village.update_last_atack()
        time.sleep(3)

        submit_button = driver.find_element_by_xpath('//button[@id="btn_ok" and @type="submit"]')
        submit_button.click()
        time.sleep(3)

        return queue

    @staticmethod
    def begin(driver, queue, **params):
        queue.add(('ANALYSE', {}))
        return queue

    @staticmethod
    def build_mine(driver, queue, **params):
        href = params['mine_href']
        page = driver.get(href)

        # Попробуем сохранить стоимость
        try:
            name_level = driver.find_element_by_xpath("//h1[@class='titleInHeader']")
            name, level = name_level.text.split(' Уровень ')
            level = Player._to_int(level)

            costs = driver.find_elements_by_xpath("//div[@class='showCosts ']/span")
            if costs and len(costs) == 5:
                wood, clay, rock, corn, crop = (Player._to_int(i.text) for i in costs)
                building = Building.get_by_name_and_level(name, level)
                if not building:
                    Building.set_new_building(name, level, wood, clay, rock, corn, crop)
        except NoSuchElementException:
            pass

        try:
            build_with_arch = driver.find_element_by_xpath("//button[@value='Построить с архитектором']")
            logging.warning('Analyse mistake. Cant build.')
            return queue
        except NoSuchElementException:
            pass

        try:
            build_button = driver.find_element_by_xpath("//button[starts-with(@value, 'Улучшить до уровня')]")
            build_button.click()
            time.sleep(5)
            logging.info('build mine.')
        except NoSuchElementException:
            #TODO get valid build after from driver
            build_after = timdelta(minutes=5)
            queue.add_wait(build_after, [('BUILD_MINE', {'mine_href': href})])

        return queue
