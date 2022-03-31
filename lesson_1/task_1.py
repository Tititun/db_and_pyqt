# Написать функцию host_ping(), в которой с помощью утилиты ping будет
# проверяться доступность сетевых узлов. Аргументом функции является список,
# в котором каждый сетевой узел должен быть представлен именем хоста или
# ip-адресом. В функции необходимо перебирать ip-адреса и проверять их
# доступность с выводом соответствующего сообщения («Узел доступен»,
# «Узел недоступен»). При этом ip-адрес сетевого узла должен создаваться с
# помощью функции ip_address(). (Внимание! Аргументом сабпроцеса должен быть
# список, а не строка!!! Крайне желательно использование потоков.)

import platform
from subprocess import Popen, PIPE
from ipaddress import ip_address, IPv4Address
from threading import Thread


def ping_address(addr, results):
    """
    пингует ip адрес addr и печатает результат
    """
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    args = ['ping', param, '3', str(addr)]
    reply = Popen(args, stdout=PIPE, stderr=PIPE)
    if reply.wait() == 0:
        results['reachable'].append(addr)
    else:
        results['unreachable'].append(addr)


def host_ping(addresses, verbose=True):
    """
    многопотоково пингует полученные адреса, предварительно пытаясь их
    преобразовать в ip_address объекты
    """
    threads = []
    results = {
        'reachable': [],
        'unreachable': []
    }
    for address in addresses:
        try:
            if not isinstance(address, IPv4Address):
                address = ip_address(address)
        except ValueError:
            print(f'Адрeс {address} не мог быть преобразован в ip_address,'
                  f' воспринимается как доменное имя.')
        thread = Thread(target=ping_address, args=(str(address), results))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    if verbose:
        print('Доступные адреcа:')
        for res in results['reachable']:
            print(res)
        print('Недоступные адреcа:')
        for res in results['unreachable']:
            print(res)

    return results


if __name__ == '__main__':
    to_check = ['127.0.0.1', '15.2.2.2', '8.8.8.8', 'mail.ru', 'github.com',
                '192.168.1.2', '87.250.250.242']
    host_ping(to_check)
