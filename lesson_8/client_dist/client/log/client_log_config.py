import logging
import sys
import os


client_logger = logging.getLogger('client_logger')
client_logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s %(levelname)-8s '
                              '%(module)s %(message)s')

file_name = os.path.join(os.path.dirname(__file__), 'client.log')
file_handler = logging.FileHandler(file_name, mode='a', encoding='utf-8')
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)

client_logger.addHandler(file_handler)
client_logger.addHandler(stream_handler)


if __name__ == '__main__':
    client_logger.debug('Какой-то баг')
    client_logger.info('Информационное сообщение')
    client_logger.warning('Предупреждение')
    client_logger.error('Ошибка')
    client_logger.critical('КРИТИЧЕСКАЯ ОШИБКА!')
