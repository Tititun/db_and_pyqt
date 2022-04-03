# 3. Написать функцию host_range_ping_tab(), возможности которой основаны
# на функции из примера 2. Но в данном случае результат должен быть итоговым
# по всем ip-адресам, представленным в табличном формате (использовать модуль
# tabulate). Таблица должна состоять из двух колонок

from tabulate import tabulate
from task_2 import host_range_ping


def host_range_ping_tab(addresses, ping_range):
    """
    пингует адреса в введенном диапазоне и выводит результат в виде таблицы
    """
    results = host_range_ping(addresses, ping_range, verbose=False)
    print(tabulate(results, headers=('Reachable', 'Unreachable')))


if __name__ == '__main__':
    host_range_ping_tab('8.8.8.0', 10)