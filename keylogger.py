import _thread
from time import sleep

import win32gui
import pyWinhook
# import sqlite3

# DBconnection = sqlite3.connect('db.sqlite3')
# mouse_sql = """
# CREATE TABLE IF NOT EXISTS mouse (
#     id integer PRIMARY KEY,
#     left_click integer,
#     right_click integer,
#     mouse_move integer,
#     mouse_wheel integer,
#     detected_at timestamp DEFAULT (datetime('now','localtime'))
# )
# """
# keyboard_sql = """
# CREATE TABLE IF NOT EXISTS keyboard(
#     id integer PRIMARY KEY,
#     keydown integer,
#     detected_at timestamp DEFAULT (datetime('now','localtime'))
# )
# """
#
# window_sql = """
# CREATE TABLE IF NOT EXISTS window(
#     id integer PRIMARY KEY,
#     window_name varchar(100),
#     activity integer,
#     detected_at timestamp DEFAULT (datetime('now','localtime'))
# )
# """
# cursor = DBconnection.cursor()
# cursor.execute(mouse_sql)
# cursor.execute(keyboard_sql)
# cursor.execute(window_sql)
# cursor.close()
# DBconnection.commit()
move_count = 0
wheel_count = 0
left_count = 0
right_count = 0
key_count = 0
window = {}


def OnMouseEvent(event):
    global move_count, left_count, right_count, wheel_count, window
    if window.get(event.WindowName, None) is None:
        window[event.WindowName] = 1
    window[event.WindowName] += 1
    print(event.MessageName)
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


# def Record():
#     global window, left_count, right_count, move_count, key_count, window, wheel_count
#     # DBconnection = sqlite3.connect('db.sqlite3')
#     # cursor = DBconnection.cursor()
#     while True:
#         sleep(60)
#         # cursor.execute(f"INSERT INTO mouse(left_click, right_click, mouse_move, mouse_wheel) VALUES ({left_count},{right_count},{move_count}, {wheel_count});")
#         # cursor.execute(f"INSERT INTO keyboard(keydown) VALUES ({key_count});")
#         # for key in window.keys():
#         #     cursor.execute("""INSERT INTO window(window_name,activity) VALUES (?,?);""", (key,window[key]))
#         # DBconnection.commit()
#         window = {}
#         left_count = 0
#         right_count = 0
#         move_count = 0
#         key_count = 0
#         wheel_count = 0
#         print("Last 60 seconds data inserted")

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


def activateKeylogger():
    # _thread.start_new(Record, ())

    hm = pyWinhook.HookManager()
    print("keylogger activated")
    hm.MouseAll = OnMouseEvent
    print("mouse event setup")
    hm.KeyAll = OnKeyboardEvent
    print("keyboard event setup")
    hm.HookMouse()
    hm.HookKeyboard()
    print("listening..")
    win32gui.PumpMessages()
