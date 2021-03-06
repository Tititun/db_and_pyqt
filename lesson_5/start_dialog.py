from PyQt5.QtWidgets import (QDialog, QPushButton, QLineEdit, QApplication,
                             QLabel , qApp)


class UserNameDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.ok_pressed = False

        self.setWindowTitle('Привет!')
        self.setFixedSize(235, 100)

        self.label = QLabel('Введите имя пользователя:', self)
        self.label.move(10, 10)
        self.label.setFixedSize(200, 15)

        self.client_name = QLineEdit(self)
        self.client_name.setFixedSize(200, 20)
        self.client_name.move(10, 30)

        self.btn_ok = QPushButton('Начать', self)
        self.btn_ok.move(20, 60)
        self.btn_ok.clicked.connect(self.click)

        self.btn_cancel = QPushButton('Выход', self)
        self.btn_cancel.move(110, 60)
        self.btn_cancel.clicked.connect(qApp.exit)

        self.show()

    def click(self):
        if self.client_name.text():
            self.ok_pressed = True
            qApp.exit()


if __name__ == '__main__':
    app = QApplication([])
    dial = UserNameDialog()
    app.exec_()
