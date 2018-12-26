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
applications = []
id = []
check_boxes = []


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
        self.pushButton.pressed.connect(self.update)
        self.pushButton_2.pressed.connect(self.update_on_time)
        self.checkBox.clicked.connect(self.choose_all)

    def load(self):
        global applications, id, check_boxes
        response = requests.get(url + 'my.gruz.list&sig=' + sig)
        root = cElementTree.fromstring(response.content)
        city = []
        for child in root.iter():
            if (child.tag == 'city_from') or (child.tag == 'city_to'):
                city.append(child.text)
            if child.tag == 'id':
                id.append(child.text)
        count = 0
        el = 0
        for cit in city:
            if count == 0:
                applications.append({"city_from": cit})
                count += 1
            else:
                applications[el]['city_to'] = cit
                count = 0
                el += 1
        el = 0
        for num in id:
            applications[el]['id'] = num
            el += 1
        y = 35
        for ap in applications:
            check = QCheckBox(ap['city_from'] + ' - ' + ap['city_to'], self)
            check.setObjectName(ap['id'])
            check.setFont(QtGui.QFont("Times", 12, QtGui.QFont.Bold))
            check.resize(450, 30)
            check.move(10, y)
            y += 30
            check_boxes.append(check)

    def update(self):
        id_for_update = []
        check_times = 0
        for check in check_boxes:
            if check.isChecked():
                check_times += 1
                id_for_update.append(check.objectName())
        if check_times == 0:
            msgbox(msg="Выберите хотя бы одну заявку", title="ERROR")
        else:
            for id in id_for_update:
                requests.post(url + "my.gruz.refresh&sig=" + sig + "&id=" + id)
            for check in check_boxes:
                check.setChecked(False)

    def update_on_time(self):
        id_for_update = []
        check_times = 0
        time_update = int(self.spinBox.value()) * 60
        for check in check_boxes:
            if check.isChecked():
                check_times += 1
                id_for_update.append(check.objectName())
        if check_times == 0:
            msgbox(msg="Выберите хотя бы одну заявку", title="ERROR")
        else:
            for check in check_boxes:
                check.setChecked(False)
            while True:
                for id in id_for_update:
                    requests.post(url + "my.gruz.refresh&sig=" + sig + "&id=" + id)
                time.sleep(time_update)

    def choose_all(self):
        if self.checkBox.isChecked():
            for check in check_boxes:
                check.setChecked(True)
        else:
            for check in check_boxes:
                check.setChecked(False)


if __name__ == '__main__':
    app = Qt.QApplication([])
    si = LoginForm()
    si.show()
    app.exec()
