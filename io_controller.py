import numpy as np
from matplotlib.pyplot import Figure
from mpl_toolkits.mplot3d import art3d, Axes3D
from enable.api import Component
from traits.api import (HasStrictTraits, Int, Float, Instance, Any,
        on_trait_change)
from chaco.api import Plot, ArrayPlotData

from links_component import LinksComponent


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
        return LinksComponent()

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

    @on_trait_change('link_plot.links[]')
    def _links_changed(self, new):
        print new
