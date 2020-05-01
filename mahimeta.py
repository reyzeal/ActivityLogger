import json
import os
import sys
from time import sleep

import pyWinhook
import requests
from PyQt5 import uic
from PyQt5.QtCore import QThreadPool, Qt, pyqtSlot, QRunnable, pyqtSignal, QObject
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QAction, QMenu, QMessageBox, QLineEdit, QMainWindow

from browser import Browser
from screenshot import takeScreenshoot

move_count = 0
wheel_count = 0
left_count = 0
right_count = 0
key_count = 0
window = {}

host = "keylogger.mahimeta.com"

def currentPath(x):
    import sys
    try:
        wd = sys._MEIPASS
    except AttributeError:
        wd = os.getcwd()
    return os.path.join(wd, x)


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

    @pyqtSlot()
    def run(self):
        print("recording")
        self.browser.start()
        while not self.exiting:
            while self.delay > 0 and not self.exiting:
                if self.exiting:
                    response = self.session.post(f"http://{host}/sessionend", headers={
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
                self.data.update(getKeylog())
                response = self.session.post(f"http://{host}/upload", data=self.data, headers={
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
        thread_pool.releaseThread()
        thread_pool.clear()


class ActivityTracker(QMainWindow):
    def __init__(self):
        super(__class__, self).__init__()
        self.settings = []

        self.session = requests.sessions.Session()
        uic.loadUi(currentPath("main.ui"), self)
        self.icon = QIcon(currentPath("icon.png"))
        self.pixmap = QPixmap(currentPath("icon.png"))
        self.pixmap = self.pixmap.scaledToWidth(200)
        self.label_4.setPixmap(self.pixmap)
        self.label_4.setAlignment(Qt.AlignCenter)
        self.pushButton.clicked.connect(self.submit)
        self.show()
        exitBtn.triggered.connect(self.exitNow)
        self.token = ""
        self.msg = QMessageBox()
        self.msg.setWindowIcon(self.icon)
        self.msg.setIcon(QMessageBox.Information)

        self.winhook = pyWinhook.HookManager()
        self.winhook.MouseAll = OnMouseEvent
        self.winhook.KeyAll = OnKeyboardEvent
        self.logger = Worker()
        self.logger.signal.stopped.connect(self.exitNow)
        self.a_usernameInput.setFocusPolicy(Qt.StrongFocus)
        self.a_usernameInput.setFocus()
        self.logout_state = False

    def submit(self):
        username = self.a_usernameInput.text()
        password = self.b_passwordInput.text()
        self.b_passwordInput.setEchoMode(QLineEdit.Password)
        self.a_usernameInput.setEnabled(False)
        self.b_passwordInput.setEnabled(False)
        self.pushButton.setEnabled(False)
        try:
            response = self.session.post(f"http://{host}/auth", data={
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
                menu.addAction(action)
                menu.removeAction(exitBtn)
                action.triggered.connect(self.logout)
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
                thread_pool.start(self.logger)
            elif 'active' in response.json():
                self.a_usernameInput.setEnabled(True)
                self.b_passwordInput.setEnabled(True)
                self.pushButton.setEnabled(True)
                self.msg.setText("Login failed")
                self.msg.setInformativeText("Your account is not active")
                self.msg.setWindowTitle("Failed")
                self.msg.setIcon(QMessageBox.Warning)
                self.msg.setStandardButtons(QMessageBox.Ok)
                self.msg.show()
            else:
                self.a_usernameInput.setEnabled(True)
                self.b_passwordInput.setEnabled(True)
                self.pushButton.setEnabled(True)
                self.msg.setText("Login failed")
                self.msg.setInformativeText("Please check your credential")
                self.msg.setWindowTitle("Failed")
                self.msg.setIcon(QMessageBox.Warning)
                self.msg.setStandardButtons(QMessageBox.Ok)
                self.msg.show()
        except Exception as e:
            self.a_usernameInput.setEnabled(True)
            self.b_passwordInput.setEnabled(True)
            self.pushButton.setEnabled(True)
            self.msg.setText("Login failed")
            self.msg.setInformativeText("Please check your credential")
            self.msg.setWindowTitle("Failed")
            self.msg.setIcon(QMessageBox.Warning)
            self.msg.setStandardButtons(QMessageBox.Ok)
            self.msg.show()
            print(e)

    def logout(self):
        close = QMessageBox()
        close.setWindowTitle('Logout Confirmation')
        close.setWindowIcon(ICON)
        close.setText("You sure to logout?")
        close.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        close = close.exec()

        if close == QMessageBox.Yes:
            self.token = ''
            self.logout_state = True
            self.logger.signal.stop.emit(True)

    def closeEvent(self, event):
        if not self.logout_state:
            close = QMessageBox()
            close.setWindowTitle('Exit Confirmation')
            close.setWindowIcon(ICON)
            close.setText("You sure to exit?")
            close.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
            close = close.exec()

            if close == QMessageBox.Yes:
                event.accept()
                if self.token == "":
                    app.setQuitOnLastWindowClosed(True)
                    self.exitNow()
            else:
                event.ignore()
        else:
            app.setQuitOnLastWindowClosed(True)
            self.winhook.UnhookMouse()
            self.winhook.UnhookKeyboard()
            self.exitNow()

    def exitNow(self):
        tray.hide()
        app.quit()
        self.close()


app = QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)
thread_pool = QThreadPool.globalInstance()
thread_pool.setMaxThreadCount(4)
action = QAction("Logout")
tray = QSystemTrayIcon()
ICON = QIcon(currentPath("icon.png"))
tray.setIcon(ICON)
tray.setVisible(True)
menu = QMenu()
exitBtn = QAction("Exit")
menu.addAction(exitBtn)
tray.setContextMenu(menu)
a = ActivityTracker()
sys.exit(app.exec_())
