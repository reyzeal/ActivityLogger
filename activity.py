import json
import os
import sys
from time import sleep

import pyWinhook
import requests
from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from browser import Browser
from screenshot import takeScreenshoot

move_count = 0
wheel_count = 0
left_count = 0
right_count = 0
key_count = 0
window = {}

def currentPath(x):
    return os.path.join(os.path.dirname(__file__),x)

def getKeylog():
    global window, left_count, right_count, move_count, key_count, window, wheel_count
    result = {
        'left_click': left_count,
        'right_click': right_count,
        'mouse_move': move_count,
        'key_down': key_count,
        'mouse_wheel': wheel_count
    }
    window = {}
    left_count = 0
    right_count = 0
    move_count = 0
    key_count = 0
    wheel_count = 0
    return result


def OnMouseEvent(event):
    global move_count, left_count, right_count, wheel_count, window
    if window.get(event.WindowName, None) is None:
        window[event.WindowName] = 1
    window[event.WindowName] += 1
    if event.MessageName == "mouse move":
        move_count += 1
    if event.MessageName == "mouse left down":
        left_count += 1
    if event.MessageName == "mouse right down":
        right_count += 1
    if event.MessageName == "mouse wheel":
        wheel_count += 1
    return True


def OnKeyboardEvent(event):
    global window, key_count
    if window.get(event.WindowName, None) is None:
        window[event.WindowName] = 1
    window[event.WindowName] += 1
    key_count += 1
    return True


class WorkerSignal(QObject):
    stop = pyqtSignal(bool)
    stopped = pyqtSignal()


class Worker(QRunnable):
    def __init__(self):
        QRunnable.__init__(self)
        self.browser = Browser()

        self.exiting = False
        self.data = {}
        self.signal = WorkerSignal()
        self.signal.stop.connect(self.setExit)
        self.token = ''
        self.session = requests.sessions.Session()
        self.delay = 60
        self.delaySet = 60

    def __del__(self):
        self.exiting = True

    def setToken(self, token):
        self.token = token
        # print(f"update token to {token}")

    def setExit(self, b):
        self.exiting = b

    def setDelay(self, x):
        x = int(x) * 60
        self.delay = x
        self.delaySet = x
        # print(f"update setting to {x}")

    def run(self) -> None:
        self.browser.start()
        while not self.exiting:
            while self.delay > 0 and not self.exiting:
                if self.exiting:
                    response = self.session.post("https://keylogger.reyzeal.com/sessionend", headers={
                        'Authorization': 'Bearer ' + self.token
                    })
                    # with open('log.txt', 'a') as f:
                    #     f.write("==============LOGOUT===========")
                    #     f.write(response.text)
                    #     f.write("==============ENDLOGOUT===========")
                    #     f.close()
                    break
                sleep(0.1)
                self.delay -= 0.1
            if self.exiting:
                break
            print("thread active")
            self.data.update({
                'screenshot': takeScreenshoot(),
                'url': json.dumps(self.browser.getList())
            })
            try:
                print("data received")
                # pprint(self.data)
                self.data.update(getKeylog())
                response = self.session.post("https://keylogger.reyzeal.com/upload", data=self.data, headers={
                    'Authorization': 'Bearer ' + self.token
                })
                # with open('log.txt', 'a') as f:
                #     f.write("==============Upload===========")
                #     f.write(response.text)
                #     f.write("==============ENDUpload===========")
                #     f.close()
                print("uploaded")
            except ConnectionError as e:
                print(e)
                pass
            print("emitted")
            self.delay = self.delaySet
        print("quit")
        self.browser.stop()
        self.signal.stopped.emit()


class ActivityTracker(QMainWindow):
    def __init__(self):
        super(__class__, self).__init__()
        self.settings = []
        self.action = QAction("Logout")

        self.session = requests.sessions.Session()
        uic.loadUi(currentPath("main.ui"), self)
        self.icon = QIcon(currentPath("icon.png"))
        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(1)
        self.tray = QSystemTrayIcon()
        self.tray.setIcon(self.icon)
        self.tray.setVisible(True)
        self.menu = QMenu()
        self.exitBtn = QAction("Exit")

        self.menu.addAction(self.exitBtn)
        self.tray.setContextMenu(self.menu)
        self.pushButton.clicked.connect(self.submit)
        self.show()
        self.exitBtn.triggered.connect(self.exitNow)
        self.token = ""
        self.msg = QMessageBox()
        self.msg.setWindowIcon(self.icon)
        self.msg.setIcon(QMessageBox.Information)

        self.winhook = pyWinhook.HookManager()
        self.winhook.MouseAll = OnMouseEvent
        self.winhook.KeyAll = OnKeyboardEvent
        self.logger = Worker()
        self.logger.signal.stopped.connect(self.exitNow)

    def submit(self):
        username = self.usernameInput.text()
        password = self.passwordInput.text()
        self.passwordInput.setEchoMode(QLineEdit.Password)
        self.usernameInput.setEnabled(False)
        self.passwordInput.setEnabled(False)
        self.pushButton.setEnabled(False)
        try:
            response = self.session.post("https://keylogger.reyzeal.com/auth", data={
                'username': username,
                'password': password
            })
            # with open('log.txt', 'a') as f:
            #     f.write("==============LOGIN===========")
            #     f.write(response.text)
            #     f.write("==============ENDLOGIN===========")
            #     f.close()

            if 'access_token' in response.json():
                self.token = response.json()['access_token']
                self.settings = response.json()['configs']
                self.logger.setDelay(self.settings[0]['value'])
                self.menu.addAction(self.action)
                self.menu.removeAction(self.exitBtn)
                self.action.triggered.connect(self.logout)
                self.hide()
                self.msg.setText("Login success")
                self.msg.setInformativeText("You can logout through system tray")
                self.msg.setWindowTitle("Success")
                self.msg.setIcon(QMessageBox.Information)
                self.msg.setStandardButtons(QMessageBox.Ok)
                self.msg.show()
                self.winhook.HookMouse()
                self.winhook.HookKeyboard()
                self.logger.setToken(self.token)
                self.thread_pool.start(self.logger)
            elif 'active' in response.json():
                self.usernameInput.setEnabled(True)
                self.passwordInput.setEnabled(True)
                self.pushButton.setEnabled(True)
                self.msg.setText("Login failed")
                self.msg.setInformativeText("Your account is not active")
                self.msg.setWindowTitle("Failed")
                self.msg.setIcon(QMessageBox.Warning)
                self.msg.setStandardButtons(QMessageBox.Ok)
                self.msg.show()
            else:
                self.usernameInput.setEnabled(True)
                self.passwordInput.setEnabled(True)
                self.pushButton.setEnabled(True)
                self.msg.setText("Login failed")
                self.msg.setInformativeText("Please check your credential")
                self.msg.setWindowTitle("Failed")
                self.msg.setIcon(QMessageBox.Warning)
                self.msg.setStandardButtons(QMessageBox.Ok)
                self.msg.show()
        except Exception as e:
            print(e)

    def logout(self):
        self.logger.signal.stop.emit(True)

    def exitNow(self):
        self.tray.hide()
        self.close()
        app.quit()
        app.exit()


app = QApplication(sys.argv)
a = ActivityTracker()
sys.exit(app.exec_())
