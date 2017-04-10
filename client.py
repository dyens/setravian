import socket
import time
from config import SOCKET_PORT
import readline
import atexit
import os

readline.parse_and_bind('tab: complete')
readline.parse_and_bind('set editing-mode vi')



basedir = os.path.abspath(os.path.dirname(__file__))
histfile = os.path.join(basedir, ".setravian_history")
try:
    readline.read_history_file(histfile)
    # default history len is -1 (infinite), which may grow unruly
    readline.set_history_length(1000)
except FileNotFoundError:
    pass

atexit.register(readline.write_history_file, histfile)

jobs = '''
jobs ={
    'LOAD_QUEUE': loader.Loader.load_queue,
    'WAIT': timer.Timer.wait,
    'WAIT_FOR': timer.Timer.wait_for,
    'STOP': stop.Stop.stop,
    'LOGIN': loader.Loader.login,
    'BEGIN': player.Player.begin,
    'ANALYSE': player.Player.analyse,
    'BUILD_MINE': player.Player.build_mine,
    'ATACK': player.Player.atack,
}
'''
reload_command = '''
global controller
global C
global loader
global timer
global stop
global player
global db
global data

reload(loader)
reload(timer)
reload(C)
reload(stop)
reload(player)
reload(db)
reload(data)
%s
controller=C.Controller(driver, jobs)
''' % jobs

save_reload_command = '''
global controller
global C
global loader
global timer
global stop
global player
global db
global data

queue_back = [i for i in controller.queue._queue]

reload(loader)
reload(timer)
reload(C)
reload(stop)
reload(player)
reload(db)
reload(data)
%s
controller=C.Controller(driver, jobs)
controller.queue._queue = queue_back
''' % jobs 



add_farm = '''
from db import FarmVillage
FarmVillage.add_to_list({params})
'''


class Client(object):

    commands = {
        'reload': reload_command,
        'save_reload': save_reload_command,
    }

    commands_with_args = {
        'add_farm': add_farm,
    }

    def __init__(self):
        self.sock = socket.socket()
        self.sock.connect(('localhost', SOCKET_PORT))
        self.sock.setblocking(0)

    def _send(self, msg):
        self.sock.send(msg.encode('utf-8'))

    def _get(self):
        time.sleep(1)
        try:
            data = self.sock.recv(1024)
            return data.decode('utf-8')
        except socket.error:
            return None

    def _command(self, command):
        if command in self.commands:
            command = self.commands[command]
        if command.split('(')[0] in self.commands_with_args:
            command_name, params = command.split('(')
            params = params[:-1]
            command = self.commands_with_args[command_name].format(params=params)
        return command


    def start(self):
        while True:
            send_data = input('>> ')
            if send_data in ('q', 'quit'):
                self.stop()
                break
            if send_data:
                if send_data in ('h', 'help'):
                    for command in self.commands:
                        print(command)
                    for command in self.commands_with_args:
                        print(command)
                    continue
                send_data = self._command(send_data)
                self._send(send_data)
                recv_data = self._get()
                if recv_data:
                    print('<<', recv_data)

    def __del__(self):
        if not self.sock._closed:
            self.stop()

    def stop(self):
        self._send('STOP_CONNECTION')
        self.sock.close()

c = Client()
c.start()
