import logging
from logging.handlers import TimedRotatingFileHandler
import sys
import os


server_logger = logging.getLogger('server_logger')
server_logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(levelname)-8s '
                              '%(module)s %(message)s')


file_name = os.path.join(os.path.dirname(__file__), 'server.log')
file_handler = TimedRotatingFileHandler(filename=file_name,
                                        when='D',
                                        interval=1,
                                        backupCount=7,
                                        encoding='utf-8')
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)

server_logger.addHandler(file_handler)
server_logger.addHandler(stream_handler)


if __name__ == '__main__':
    server_logger.debug('Какой-то баг')
    server_logger.info('Информационное сообщение')
    server_logger.warning('Предупреждение')
    server_logger.error('Ошибка')
    server_logger.critical('КРИТИЧЕСКАЯ ОШИБКА!')
