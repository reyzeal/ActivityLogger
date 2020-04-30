import base64
import os
import warnings
import ctypes
from io import BytesIO

import win32api
import win32con
import win32gui
import wx
from PIL import Image

warnings.filterwarnings("ignore", category=DeprecationWarning)


def get_concat_h(im1, im2):
    dst = Image.new('RGB', (im1.width + im2.width, im1.height))
    dst.paste(im1, (0, 0))
    dst.paste(im2, (im1.width, 0))
    return dst


class App(wx.App):
    def OnInit(self):
        dll = ctypes.WinDLL('gdi32.dll')
        for idx, (hMon, hDC, (left, top, right, bottom)) in enumerate(win32api.EnumDisplayMonitors(None, None)):
            hDeskDC = win32gui.CreateDC(win32api.GetMonitorInfo(hMon)['Device'], None, None)
            bitmap = wx.Bitmap(right - left, bottom - top)
            hMemDC = wx.MemoryDC()
            hMemDC.SelectObject(bitmap)
            try:
                dll.BitBlt(hMemDC.GetHDC(), 0, 0, right - left, bottom - top, int(hDeskDC), 0, 0, win32con.SRCCOPY)
            finally:
                hMemDC.SelectObject(wx.NullBitmap)
            bitmap.SaveFile('screenshots/screenshot_%02d.bmp' % idx, wx.BITMAP_TYPE_BMP)
            win32gui.ReleaseDC(win32gui.GetDesktopWindow(), hDeskDC)
        im1 = Image.open('screenshots/screenshot_00.bmp', 'r')
        for idx, (hMon, hDC, (left, top, right, bottom)) in enumerate(win32api.EnumDisplayMonitors(None, None)):
            if idx == 0:
                continue
            im2 = Image.open('screenshots/screenshot_%02d.bmp' % idx, 'r')
            im1 = get_concat_h(im1, im2)
        im1.save('screenshots/screenshot.jpg')
        return True


def takeScreenshoot():
    if not os.path.exists('screenshots'):
        os.mkdir('screenshots')
    App(0).Destroy()
    buffered = BytesIO()
    Image.open('screenshots/screenshot.jpg').save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue())
    return img_str


if __name__ == '__main__':
    takeScreenshoot()
