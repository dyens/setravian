import logging
from datetime import timedelta
from config import LOGIN
from config import PASSWORD
from config import HREF
import pickle
import os
import time

class Loader(object):

    MAIN_ADDRES = '%s/dorf1.php' % HREF
    ERROR_ADDRES = '%s/dorf1.php/404' % HREF

    @staticmethod
    def _load_cookies(driver):
        driver.get(Loader.ERROR_ADDRES)
        cookies_exist = os.path.exists('cookies.pkl')
        if cookies_exist:
            cookies = pickle.load(open("cookies.pkl", "rb"))
            driver.delete_all_cookies()
            for cookie in cookies:
                driver.add_cookie(cookie)

    @staticmethod
    def _update_cookies(driver):
        cookies_exist = os.path.exists('cookies.pkl')
        if cookies_exist:
            os.remove('cookies.pkl')
        pickle.dump(driver.get_cookies() , open("cookies.pkl","wb"))


    @staticmethod
    def login(driver, queue, **params):
        driver.get(Loader.MAIN_ADDRES)
        form = driver.find_elements_by_xpath("//form[@name='login' and @method='POST']")
        if not form:
            #logging not needeed
            return queue
        if len(form) != 1:
            logging.error('Cant find login form.')
            queue.stop()

        login = driver.find_element_by_name('name')
        password = driver.find_element_by_name('password')
        button = driver.find_element_by_xpath("//button[@id='s1' and @type='submit']")
        login.send_keys(LOGIN)
        password.send_keys(PASSWORD)
        button.click()
        time.sleep(5)
        Loader._update_cookies(driver)
        return queue


    @staticmethod
    def load_queue(driver, queue, **params):
        Loader._load_cookies(driver)
        driver.get(Loader.MAIN_ADDRES)
        form = driver.find_elements_by_xpath("//form[@name='login' and @method='POST']")
        if len(form) == 1:
            queue.add(('LOGIN', {}))
            queue.add(('BEGIN', {}))
        elif len(form) == 0:
            queue.add(('BEGIN', {}))
        else:
            logging.error('Wrong behaviour in load queue.')
            delta = timedelta(minutes=1)
            jobs = [('LOAD_QUEUE', {})]
            queue.add_wait(delta, jobs)
        return queue

