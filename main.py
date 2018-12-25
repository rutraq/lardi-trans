from PyQt5 import Qt, QtGui, QtCore
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QCheckBox
import login_form
import main_form
import time
from xml.etree import cElementTree
import requests
from easygui import msgbox

sig = ''
url = 'http://api.lardi-trans.com/api/?method='


class LoginForm(QtWidgets.QMainWindow, login_form.Ui_Login):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.lineEdit_2.returnPressed.connect(self.login)
        self.pushButton.pressed.connect(self.login)
        self.lineEdit.returnPressed.connect(self.login)

    def login(self):
        global sig
        login = self.lineEdit.text()
        password = self.lineEdit_2.text()
        try:
            response = requests.get(url + 'auth&login=' + login + '&password=' + password)
            root = cElementTree.fromstring(response.content)
            i = 0
            for child in root.iter():
                i += 1
            if i != 2:
                for child in root.iter('sig'):
                    sig = child.text
                self.main_form = MainForm()
                self.main_form.show()
                self.show()
                self.hide()
            elif i == 2:
                msgbox(msg="Логин или пароль неверный", title='Login', ok_button='Ok')
                self.lineEdit_2.setText('')
        except requests.exceptions.ConnectionError:
            msgbox(msg='Отсутствует интернет соединение', title='Login', ok_button='Ok')


class MainForm(QtWidgets.QMainWindow, main_form.Ui_Dialog):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.load()

    def load(self):
        applications = dict()
        response = requests.get(url + 'my.gruz.list&sig=' + sig)
        root = cElementTree.fromstring(response.content)
        for child in root.iter():
            if (child.tag == 'city_from') or (child.tag == 'city_to'):
                print(child.text)


if __name__ == '__main__':
    app = Qt.QApplication([])
    si = LoginForm()
    si.show()
    app.exec()