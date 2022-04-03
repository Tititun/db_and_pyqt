import socket
from common.variables import MAX_LENGTH
from common.utils import send_message, read_message
import time
import argparse
import logging
from decorators import log
import threading
from log.client_log_config import client_logger

logger = logging.getLogger('client_logger')


class Client:
    def __init__(self, account_name):
        self.account_name = account_name
        self.status = 'online'
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen_thread = None
        self.send_thread = None

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

    @staticmethod
    def parse_message(msg):
        from_ = msg.get('from', 'Чат-бот')
        message = msg.get('message')
        return f'{from_}: {message}'

    def run(self):
        self.start_listening()
        self.start_user_thread()
        while True:
            time.sleep(0.5)
            if self.listen_thread.is_alive() and self.send_thread.is_alive():
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
                    print(f'Сообщение в чате: {chat_message}')

        self.listen_thread = threading.Thread(target=receive_message)
        self.listen_thread.daemon = True
        self.listen_thread.start()

    def start_user_thread(self):
        def user_thread():
            """
            функция запрашивает у пользователя имя получателя и сообщение,
            затем отправляет сообщение
            """
            print(f'Добро пожаловать в чат. Для выхода нажмите Ctrl + C')
            while True:
                to = input('Введите получателя:\n')
                message_text = input('Введите текст сообщения:\n')
                message = {
                    'action': 'message',
                    'time': time.time(),
                    'message': message_text,
                    'to': to,
                    'user': {
                        'account_name': self.account_name,
                        'status': 'online'
                    }
                }
                send_message(self.sock, message)

        self.send_thread = threading.Thread(target=user_thread)
        self.send_thread.daemon = True
        self.send_thread.start()


def main():
    """
    Отправляет presence сообщение на сервер
    Работает позиционными аргументами из командной строки:
    -address - ip адрес сервера, обязательный аргумент
    -port - порт сервера, стандартное значние: 8888
    -u --user опциональный аргумент, имя пользователя,
                                     стандартное значние: Guest

    """
    parser = argparse.ArgumentParser(description='Скрипт для отправки presence'
                                                 ' сообщения и чтения ответа')
    parser.add_argument('address', type=str, help='ip адрес сервера')
    parser.add_argument('port', type=int, help='порт сервера', nargs='?',
                        default=8888)
    parser.add_argument('-u', '--user', type=str, help='имя пользователя',
                        nargs='?', default='Guest')
    args = parser.parse_args()

    logger.debug('Скрипт запущен с запросом на соединение с сервером '
                 f'{args.address}:{args.port} от пользователя {args.user}')

    client = Client(args.user)
    connection_success = client.connect(args.address, args.port)
    if connection_success:
        client.create_presence()
        client.run()


if __name__ == '__main__':
    main()
