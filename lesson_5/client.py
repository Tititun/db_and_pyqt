import datetime
import socket
import sys
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QApplication
from common.variables import MAX_LENGTH
from common.utils import send_message, read_message
import time
import argparse
import logging
import threading
from start_dialog import UserNameDialog
from client_database import ClientStorage
from log.client_log_config import client_logger
from client_gui import ClientMainWindow

logger = logging.getLogger('client_logger')
stop_client = False


class Client(threading.Thread, QObject):
    new_message = pyqtSignal(str)
    connection_lost = pyqtSignal()

    def __init__(self, account_name, db):
        threading.Thread.__init__(self)
        QObject.__init__(self)
        self.db = db
        self.account_name = account_name
        self.status = 'online'
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen_thread = None
        self.send_thread = None
        self.all_users = []


    def create_presence(self):
        """функция для отправки presence сообщения на сервер"""
        msg = {
            'action': 'presence',
            'time': time.time(),
            'user': {
                'account_name': self.account_name,
                'status': self.status
            }
        }
        send_message(self.sock, msg)

    def connect(self, addr, port):
        try:
            self.sock.connect((addr, port))
            return True
        except ConnectionError:
            logger.error(f'Не удалось установить соединение с сервером '
                         f'{addr}:{port}')

    @staticmethod
    def is_response_success(status_code):
        """
        функция для проверки статуса ответа от сервера
        """
        if 300 >= status_code >= 100:
            return True
        else:
            return False

    def parse_message(self, msg):
        if msg.get('status') == 202:
            content = msg.get('alert')
            if isinstance(content, list):
                for name in content:
                    self.db.add_contact(name)
            print(msg['alert'])

        elif msg.get('status') == 201:
            print('Запрос выполнен')

        elif msg.get('status') == 400:
            print(f'Ошибка запроса: {msg.get("alert", "что-то не то")}')
        from_ = msg.get('from', 'Чат-бот')
        message = msg.get('message')
        if from_ not in ['user_list', 'Чат-бот']:
            return msg
        elif from_ == 'user_list':
            self.all_users = message if message else []

    def run(self):
        global stop_client
        self.start_listening()
        while True:
            time.sleep(0.5)
            if stop_client:
                send_message(self.sock,
                             {
                                 'action': 'exit',
                                 'time': time.time()}
                             )
                break
            if self.listen_thread.is_alive():
                continue
            break

    def start_listening(self):

        def receive_message():
            """
            функция, которая печатает полученное сообщение
            """
            while True:
                data = self.sock.recv(MAX_LENGTH)
                if msg := read_message(data):
                    chat_message = self.parse_message(msg)
                    if chat_message:
                        self.db.write_message(
                            chat_message['from'],
                            chat_message['to'],
                            chat_message['message'],
                            datetime.datetime.fromtimestamp(chat_message['time'])
                        )
                        print(f'Сообщение в чате: {chat_message}')
                        self.new_message.emit(chat_message['from'])

        self.listen_thread = threading.Thread(target=receive_message)
        self.listen_thread.daemon = True
        self.listen_thread.start()

def main():
    """
    Отправляет presence сообщение на сервер
    Работает позиционными аргументами из командной строки:
    -address - ip адрес сервера, обязательный аргумент
    -port - порт сервера, стандартное значние: 7777
    -u --user опциональный аргумент, имя пользователя,
                                     стандартное значние: Guest

    """
    global stop_client
    parser = argparse.ArgumentParser(description='Скрипт для отправки presence'
                                                 ' сообщения и чтения ответа')
    parser.add_argument('address', type=str, help='ip адрес сервера', nargs='?',
                        default='127.0.0.1')
    parser.add_argument('port', type=int, help='порт сервера', nargs='?',
                        default=7777)
    args = parser.parse_args()

    logger.debug('Скрипт запущен с запросом на соединение с сервером '
                 f'{args.address}:{args.port}')

    client_app = QApplication(sys.argv)
    start_dialog = UserNameDialog()
    client_app.exec_()

    if start_dialog.ok_pressed:
        client_name = start_dialog.client_name.text()
        print(client_name)
        del start_dialog
    else:
        exit(0)


    db = ClientStorage(user=client_name)
    client = Client(client_name, db)
    connection_success = client.connect(args.address, args.port)
    if connection_success:
        try:
            client.create_presence()
            client.start()
            main_window = ClientMainWindow(db, client)
            main_window.make_connection()
            main_window.setWindowTitle(
                f'Чат Программа alpha release - {client_name}')
            client_app.exec_()
            stop_client = True
        except:
            send_message(client.sock,
                         {
                            'action': 'exit',
                            'time': time.time()}
                         )


if __name__ == '__main__':
    main()
