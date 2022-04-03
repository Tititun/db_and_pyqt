from unittest import TestCase, mock
import sys
import os
import argparse
sys.path.append(os.path.join(os.getcwd(), '..'))
from client import main as client_main, is_response_success, create_presence


class TestClient(TestCase):

    @mock.patch('builtins.print')
    @mock.patch('argparse.ArgumentParser.parse_args',
                return_value=argparse.Namespace(address='127.0.0.1', port=8888))
    def test_failed_connection(self, _, pr):
        """првоерка, что соединение не устанавливается с несуществующим
         сервером"""
        client_main()
        pr.assert_called_with('Не удалось установить соединение с'
                              ' сервером 127.0.0.1:8888')

    def test_successful_reponse(self):
        """проверка успешного ответа от сервера"""
        self.assertTrue(is_response_success(200))

    def test_unsuccessful_reponse(self):
        """проверка неуспешного от сервера"""
        self.assertFalse(is_response_success(400))

    @mock.patch('client.send_message')
    def test_presence_default_username(self, fake):
        """проверка, что имя пользователя по умолчанию - guest"""
        create_presence('any')
        user_name = fake.call_args[0][1]['user']['account_name']
        self.assertEqual(user_name, 'guest')
