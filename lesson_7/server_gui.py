from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QLabel, \
    QTableView, QDialog, QPushButton, QLineEdit, QFileDialog, QMessageBox
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt
from typing import Dict
from add_user import RegisterUser
from remove_user import DelUserDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.exitAction = QAction('Выход', self)
        self.exitAction.setShortcut('Ctrl+Q')
        self.exitAction.triggered.connect(qApp.quit)

        self.show_history_button = QAction('История клиентов', self)
        self.config_btn = QAction('Настройки сервера', self)
        self.register_btn = QAction('Регистрация пользователя', self)

        self.remove_btn = QAction('Удаление пользователя', self)

        self.statusBar()

        self.toolbar = self.addToolBar('MainBar')
        self.toolbar.addAction(self.exitAction)
        self.toolbar.addAction(self.show_history_button)
        self.toolbar.addAction(self.config_btn)
        self.toolbar.addAction(self.register_btn)
        self.toolbar.addAction(self.remove_btn)

        self.setFixedSize(800, 600)
        self.setWindowTitle('Сервер')

        self.label = QLabel('Список подключённых клиентов:', self)
        self.label.setFixedSize(400, 15)
        self.label.move(10, 35)

        self.active_clients_table = QTableView(self)
        self.active_clients_table.move(10, 55)
        self.active_clients_table.setFixedSize(780, 400)

        self.reg_window = None
        self.rem_window = None
        self.show()

    def load_clients(self, database):
        list_users = database.active_users_list()
        list_table = QStandardItemModel()
        list_table.setHorizontalHeaderLabels(
            ['Имя Клиента', 'Время подключения', 'IP Адрес', 'Порт'])

        for row in list_users:
            user, time, ip, port = row
            user = QStandardItem(user)
            user.setEditable(False)
            ip = QStandardItem(ip)
            ip.setEditable(False)
            port = QStandardItem(str(port))
            port.setEditable(False)
            time = QStandardItem(str(time.replace(microsecond=0)))
            time.setEditable(False)
            list_table.appendRow([user, ip, port, time])

        self.active_clients_table.setModel(list_table)


    def show_statistics(self, db):

        self.stat_window = QDialog()
        self.stat_window.setWindowTitle('История входа клиентов')
        self.stat_window.setFixedSize(400, 500)
        self.stat_window.setAttribute(Qt.WA_DeleteOnClose)

        self.stat_window.history_table = QTableView(self.stat_window)
        self.stat_window.history_table.move(10, 10)
        self.stat_window.history_table.setFixedSize(580, 620)

        hist_list = db.contacts_stats()

        list_table = QStandardItemModel()
        list_table.setHorizontalHeaderLabels(
            ['Имя Клиента', 'Последний раз входил'])
        for row in hist_list:
            user, last_seen = row
            user = QStandardItem(user)
            user.setEditable(False)
            last_seen = QStandardItem(str(last_seen.replace(microsecond=0)))
            last_seen.setEditable(False)
            list_table.appendRow([user, last_seen])

        self.stat_window.history_table.setModel(list_table)
        self.stat_window.show()

    def show_config_window(self, config_file: Dict):

        config = QDialog()
        self.config_window = config

        config.setFixedSize(400, 270)
        config.setWindowTitle('Настройки сервера')

        db_path_label = QLabel('Путь до файла базы данных: ', config)
        db_path_label.move(10, 10)
        db_path_label.setFixedSize(300, 30)

        config.db_path = QLineEdit(config)
        config.db_path.setFixedSize(300, 30)
        config.db_path.move(10, 40)
        config.db_path.setReadOnly(True)
        config.db_path.insert(config_file['SETTINGS']['Database_path'])

        db_path_select = QPushButton('Обзор...', config)
        db_path_select.move(315, 40)

        def open_file_dialog():
            path = QFileDialog.getOpenFileName()[0]
            path = path.replace('/', '\\')
            config.db_path.insert(path)

        db_path_select.clicked.connect(open_file_dialog)

        db_file_label = QLabel('Имя файла базы данных: ', config)
        db_file_label.move(10, 75)
        db_file_label.setFixedSize(180, 15)

        config.db_file = QLineEdit(config)
        config.db_file.move(200, 75)
        config.db_file.setFixedSize(150, 20)
        config.db_file.insert(config_file['SETTINGS']['Database_file'])

        port_label = QLabel('Номер порта:', config)
        port_label.move(10, 110)
        port_label.setFixedSize(180, 15)

        config.port = QLineEdit(config)
        config.port.move(200, 110)
        config.port.setFixedSize(150, 20)
        config.port.insert(config_file['SETTINGS']['Default_port'])

        ip_label = QLabel('IP:', config)
        ip_label.move(10, 145)
        ip_label.setFixedSize(180, 20)

        config.ip = QLineEdit(config)
        config.ip.move(200, 145)
        config.ip.setFixedSize(150, 20)
        config.ip.insert(config_file['SETTINGS']['Listen_Address'])

        save_btn = QPushButton('Сохранить', config)
        save_btn.move(190, 180)

        close_button = QPushButton('Закрыть', config)
        close_button.move(275, 180)
        close_button.clicked.connect(config.close)
        save_btn.clicked.connect(lambda: self.save_server_config(config_file))
        config.show()

    def save_server_config(self, config_file):
        message = QMessageBox()
        cw = self.config_window
        config_file['SETTINGS']['Database_path'] = cw.db_path.text()
        config_file['SETTINGS']['Database_file'] = cw.db_file.text()
        try:
            port = int(cw.port.text())
        except ValueError:
            message.warning(cw, 'Ошибка', f'{cw.port.text()} не может быть'
                                          f' портом')
        else:
            config_file['SETTINGS']['Listen_Address'] = cw.ip.text()
            if 1023 < port < 65536:
                config_file['SETTINGS']['Default_port'] = str(port)
                with open('server.ini', 'w') as f:
                    config_file.write(f)
                    message.information(cw, 'OK', 'Настройки сохранены!')
            else:
                message.warning(cw, 'Ошибка',
                                'Порт должен быть от 1024 до 65536')

    def reg_user(self, db, thread):
        self.reg_window = RegisterUser(db, thread)
        self.reg_window.show()

    def rem_user(self, db, thread):
        self.rem_window = DelUserDialog(db, thread)
        self.rem_window.show()
