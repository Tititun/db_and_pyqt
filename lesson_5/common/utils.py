import json
import socket
from .variables import ENCODING


def send_message(send_to: socket.socket, msg: dict):
    """функция для кодировки и отправки сообщения"""
    msg = json.dumps(msg, default=str).encode(ENCODING)
    send_to.send(msg)


def read_message(msg: bytes):
    """функция для принятия и декодирования сообщения"""
    try:
        return json.loads(msg.decode('utf-8'))
    except ValueError:
        pass