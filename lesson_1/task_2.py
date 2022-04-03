# 2. Написать функцию host_range_ping() (возможности которой основаны на
# функции из примера 1) для перебора ip-адресов из заданного диапазона.
# Меняться должен только последний октет каждого адреса. По результатам
# проверки должно выводиться соответствующее сообщение.

from task_1 import host_ping
from ipaddress import ip_address


def host_range_ping(address, ping_range, verbose=True):
    """
    проверяет доступность адресов в выбранном диапазоне
    """
    print(f'Проверяю {ping_range} адресов, начиная с {address}')
    try:
        address = ip_address(address)
    except ValueError:
        print(f'Введен некорректный ip адрес: {address}')
        return
    addresses = [address]
    for i in range(1, ping_range + 1):
        addresses.append(address + i)

    return host_ping(addresses, verbose=verbose)


if __name__ == '__main__':
    host_range_ping('8.8.8.0', 10)


