import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import ElementNotVisibleException
from config import GECKO_PATH
from config import SOCKET_PORT
import socket
import logging
logging.basicConfig(level=logging.INFO)
from importlib import reload
import os



def init_driver():
    import os
    os.environ["PATH"] += os.pathsep + GECKO_PATH
    driver = webdriver.Firefox()
    driver.wait = WebDriverWait(driver, 5)
    return driver

def lookup(driver, query):
    driver.get("http://www.google.com")
    try:
        box = driver.wait.until(EC.presence_of_element_located(
            (By.NAME, "q")))
        button = driver.wait.until(EC.element_to_be_clickable(
            (By.NAME, "btnK")))
        box.send_keys(query)
        try:
            button.click()
        except ElementNotVisibleException:
            button = driver.wait.until(EC.visibility_of_element_located(
                (By.NAME, "btnG")))
            button.click()
    except TimeoutException:
        print("Box or Button not found in google.com")

class Server(object):

    conn = None
    addr = None

    def start(self):
        self.sock = socket.socket()
        self.sock.bind(('', SOCKET_PORT))
        self.sock.listen(1)
        logging.info('server starts.')
        self.sock.setblocking(0)

    def _get_connection(self):
        try:
            self.conn, self.addr = self.sock.accept()
            logging.info('server connected.')
        except socket.error:
            pass


    def __del__(self):
        self.stop()

    def stop(self):
        if self.conn:
            self.conn.close()
        self.sock.close()
        logging.info('server stops.')

    def _check_stop_con(self, data):
        if data == 'STOP_CONNECTION':
            self.conn, self.addr = None, None
            logging.info('connection closed.')
            return True
        return False

    def get(self):
        if not self.conn:
            self._get_connection()
        if not self.conn:
            return None
        else:
            data = self.conn.recv(1024)
            data = data.decode('utf-8')
            if self._check_stop_con(data):
                return None
            return data

    def send(self, msg):
        self.conn.send(msg.encode('utf-8'))

#Need reload
import controller as C
import loader
import timer
import stop
import player
import db
import data
import utils

def get_jobs():
    return {
        'LOAD_QUEUE': loader.Loader.load_queue,
        'WAIT': timer.Timer.wait,
        'WAIT_FOR': timer.Timer.wait_for,
        'STOP': stop.Stop.stop,
        'LOGIN': loader.Loader.login,
        'BEGIN': player.Player.begin,
        'ANALYSE': player.Player.analyse,
        'BUILD_MINE': player.Player.build_mine,
        'ATACK': player.Player.atack,
        'TRADE': player.Player.trade,
        'READ_MESSAGES': player.Player.read_messages,
    }



driver = init_driver()
controller = C.Controller(driver, get_jobs())


def loop():
    server = Server()
    server.start()
    while True:

        #Need reload
        global controller
        global C
        global loader
        global timer
        global stop
        global player
        global db
        global data
        global utils

        controller.next()
        in_data = server.get()
        # При соединении тут происходит wait
        if in_data:
            try:
                msg =exec(in_data)
                server.send(str(msg))
            except Exception as e:
                server.send(str(e))






if __name__ == "__main__":
    loop()
#    driver = init_driver()
#    lookup(driver, "Selenium")
#    time.sleep(5)
#    driver.quit()
