from PyQt5.QtWidgets import (QMainWindow, qApp, QMessageBox,
                             QDialog, QLabel, QComboBox, QPushButton)
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QBrush, QColor
from PyQt5.QtCore import pyqtSlot, QEvent, Qt
import logging
import datetime
from main_window_conv import Ui_MainClientWindow
import os
import sys
sys.path.append(os.path.pardir)
from common.utils import send_message
import time


logger = logging.getLogger('client_dist')


class ClientMainWindow(QMainWindow):
    def __init__(self, database, transport):
        super().__init__()

        self.show()
        self.database = database
        self.transport = transport

        self.ui = Ui_MainClientWindow()
        self.ui.setupUi(self)

        self.ui.menu_exit.triggered.connect(qApp.exit)

        # Кнопка отправить сообщение
        self.ui.btn_send.clicked.connect(self.send_message)

        # "добавить контакт"
        self.ui.btn_add_contact.clicked.connect(self.add_contact_window)
        self.ui.menu_add_contact.triggered.connect(self.add_contact_window)
        # Удалить контакт
        self.ui.btn_remove_contact.clicked.connect(self.delete_contact)
        self.ui.menu_del_contact.triggered.connect(self.delete_contact)

        self.contacts_model = None
        self.history_model = None
        self.messages = QMessageBox()
        self.current_chat = None  # Текущий контакт с которым идёт обмен сообщениями
        self.selected_user = None   # Текущий выделенный контакт
        self.ui.list_messages.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.ui.list_messages.setWordWrap(True)

        # Double click по списку контактов отправляется в обработчик
        self.ui.list_contacts.clicked.connect(self.select_user)
        self.ui.list_contacts.doubleClicked.connect(self.select_active_user)

        self.clients_list_update()
        self.add_contact_window = None
        self.show()

    def clients_list_update(self):
        contacts_list = self.database.list_contacts()
        self.contacts_model = QStandardItemModel()
        for i in sorted(contacts_list):
            item = QStandardItem(i)
            item.setEditable(False)
            self.contacts_model.appendRow(item)
        self.ui.list_contacts.setModel(self.contacts_model)
        return contacts_list

    def select_active_user(self):
        self.current_chat = self.ui.list_contacts.currentIndex().data()
        self.set_active_user()

    def select_user(self):
        self.selected_user = self.ui.list_contacts.currentIndex().data()

    def set_active_user(self):
        self.ui.label_new_message.setText(f'Введите сообщение для {self.current_chat}:')
        self.ui.btn_clear.setDisabled(False)
        self.ui.btn_send.setDisabled(False)
        self.ui.text_message.setDisabled(False)
        self.history_list_update()

    def history_list_update(self):
        # Получаем историю сортированную по дате
        list_messages = sorted(self.database.get_history(self.current_chat),
                               key=lambda item: item[3])

        if not self.history_model:
            self.history_model = QStandardItemModel()
            self.ui.list_messages.setModel(self.history_model)
        self.history_model.clear()
        # Берём не более 20 последних записей.
        length = len(list_messages)
        start_index = 0
        if length > 20:
            start_index = length - 20

        for i in range(start_index, length):
            person_1, person_2, text, timestamp = list_messages[i]

            timestamp = timestamp.replace(microsecond=0)
            speaker = person_1 if person_1 != self.database.user\
                else person_2
            if person_1 == speaker:
                mess = QStandardItem(f'{speaker} [{timestamp}]:\n {text}')
                mess.setEditable(False)
                mess.setBackground(QBrush(QColor(255, 213, 213)))
                mess.setTextAlignment(Qt.AlignLeft)
                self.history_model.appendRow(mess)
            else:
                mess = QStandardItem(f'Я [{timestamp}]:\n {text}')
                mess.setEditable(False)
                mess.setTextAlignment(Qt.AlignRight)
                mess.setBackground(QBrush(QColor(204, 255, 204)))
                self.history_model.appendRow(mess)
        self.ui.list_messages.scrollToBottom()

    def add_contact_window(self):
        add_dialog = QDialog()

        add_dialog.setFixedSize(350, 120)
        add_dialog.setWindowTitle('Выберите контакт для добавления:')
        add_dialog.setAttribute(Qt.WA_DeleteOnClose)
        add_dialog.setModal(True)

        selector_label = QLabel('Выберите контакт для добавления:', add_dialog)
        selector_label.setFixedSize(200, 20)
        selector_label.move(10, 0)

        add_dialog.selector = QComboBox(add_dialog)
        add_dialog.selector.setFixedSize(200, 20)
        add_dialog.selector.move(10, 30)

        add_dialog.btn_refresh = QPushButton('Обновить список', add_dialog)
        add_dialog.btn_refresh.setFixedSize(125, 30)
        add_dialog.btn_refresh.move(60, 60)

        add_dialog.btn_ok = QPushButton('Добавить', add_dialog)
        add_dialog.btn_ok.setFixedSize(100, 30)
        add_dialog.btn_ok.move(230, 20)

        btn_cancel = QPushButton('Отмена', add_dialog)
        btn_cancel.setFixedSize(100, 30)
        btn_cancel.move(230, 60)
        btn_cancel.clicked.connect(add_dialog.close)

        self.add_contact_window = add_dialog
        self.possible_contacts_update()

        add_dialog.btn_refresh.clicked.connect(
            lambda: self.possible_contacts_update())
        add_dialog.btn_ok.clicked.connect(
            lambda: self.add_contact_action(add_dialog.selector.currentText()))

        add_dialog.show()

    def possible_contacts_update(self):
        self.add_contact_window.selector.clear()
        contacts_list = set(self.database.list_contacts())
        users_list = [u for u in self.transport.all_users if u not in
                      contacts_list]
        if self.database.user in users_list:
            users_list.remove(self.database.user)
        self.add_contact_window.selector.addItems(users_list)

    def add_contact_action(self, item):
        self.send_action(cmd='add_contact', user=item)
        self.database.add_contact(item)
        self.possible_contacts_update()
        self.clients_list_update()


    def delete_contact(self):
        print(self.selected_user, self.current_chat)
        to_delete = self.selected_user
        self.send_action(cmd='del_contact', user=to_delete)

        self.database.delete_contact(to_delete)
        self.clients_list_update()
        self.selected_user = None

        if to_delete == self.current_chat:
            self.current_chat = None
            self.ui.btn_clear.setDisabled(True)
            self.ui.btn_send.setDisabled(True)
            self.ui.text_message.setDisabled(True)
            self.history_list_update()

    def send_message(self):
        self.send_action(cmd='message', user=None)

    def send_action(self, cmd=None, user=None):
        action = {}
        timestamp = time.time()
        if cmd in ['add_contact', 'del_contact'] and user:
            action = {
                'action': cmd,
                'user_id': user
            }

        elif cmd in ['list', 'exit']:
            action = {'action': cmd}

        elif cmd == 'message':
            message_text = self.ui.text_message.toPlainText()
            self.ui.text_message.clear()
            if not message_text:
                return
            action = {
                'action': cmd,
                'message': message_text,
                'to': self.current_chat,
            }
            self.database.write_message(self.database.user, self.current_chat,
                                        message_text,
                                        datetime.datetime.fromtimestamp(
                                            timestamp))
        try:
            message = {
                **action,
                'time': timestamp,
                'user': {
                    'account_name': self.database.user,
                    'status': 'online'
                }
            }
            send_message(self.transport.sock, message)

        except Exception:
            import traceback
            print(traceback.format_exc())
        self.history_list_update()

    @pyqtSlot(str)
    def message(self, sender):
        if sender == self.current_chat:
            self.history_list_update()
        else:
            if sender in self.clients_list_update():
                if self.messages.question(self, 'Новое сообщение',
                                          f'Получено новое сообщение от {sender}, '
                                          f'открыть чат с ним?', QMessageBox.Yes,
                                          QMessageBox.No) == QMessageBox.Yes:
                    self.current_chat = sender
                    self.set_active_user()
            else:
                if self.messages.question(self, 'Новое сообщение',
                              f'Получено новое сообщение от {sender}.\n '
                              f'Данного пользователя нет в вашем контакт-листе.\n'
                              f' Добавить в контакты и открыть чат с ним?',
                              QMessageBox.Yes, QMessageBox.No) == QMessageBox.Yes:
                    self.send_action(cmd='add_contact', user=sender)
                    self.database.add_contact(sender)
                    self.clients_list_update()
                    self.current_chat = sender
                    self.set_active_user()

    @pyqtSlot()
    def connection_lost(self):
        self.messages.warning(self, 'Сбой соединения',
                              'Потеряно соединение с сервером. ')
        self.close()

    def make_connection(self):
        self.transport.new_message.connect(self.message)
        self.transport.connection_lost.connect(self.connection_lost)
