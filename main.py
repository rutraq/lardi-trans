from PyQt5 import Qt, QtGui, QtCore
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QCheckBox
import login_form
import main_form
import time
from xml.etree import cElementTree
import requests
from easygui import msgbox
from PyQt5.QtCore import QThread, pyqtSignal

sig = ''
url = 'http://api.lardi-trans.com/api/?method='
applications = []
id = []
check_boxes = []
start = False
id_for_update = []
time_update = 0


class UpdateApplications(QThread):
    def __init__(self, k):
        super().__init__()
        self.k = k

    def run(self):
        while True:
            while True:
                for id in id_for_update:
                    requests.post(url + "my.gruz.refresh&sig=" + sig + "&id=" + id)
                time.sleep(time_update)


class TimeUpdate(QThread):
    progress = pyqtSignal(str)

    def __init__(self, k):
        super().__init__()
        self.k = k

    def run(self):
        time = str(time_update) + ":00"
        # while time != "0:00":
        #     minutes = time[-2:-1]
        #     print(minutes)
        minutes = int(time[-2:])
        print(len(minutes))


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
        self.label.hide()
        self.label_2.hide()

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
        global id_for_update
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
            self.checkBox.setChecked(False)

    def update_on_time(self):
        global id_for_update, start, time_update
        check_times = 0
        time_update = int(self.spinBox.value()) * 60
        for check in check_boxes:
            if check.isChecked():
                check_times += 1
                id_for_update.append(check.objectName())
        if check_times == 0:
            if not start:
                msgbox(msg="Выберите хотя бы одну заявку", title="ERROR")
            else:
                self.pushButton_2.setText("Обновлять по времени")
                start = False
                self.thread1.terminate()
        else:
            for check in check_boxes:
                check.setChecked(False)
            self.pushButton_2.setText("Остановить")
            start = True
            self.thread1 = UpdateApplications(1)
            self.thread1.start()
            self.checkBox.setChecked(False)
            self.label.show()
            self.label_2.show()
            self.thread2 = TimeUpdate(1)
            self.thread2.start()

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
