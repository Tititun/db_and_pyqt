import select
import socket
import re
import argparse
import time
from common.utils import send_message, read_message
from common.variables import MAX_CONNECTIONS, MAX_LENGTH
import logging
from decorators import log
from metaclasses import ServerVerifier
from descriptors import Port
from server_database import ServerStorage
from log.server_log_config import server_logger

logger = logging.getLogger('server_logger')


class Server(metaclass=ServerVerifier):
    port = Port()

    def __init__(self, listen_address, listen_port, db):
        self.addr = listen_address
        self.port = listen_port

        self.clients = []
        self.messages = []
        self.users = {}

        self.socket = self.init_socket()
        self.db = db

    def init_socket(self) -> socket.socket:
        logger.debug(f'Сервер запущен с параметрами: ip - {self.addr}'
                     f' port - {self.port}')
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.addr, self.port))
        s.settimeout(1)
        return s

    def start_loop(self):
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

            logger.info(f'Получено {len(recieved)} сообщений')
            messages = []  # собираем все полученные сообщения
            print('Пользователи:', self.users)

            if recieved:
                for rec in recieved:
                    try:
                        message = rec.recv(MAX_LENGTH)
                        if message == b'':
                            raise Exception
                        if msg := self.process_message(message, rec):
                            messages.append(msg)
                    except:
                        self.delete_user(rec)
                        if rec in self.clients:
                            self.clients.remove(rec)

            # если сообщения есть, то отправляем их слушающим пользователям:
            logger.info(f'{len(listeners)} пользователей ожидают сообщения')
            print(self.db.active_users_list())
            for listener in listeners:
                try:
                    for message in messages:
                        to = message.get('to')
                        if to and self.users.get(to) != listener:
                            continue
                        logger.info(f'Отправляется сообщение {message}')
                        send_message(listener, message)
                except:
                    # клиент отсоединился
                    self.delete_user(listener)
                    self.clients.remove(listener)

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
                response[
                    'message'] = f'Пользователь {user} присоединился к чату'
                self.users[user] = socket_
                client_ip, client_port = socket_.getpeername()
                self.db.user_login(user, client_ip, client_port)
            elif action == 'message':
                response['from'] = user
                response['message'] = message.get('message')
                response['to'] = message.get('to')
            response['status'] = 200
            response['time'] = time.time()
        return response

    def delete_user(self, user: socket):
        """
        удаляет пользователя из списка активных пользователей
        """
        for name, socket_ in self.users.items():
            self.db.user_logout(name)
            if socket_ == user:
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
    """
    Запускает работу сервера с аргументами из командной строки:
    -a --address - ip адрес сервера, дефолтное значние: 127.0.0.1
    -p --port - порт для прослушивания, дефолтное значние: 7777
    Сервер читает полученное сообщение и отправляет ответ
    """
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

    db = ServerStorage()
    server = Server(args.address, args.port, db)
    server.start_loop()


if __name__ == '__main__':
    main()
