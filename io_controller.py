import numpy as np
from matplotlib.pyplot import Figure
from mpl_toolkits.mplot3d import art3d, Axes3D
from enable.api import Component
from traits.api import (HasStrictTraits, Int, Float, Instance, Any, Dict,
        on_trait_change, Set, List, Event)
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


# Map of input names and the amount needed to normalize them
INPUT_MAP = [('potentiometer', 1024.0),
            ('distance', 100.0),
            ('switch', 1),
            ('acc_z', 1024.0),
            ('acc_y', 1024.0),
            ('acc_x', 1024.0)]

OUTPUT_MAP = ['motor', 'servo', 'led']


class IOController(HasStrictTraits):

    ### Current Sensor Values  ################################################

    acc_x = Int(plot_data=True)

    acc_y = Int(plot_data=True)

    acc_z = Int(plot_data=True)

    switch = Float(plot_data=True)

    distance = Float(plot_data=True)

    potentiometer = Float(plot_data=True)

    ### Plots  ################################################################

    logo_plot = Instance(Figure)

    acc_x_plot = Instance(Plot)

    acc_y_plot = Instance(Plot)

    acc_z_plot = Instance(Plot)

    switch_plot = Instance(Plot)

    distance_plot = Instance(Plot)

    pot_plot = Instance(Plot)

    link_plot = Instance(Component)

    plot_data = Instance(ArrayPlotData)

    _logo_ax = Any()

    ### Outputs  ##############################################################

    led_value = Int(output=True)

    servo_value = Int(output=True)

    motor_value = Int(output=True)

    ### IOController Interface  ###############################################

    added_links = List()

    removed_links = List()

    outputs = Dict()

    rotate_logo = Event()

    ### Private Traits  #######################################################

    _current_links = Set()

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

    def _switch_plot_default(self):
        plot = Plot(self.plot_data)
        plot.plot(('switch',))
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
        plot_data.set_data('distance', np.zeros(50))
        plot_data.set_data('potentiometer', np.zeros(50))
        plot_data.set_data('switch', np.zeros(50))
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

    @on_trait_change('+output')
    def _push_to_server(self, name, new):
        self.outputs[name] = new
        print self.outputs

    #@on_trait_change('acc_x, acc_y, acc_z')
    #def _update_logo_plot(self):
    #    ax = self._logo_ax
    #    if ax and ax.figure.canvas:
    #        xyz = - (np.array([self.acc_x, self.acc_y, self.acc_z]) / -800.0) - .5
    #        print xyz, np.array([self.acc_x, self.acc_y, self.acc_z])
    #        elev, azim = cart_to_sph(xyz)
    #        print 'new elev, azim:', elev, azim
    #        ax.elev = elev * 360
    #        ax.azim = azim * 360

    @on_trait_change('rotate_logo')
    def _rotate_logo_plot(self):
        ax = self._logo_ax
        if ax and ax.figure.canvas:
            ax.azim += 1
            ax.figure.canvas.draw()

    @on_trait_change('link_plot.links[]')
    def _links_changed(self, new):
        new = set(new)
        old = self._current_links
        added = new - old
        added_links = []
        for i, out in added:
            added_links.append((INPUT_MAP[i], OUTPUT_MAP[out]))
        removed = old - new
        removed_links = []
        for i, out in removed:
            removed_links.append((INPUT_MAP[i], OUTPUT_MAP[out]))
        self._current_links = new
        self.added_links.extend(added_links)
        self.removed_links.extend(removed_links)
        print added, removed


def cart_to_sph(xyz):
    xy = xyz[0] ** 2 + xyz[1] ** 2
    #elev = np.arctan2(np.sqrt(xy), xyz[2])  # for elevation angle defined from Z-axis down
    elev = np.arctan2(xyz[2], np.sqrt(xy))  # for elevation angle defined from XY-plane up
    azim = np.arctan2(xyz[1], xyz[0])
    return elev, azim
