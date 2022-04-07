import logging
logger = logging.getLogger('server')


# Дескриптор порта:
class Port:
    def __set__(self, instance, value):
        if not 0 <= value <= 65535:
            raise ValueError(
                f'Порт сервера должен быть в диапазоне от 0 до 65535,'
                f' получено: {value}.')
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name
