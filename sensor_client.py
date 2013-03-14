#import json
import threading

import numpy as np
import enaml
#import zmq

from io_controller import IOController


LOGO_TOP = np.array([[0, 0, 1],
                [0, 1, 1],
                [1, 1, 1],
                [1, 0, 1],
                [.75, 0, 1],
                [.75, .75, 1],
                [.25, .75, 1],
                [.25, 0, 1],
                ])

LOGO_LEFT = np.array([[0, 0, 1],
                      [0, 0, 0],
                      [1, 0, 0],
                      [1, 0, .25],
                      [.25, 0, .25],
                      [.25, 0, 1],
                ])

LOGO_RIGHT = np.array([[1, 0, 0],
                      [1, 1, 0],
                      [1, 1, .25],
                      [1, 0, .25],
                ])


ACC_MAX = 1024
ACC_MIN = 0

INPUT_MAP = ['x', 'y', 'z', 'comp', 'dist', 'pot']
OUTPUT_MAP = ['led', 'servo', 'motor']


class SensorApp(object):

    def __init__(self, ip='jj.ax.lt', port=2012):
        self.ip = ip
        self.port = port

        self._run = True

        self.io_controller = IOController()

        self.start()

    def start(self):
        self._sensor_client_thread = threading.Thread(
                target=self._sensor_client_worker)
        self._sensor_client_thread.start()

    def stop(self):
        self._run = False

    def _sensor_client_worker(self):
        while self._run:
            updates = {'acc_x': int(np.random.random() * 1024),
                           'acc_y': int(np.random.random() * 1024),
                           'acc_z': int(np.random.random() * 1024),
                           'compass_heading': np.random.random() * 360,
                           'distance': np.random.random() * 90,
                           'potentiometer': np.random.random()}
            self.io_controller.set(**updates)
            import time
            time.sleep(.1)
        #context = zmq.Context()

        ##  Socket to talk to server
        #socket = context.socket(zmq.REQ)
        #socket.connect("tcp://{}:{}".format(self.ip, self.port))

        #while self._run:
        #    socket.send('r')
        #    message = socket.recv()
        #    self.sensor_control.set(**json.loads(message))
        #socket.close()


if __name__ == '__main__':
    from enaml.stdlib.sessions import show_simple_view
    with enaml.imports():
        from sensor_view import SensorViewWindow
    sensor_app = SensorApp()
    window = SensorViewWindow(io_controller=sensor_app.io_controller)
    show_simple_view(window)
    sensor_app.stop()
