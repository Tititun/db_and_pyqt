from unittest import TestCase, mock
import sys
import os
import argparse
sys.path.append(os.path.join(os.getcwd(), '..'))
from server import check_ip_port, compile_response


class TestServer(TestCase):

    def test_failed_server(self):
        """проверка, что если порт указан неверно, то сервер не запустится"""
        self.assertFalse(check_ip_port('127.0.0.1', 100000))

    def test_response_success(self):
        """проверка первого аргумента функции compile_response"""
        self.assertEqual(compile_response(200, '', '')['response'], 200)

    def test_response_type(self):
        """функция compile_response должна возаращать словарь"""
        self.assertIsInstance(compile_response(200, '', ''), dict)

    def test_response_error(self):
        """проверка третьего аргумента функции compile_response"""
        self.assertIn('error', compile_response(404, '', 'error'))
