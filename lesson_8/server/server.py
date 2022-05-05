import binascii
import hmac
import os
import select
import socket
import re
import argparse
import sys
import threading
import time
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication
import sys
sys.path.append(os.path.pardir)


from common.utils import send_message, read_message
from common.variables import MAX_LENGTH
import logging
from decorators import log
from metaclasses import ServerVerifier
from descriptors import Port
from server_database import ServerStorage
import configparser
from log.server_log_config import server_logger
from server_gui import MainWindow
import sqlalchemy

logger = logging.getLogger('server_logger')
stop_server = False

class Server(threading.Thread, metaclass=ServerVerifier):
    port = Port()

    def __init__(self, listen_address, listen_port, db):
        self.addr = listen_address
        self.port = listen_port

        self.clients = []
        self.messages = []
        self.users = {}
        self.waiting = {}  # users waiting for authorization

        self.socket = self.init_socket()
        self.db = db
        super().__init__()

    def init_socket(self) -> socket.socket:
        logger.debug(f'Сервер запущен с параметрами: ip - {self.addr}'
                     f' port - {self.port}')
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.addr, self.port))
        s.settimeout(1)
        return s

    def run(self):
        global stop_server

        self.socket.listen()
        while True:
            try:
                client, addr = self.socket.accept()
                logger.info(f'Получен запрос на соединение от {addr}')
            except OSError:
                pass
            else:
                self.clients.append(client)
                logger.info(f'Установлено соединение с {client}')

            recieved, listeners, err = [], [], []
            try:
                if self.clients:
                    recieved, listeners, err = \
                        select.select(self.clients, self.clients, [], 0)
            except:
                continue

            # logger.info(f'Получено {len(recieved)} сообщений')
            messages = []  # собираем все полученные сообщения

            if recieved:
                for rec in recieved:
                    try:
                        message = rec.recv(MAX_LENGTH)
                        if message == b'':
                            continue
                        if msg := self.process_message(message, rec):
                            messages.append(msg)
                    except:
                        pass

            all_users = [u[0] for u in self.db.users_list()]

            for listener in self.users:
                messages.append({
                    'to': listener,
                    'time': time.time(),
                    'status': 200,
                    'message': all_users,
                    'from': 'user_list'
                })
            # если сообщения есть, то отправляем их слушающим пользователям:
            for listener in listeners:
                try:
                    for message in messages:
                        to = message.get('to')
                        if to and self.users.get(to) != listener:
                            continue
                        # logger.info(f'Отправляется сообщение {message}')
                        send_message(listener, message)
                except:
                    # клиент отсоединился
                    self.delete_user(listener)
                    self.clients.remove(listener)

            if stop_server:
                self.db.session.close()
                break

    def process_message(self, rec, socket_):
        """
        функция обрабатывает сообщение формирует ответ
        """
        message = read_message(rec)
        response = {}
        if message:
            action = message.get('action')
            user = message.get('user', {}).get('account_name', 'Guest')
            if action == 'presence':
                if user in self.users:
                    # пользователь уже авторизован
                    response['status'] = 400
                    response['error'] = 'Пользователь уже авторизован'
                    send_message(socket_, response)
                    self.clients.remove(socket_)
                    return
                elif user not in [u[0] for u in self.db.users_list()]:
                    response['status'] = 400
                    response['error'] = 'Такого пользователя не существует'
                    send_message(socket_, response)
                    self.clients.remove(socket_)
                    return
                else:
                    response['status'] = 511
                    random_str = binascii.hexlify(os.urandom(64))
                    response['data'] = random_str.decode('ascii')
                    hash = hmac.new(self.db.get_hash(user), random_str, 'MD5')
                    digest = hash.digest()
                    self.waiting[user] = digest
                    send_message(socket_, response)
                    return
            elif action == 'presence_2':
                client_digest = binascii.a2b_base64(message['data'])
                server_digest = self.waiting.get(user)
                if server_digest and\
                        hmac.compare_digest(client_digest, server_digest):
                    self.users[user] = socket_
                    client_ip, client_port = socket_.getpeername()
                    self.db.user_login(user, client_ip, client_port)
                    response['status'] = 200
                else:
                    response['status'] = 400
                    response['error'] = 'Неправильный пароль'
                if user in self.waiting:
                    del self.waiting[user]
            elif action == 'message':
                response['from'] = user
                response['message'] = message.get('message')
                response['to'] = message.get('to')
                response['status'] = 200
            elif action == 'get_contacts':
                response['alert'] = self.db.list_contacts(user)
                response['status'] = 202
                response['to'] = user
            elif action == 'add_contact':
                name = message.get('user_id')
                response['to'] = user
                if name in [u[0] for u in self.db.users_list()]:
                    self.db.create_contact(user, name)
                    response['status'] = 201
                else:
                    response['status'] = 400
                    response['alert'] = f'Пользователь с именем {name}' \
                                        f' не обнаружен'
            elif action == 'del_contact':
                name = message.get('user_id')
                self.db.delete_contact(user, name)
                response['status'] = 201
                response['to'] = user
            elif action == 'exit':
                self.delete_user(socket_)
                if rec in self.clients:
                    self.clients.remove(rec)
            response['time'] = time.time()
        return response

    def delete_user(self, user: socket):
        """
        удаляет пользователя из списка активных пользователей
        """
        for name, socket_ in self.users.items():
            if user == socket_:
                self.db.user_logout(name)
                del self.users[name]
                break

@log
def check_ip_port(ip, port):
    """
    функция проверяет, чтобы ip соответствовал ipv4 формату и порт
    был в  пределах допустимых значений
    """
    # logger.debug(f'функция check_ip_port вызвана с параметрами'
    #              f' ip: {ip}, port: {port}')
    ip_match = re.match(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', ip)
    port_match = port < 65535
    return ip_match and port_match


def main():
    global stop_server
    """
    Запускает работу сервера с аргументами из командной строки:
    -a --address - ip адрес сервера, дефолтное значние: 127.0.0.1
    -p --port - порт для прослушивания, дефолтное значние: 7777
    Сервер читает полученное сообщение и отправляет ответ
    """

    config = configparser.ConfigParser()
    config.read('server.ini')

    parser = argparse.ArgumentParser(description='Скрипт для получения'
                                                 'presence сообщений')
    parser.add_argument('-a', '--address',  type=str, help='ip адрес сервера',
                        default='127.0.0.1')
    parser.add_argument('-p', '--port', type=int, help='порт сервера',
                        default=7777)
    args = parser.parse_args()
    if not check_ip_port(args.address, args.port):
        logger.error(f'Сервер {args.address}:{args.port} не удалось запустить')
        return

    db_file = config['SETTINGS']['Database_file']
    db = ServerStorage(db_file)

    server_app = QApplication(sys.argv)
    server = Server(args.address, args.port, db)
    server.start()

    mw = MainWindow()
    mw.statusBar().showMessage('Server is working')

    def update_list():
        try:
            mw.load_clients(db)
        except sqlalchemy.exc.PendingRollbackError:
            db.session.rollback()
    update_list()

    timer = QTimer()
    timer.timeout.connect(update_list)
    timer.start(1000)

    mw.show_history_button.triggered.connect(lambda: mw.show_statistics(db))
    mw.config_btn.triggered.connect(lambda: mw.show_config_window(config))
    mw.register_btn.triggered.connect(lambda: mw.reg_user(db, server))
    mw.remove_btn.triggered.connect(lambda: mw.rem_user(db, server))

    server_app.exec_()
    stop_server = True


if __name__ == '__main__':
    main()
