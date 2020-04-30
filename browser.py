import threading
from time import sleep

from scapy.layers.http import HTTP
from scapy.layers.tls.extensions import TLS_Ext_ServerName
from scapy.layers.tls.record import TLS
from scapy.sendrecv import sniff


class Browser:
    def __init__(self):
        self.state = True
        self.threading = threading.Thread(target=self.process, args=())
        self.url = []

    def extract(self, packet):
        try:
            if packet.haslayer(TLS):
                # pprint(packet[TLS].msg)
                for i in packet[TLS].msg[0].ext:
                    if isinstance(i, TLS_Ext_ServerName):
                        # print('https', i.servernames[0].servername)
                        self.url.append(i.servernames[0].servername.decode("utf-8"))
            elif packet.haslayer(HTTP) and 'html' in packet[HTTP].Accept.decode("utf-8"):
                self.url.append(packet[HTTP].Host.decode("utf-8"))
        except Exception as e:
            return

    def process(self):
        while self.state:
            try:
                sniff(prn=self.extract, filter="port 80 or port 443", store=False, stop_filter=self.state)
            except:
                pass

    def start(self):
        self.threading.start()
        pass

    def stop(self):
        self.state = False
        self.threading.join(10)
        pass

    def getList(self):
        data = self.url.copy()
        self.url = []
        return data


if __name__ == '__main__':
    c = Browser()
    c.start()
    while True:
        sleep(10)
