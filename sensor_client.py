#import json
import threading

import numpy as np
import enaml
#import zmq
from enable.api import Component
from chaco.api import Plot, ArrayPlotData
from traits.api import (HasStrictTraits, Int, on_trait_change, Float,
        Instance, Any, List)
from matplotlib.pyplot import Figure
from mpl_toolkits.mplot3d import art3d, Axes3D


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
N_INPUTS = 6
N_OUTPUTS = 3


class Box(Component):
    lines = List()

    bgcolor = (0.9294, 0.9294, 0.9294)

    def draw(self, gc, **kwargs):
        super(Box, self).draw(gc, **kwargs)
        with gc:
            self._draw_endpoints(gc)
            self._draw_lines(gc)
            gc.stroke_path()
        return

    def _draw_endpoints(self, gc):
        w, h = gc.width(), gc.height()
        gc.set_line_width(2.0)
        gc.set_stroke_color((0.0, 0.0, 0.0, 1.0))
        r = 15
        b = 30
        s = h / 13
        left_circle_pos = np.linspace(s, h - s, N_INPUTS)
        right_circle_pos = left_circle_pos[:N_OUTPUTS]
        for y_coord in left_circle_pos:
            gc.arc(b, y_coord, r, 0, 360)
        for y_coord in right_circle_pos:
            gc.arc(w - b, y_coord, r, 0, 360)

    def _draw_lines(self, gc):
        w, h = gc.width(), gc.height()
        gc.set_line_width(2.0)
        gc.set_stroke_color((0.0, 0.0, 0.0, 1.0))
        for line in self.lines:
            x1, y1, x2, y2 = line
            gc.move_to(x1, y1)
            gc.line_to(x2, y2)

    def normal_key_pressed(self, event):
        print "key pressed: ", event.character

    def normal_mouse_move(self, event):
        self.lines = [(30, 30, event.x, event.y)]
        self.request_redraw()


class IOController(HasStrictTraits):

    ### Sensors  ##############################################################

    acc_x = Int(plot_data=True)

    acc_y = Int(plot_data=True)

    acc_z = Int(plot_data=True)

    compass_heading = Float(plot_data=True)

    distance = Float(plot_data=True)

    potentiometer = Float(plot_data=True)

    ### Plots  ################################################################

    logo_plot = Instance(Figure)

    acc_x_plot = Instance(Plot)

    acc_y_plot = Instance(Plot)

    acc_z_plot = Instance(Plot)

    compass_plot = Instance(Plot)

    distance_plot = Instance(Plot)

    pot_plot = Instance(Plot)

    link_plot = Instance(Component)

    plot_data = Instance(ArrayPlotData)

    _logo_ax = Any()

    ### Outputs  ##############################################################

    led_value = Int(output=True)

    servo_value = Int(output=True)

    motor_value = Int(output=True)

    ### Trait Defaults  #######################################################

    def _logo_plot_default(self):
        fig = Figure()
        self._logo_ax = ax = Axes3D(fig)
        ax.set_axis_off()
        top = art3d.Poly3DCollection([LOGO_TOP])
        top.set_color('#253370')
        top.set_edgecolor('#253370')
        left = art3d.Poly3DCollection([LOGO_LEFT])
        left.set_color('#acafb3')
        left.set_edgecolor('#acafb3')
        right = art3d.Poly3DCollection([LOGO_RIGHT])
        right.set_color('#253370')
        right.set_edgecolor('#253370')
        ax.add_collection3d(top)
        ax.add_collection3d(left)
        ax.add_collection3d(right)
        return fig

    def _acc_x_plot_default(self):
        plot = Plot(self.plot_data)
        plot.plot(('acc_x',))
        plot.padding = (0, 0, 0, 0)
        return plot

    def _acc_y_plot_default(self):
        plot = Plot(self.plot_data)
        plot.plot(('acc_y',))
        plot.padding = (0, 0, 0, 0)
        return plot

    def _acc_z_plot_default(self):
        plot = Plot(self.plot_data)
        plot.plot(('acc_z',))
        plot.padding = (0, 0, 0, 0)
        return plot

    def _compass_plot_default(self):
        plot = Plot(self.plot_data)
        plot.plot(('compass_heading',))
        plot.padding = (0, 0, 0, 0)
        return plot

    def _distance_plot_default(self):
        plot = Plot(self.plot_data)
        plot.plot(('distance',))
        plot.padding = (0, 0, 0, 0)
        return plot

    def _pot_plot_default(self):
        plot = Plot(self.plot_data)
        plot.plot(('potentiometer',))
        plot.padding = (0, 0, 0, 0)
        return plot

    def _link_plot_default(self):
        return Box()

    def _plot_data_default(self):
        plot_data = ArrayPlotData()
        plot_data.set_data('compass_heading', np.zeros(50))
        plot_data.set_data('distance', np.zeros(50))
        plot_data.set_data('potentiometer', np.zeros(50))
        plot_data.set_data('compass_heading', np.zeros(50))
        plot_data.set_data('acc_x', np.zeros(50))
        plot_data.set_data('acc_y', np.zeros(50))
        plot_data.set_data('acc_z', np.zeros(50))
        return plot_data

    def clicked(self, win):
        import ipdb
        ipdb.set_trace()  # XXX BREAKPOINT

    ### Trait Change Handlers  ################################################

    @on_trait_change('+plot_data')
    def _push_to_plot_data(self, name, new):
        # XXX This is causing NSConcreteMapTable to leak
        ary = self.plot_data[name]
        if ary is not None:
            ary = np.append(ary, new)
            ary = ary[-50:]
            self.plot_data.set_data(name, ary)

    @on_trait_change('acc_x, acc_y, acc_z')
    def _update_logo_plot(self):
        ax = self._logo_ax
        if ax and ax.figure.canvas:
            ax.azim += 1
            ax.figure.canvas.draw()


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
