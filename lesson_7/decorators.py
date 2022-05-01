import logging
import sys
import inspect
from log.client_log_config import client_logger
from log.server_log_config import server_logger


def log(func):
    """
    Декоратор для логирования аргументов функции и информации о том, кто
    вызвал функцию
    """
    def decorated(*args, **kwargs):
        res = func(*args, **kwargs)
        if sys.argv[0].endswith('client.py'):
            logger = logging.getLogger('client_logger')
        elif sys.argv[0].endswith('server.py'):
            logger = logging.getLogger('server_logger')
        else:
            logger = logging.getLogger('noname_logger')
        caller = inspect.stack()[1].function
        logger.debug(f'{func.__name__} вызвана из функции {caller} с аргументами'
                     f' {args}, {kwargs}. Результат: {res}')
        return res
    return decorated