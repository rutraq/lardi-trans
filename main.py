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
import psycopg2
import winreg

sig = ''
url = 'http://api.lardi-trans.com/api/?method='
applications = []
id = []
check_boxes = []
start = False
id_for_update = []
time_update = 0
conn = cur = None


class UpdateApplications(QThread):
    def __init__(self, k):
        super().__init__()
        self.k = k

    def run(self):
        while True:
            while True:
                for id in id_for_update:
                    requests.post(url + "my.gruz.refresh&sig=" + sig + "&id=" + id)
                    requests.post(url + "my.trans.refresh&sig=" + sig + "&id=" + id)
                time.sleep(time_update)


class TimeUpdate(QThread):
    progress = pyqtSignal(str)

    def __init__(self, k):
        super().__init__()
        self.k = k

    def run(self):
        choosen_time = str(time_update) + ":00"
        seconds = int(choosen_time[-2:])
        minutes = int(time_update) // 60 - 1
        if seconds == 0:
            seconds = 60
        while True:
            while seconds != 0:
                seconds -= 1
                if seconds < 10:
                    seconds_str = '0' + str(seconds)
                else:
                    seconds_str = str(seconds)
                self.progress.emit(str(minutes) + ":" + seconds_str)
                time.sleep(1)
            minutes -= 1
            if minutes == -1:
                minutes = int(time_update) // 60 - 1
            seconds = 60


class CheckApplications(QThread):
    progress = pyqtSignal(list)

    def __init__(self, k):
        super().__init__()
        self.k = k

    def run(self):
        global applications, id
        while True:
            response = requests.get(url + 'my.gruz.list&sig=' + sig)
            root = cElementTree.fromstring(response.content)
            city = []
            for child in root.iter('id'):
                if child.text not in applications:
            self.progress.emit(applications)


class LoginForm(QtWidgets.QMainWindow, login_form.Ui_Login):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.lineEdit_2.returnPressed.connect(self.login)
        self.pushButton.pressed.connect(self.login)
        self.lineEdit.returnPressed.connect(self.login)
        self.lineEdit_3.returnPressed.connect(self.license)
        self.pushButton_2.clicked.connect(self.license)
        self.check_license()

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

    def check_license(self):
        global conn, cur
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "SOFTWARE\Lardi", 0, winreg.KEY_ALL_ACCESS)
            key_from_winreg = winreg.QueryValue(key, "activate")
            conn = psycopg2.connect("dbname='twknsdce' user='twknsdce' host='pellefant.db.elephantsql.com' password='8J4NHVvE9kdI5vpbjTAD48i6Jc0d4QEp'")
            cur = conn.cursor()
            cur.execute("SELECT * FROM License_keys WHERE key = '" + key_from_winreg + "' ")
            row = cur.fetchone()
            if (row is not None) and (row[1] == 1):
                self.label_3.hide()
                self.label_4.hide()
                self.pushButton_2.hide()
                self.lineEdit_3.hide()
            else:
                try:
                    cur = conn.cursor()
                except psycopg2.OperationalError:
                    msgbox(msg="Отсутствует интернет соединение", title="Login", ok_button="Exit")
                    exit(0)
        except FileNotFoundError:
            try:
                conn = psycopg2.connect(
                    "dbname='twknsdce' user='twknsdce' host='pellefant.db.elephantsql.com' password='8J4NHVvE9kdI5vpbjTAD48i6Jc0d4QEp'")
                cur = conn.cursor()
            except psycopg2.OperationalError:
                msgbox(msg="Отсутствует интернет соединение", title="Login", ok_button="Exit")
                exit(0)

    def license(self):
        global conn, cur
        license_key = self.lineEdit_3.text()
        cur.execute("SELECT * FROM License_keys WHERE key = '" + license_key + "' ")
        row = cur.fetchone()
        if (row is not None) and (row[1] == 0):
            cur.execute("UPDATE License_keys SET use_of_key=1 WHERE key = '" + license_key + "'")
            conn.commit()
            self.label_3.hide()
            self.label_4.hide()
            self.pushButton_2.hide()
            self.lineEdit_3.hide()
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "SOFTWARE", 0, winreg.KEY_ALL_ACCESS)
            winreg.CreateKey(key, "Lardi")
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "SOFTWARE\Lardi", 0, winreg.KEY_ALL_ACCESS)
            winreg.SetValue(key, "activate", 1, license_key)
        else:
            msgbox(msg="Лицензионный ключ неверный", title="License", ok_button="OK")


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
        # self.thread3 = CheckApplications(1)
        # self.thread3.progress.connect(self.load_applications)
        # self.thread3.start()

    def load_applications(self, value):
        global check_boxes
        y = 35
        print(value)
        for ap in value:
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
                requests.post(url + "my.trans.refresh&sig=" + sig + "&id=" + id)
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
                self.thread1.terminate()
                self.thread2.terminate()
                self.label.hide()
                self.label_2.hide()
                start = False
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
            self.thread2.progress.connect(self.time_on_form)
            self.thread2.start()

    def choose_all(self):
        if self.checkBox.isChecked():
            for check in check_boxes:
                check.setChecked(True)
        else:
            for check in check_boxes:
                check.setChecked(False)

    def time_on_form(self, value):
        self.label_2.setText(value)


if __name__ == '__main__':
    app = Qt.QApplication([])
    si = LoginForm()
    si.show()
    app.exec()
