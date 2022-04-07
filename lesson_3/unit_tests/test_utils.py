from unittest import TestCase
import sys
import os
import socket
import time
sys.path.append(os.path.join(os.getcwd(), '..'))
from common.utils import send_message, read_message
from common.variables import MAX_LENGTH


class TestUtils(TestCase):

    def setUp(self) -> None:
        server_ip = '127.0.0.1'
        server_port = 8888
        # очень плохая практика со случайным выбором порта, но без этого у меня
        # порт не закрывался успешно после первого теста, и второй тест не
        # проходил
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.bind((server_ip, server_port))
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.listen()
        self.client.connect((server_ip, server_port))
        self.client_rec, _ = self.s.accept()

    def tearDown(self) -> None:
        self.s.close()
        self.client.close()
        self.client_rec.close()

    def test_send_message(self):
        """
        проверка отправки сообщения
        """
        message = {
            'action': 'presence',
        }
        send_message(self.client, message)
        data = self.client_rec.recv(MAX_LENGTH)
        self.assertIsInstance(data, bytes)

    def test_read_message(self):
        """
        проверка чтения сообщения
        """
        time_sent = time.time()
        message = {
            'action': 'presence',
            'time': time_sent,
        }
        send_message(self.client, message)
        data = self.client_rec.recv(MAX_LENGTH)
        time_read = read_message(data)['time']
        self.assertEqual(time_read, time_sent)

