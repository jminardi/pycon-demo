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


class ConnectionsComponent(Component):

    # List of lines to draw
    lines = List()

    b = Int(30)

    r = Int(15)

    bgcolor = (0.9294, 0.9294, 0.9294)

    def draw(self, gc, **kwargs):
        super(ConnectionsComponent, self).draw(gc, **kwargs)
        with gc:
            self._draw_endpoints(gc)
            self._draw_lines(gc)
        return

    def _draw_endpoints(self, gc):
        self.w, self.h = w, h = gc.width(), gc.height()
        gc.set_stroke_color((37/255., 51/255., 112/255., 1))
        gc.set_line_width(4.0)
        self.r = r = 15
        self.b = b = 30
        s = h / 13
        self.left_circle_pos = lcp = np.linspace(s, h - s, N_INPUTS)
        self.right_circle_pos = rcp = lcp[:N_OUTPUTS]
        for y_coord in lcp:
            gc.arc(b, y_coord, r, 0, 360)
        for y_coord in rcp:
            gc.arc(w - b, y_coord, r, 0, 360)
        gc.stroke_path()

    def _draw_lines(self, gc):
        w, h = gc.width(), gc.height()
        gc.set_line_width(4.0)
        gc.set_stroke_color((172/255., 175/255., 179/255., 1))
        for line in self.lines:
            x1, y1, x2, y2 = line
            gc.move_to(x1, y1)
            gc.line_to(x2, y2)
        gc.stroke_path()

    def normal_key_pressed(self, event):
        print "key pressed: ", event.character

    def normal_left_down(self, event):
        circle_y = self._get_nearest_circle(event.x, event.y)
        if circle_y is not None:
            self.lines.append([self.b, circle_y, event.x, event.y])
            self.event_state = 'connecting'
            event.handled = True
            self.request_redraw()
        else:
            pass
            # XXX Implement this
            #clicked_line = self._get_nearest_line(self, x, y)
            #if clicked_line:
            #    self.lines.pop(clicked_line)

    def connecting_left_down(self, event):
        circle_y = self._get_nearest_circle(event.x, event.y)
        if circle_y:
            self.lines[-1][2:] = [self.w - self.b, circle_y]
        else:
            self.lines.pop()
        self.event_state = 'normal'
        event.handled = True
        self.request_redraw()

    def connecting_mouse_move(self, event):
        self.lines[-1][-2:] = [event.x, event.y]
        event.handled = True
        self.request_redraw()

    def _get_nearest_circle(self, x, y):
        """ Returns the nearest circle or None if there are no circles within
            `distance` of x and y.

        """
        if self.event_state == 'normal':  # only check input circles
            left_gutter = self.b + self.r
            if x > left_gutter:  # border + radius
                return None
            for circle_y in self.left_circle_pos:
                if circle_y - self.r < y and circle_y + self.r > y:
                    return circle_y
            return None

        if self.event_state == 'connecting':  # only check output cirlces
            right_gutter = self.w - (self.b + self.r)
            if x < right_gutter:
                return None
            for circle_y in self.right_circle_pos:
                if circle_y - self.r < y and circle_y + self.r > y:
                    return circle_y
            return None


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
        return ConnectionsComponent()

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
