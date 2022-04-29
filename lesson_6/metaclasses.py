import dis


class ServerVerifier(type):
    def __init__(cls, clsname, bases, clsdict):
        is_tcp = False  # если обнаружен AF_INET -> True
        for func in clsdict:
            try:
                ret = dis.get_instructions(clsdict[func])
            except TypeError:
                pass
            else:
                for i in ret:
                    pass
                    if i.opname == 'LOAD_METHOD' and i.argval == 'connect':
                        raise TypeError(
                            'Метод connect не может использоваться в сервере')
                    elif i.opname == 'LOAD_ATTR' and i.argval == 'AF_INET':
                        is_tcp = True

        if not is_tcp:
            raise TypeError('Не использован TCP протокол для инициализации '
                            'сокета')

        super().__init__(clsname, bases, clsdict)


class ClientVerifier(type):
    def __init__(cls, clsname, bases, clsdict):
        is_tcp = False  # если обнаружен AF_INET -> True
        for func in clsdict:
            try:
                ret = dis.get_instructions(clsdict[func])
            except TypeError:
                pass
            else:
                for i in ret:
                    if i.opname == 'LOAD_METHOD' and i.argval in ['accept',
                                                                  'listen']:
                        raise TypeError(
                            'Методы accept и listen не могут быть использованы'
                            ' на клиентской стороне')
                    elif i.opname == 'LOAD_ATTR' and i.argval == 'AF_INET':
                        is_tcp = True

        if not is_tcp:
            raise TypeError('Не использован TCP протокол для инициализации '
                            'сокета')

        super().__init__(clsname, bases, clsdict)