import PySimpleGUI as sg
import psutil

from dataclasses import dataclass, field

sg.theme('black')

GRAPH_W = 160
GRAPH_H = 40
STEP = 5

MEGABYTE = 1024*1024
GIGABYTE = MEGABYTE*1024
NETWORK_BANDWIDTH = 2


@dataclass
class LineGraph:
    name: str
    color: str
    width: int = GRAPH_W
    height: int = GRAPH_H
    sg_text: sg.Text = field(init=False)
    sg_graph: sg.Graph = field(init=False)
    items: list = field(default_factory=list)
    pos_x: int = 0
    last_x: int = 0
    last_y: int = 0

    def __post_init__(self):
        self.sg_text = sg.Text(self.name, font=('Tahoma', 8), key=self.name+'-txt')
        self.sg_graph = sg.Graph((self.width, self.height), (0, 0), (self.width, self.height),
                                 key=self.name+'-graph', background_color='white')

    def update_graph(self, value):
        pos_y = value * self.height/100
        self.items.append(self.sg_graph.draw_line(
            (self.last_x, self.last_y),
            (self.pos_x, pos_y),
            color=self.color,
            width=1,
        ))

        self.last_x, self.last_y = self.pos_x, pos_y
        if self.pos_x > self.width:
            self.sg_graph.delete_figure(self.items[0])
            self.sg_graph.move(-STEP, 0)
            self.last_x -= STEP
            self.items.pop(0)
        else:
            self.pos_x += STEP

    def update_text(self, text):
        self.sg_text.update(text)

    @property
    def layout(self):
        return sg.Column([[self.sg_text], [self.sg_graph]], pad=(1, 1))


def main():
    cpu_graph = LineGraph('CPU', 'blue')
    mem_graph = LineGraph('Memory', 'purple')
    net_graph = LineGraph('Network', 'green')

    layout = [[cpu_graph.layout], [mem_graph.layout], [
        net_graph.layout], [sg.Exit(font=('Tahoma', 10), size=(5, 1))]]
    window = sg.Window('Monitoring', layout, relative_location=(500, 50), no_titlebar=True,
                       keep_on_top=True, alpha_channel=0.4, grab_anywhere=True, finalize=True)

    sw, sh = window.get_screen_size()
    ww, wh = window.size

    window.move(sw-ww, wh)  # center-right

    net_last_recv = psutil.net_io_counters().bytes_recv
    while True:
        event, values = window.read(timeout=500)    # polling frequency
        if event in (None, 'Exit'):
            break
        cpu_perf = psutil.cpu_percent()
        cpu_freq = (psutil.cpu_freq().current/1000) * (cpu_perf/100)
        cpu_graph.update_graph(cpu_perf)
        cpu_graph.update_text(f"CPU: {cpu_perf:.0f}% {cpu_freq:.2f} GHz")

        mem = psutil.virtual_memory()
        mem_graph.update_graph(mem.percent)
        mem_graph.update_text(
            f"Memory: {mem.used/GIGABYTE:.1f}/{mem.total/GIGABYTE:.1f} GB ({mem.percent}%)")

        global NETWORK_BANDWIDTH
        net_recv = psutil.net_io_counters().bytes_recv
        net_recv_val = (net_recv - net_last_recv)/MEGABYTE
        while net_recv_val > NETWORK_BANDWIDTH:
            NETWORK_BANDWIDTH += 1
        net_last_recv = net_recv
        net_graph.update_graph(net_recv_val*100/NETWORK_BANDWIDTH)   # to percentage
        net_graph.update_text(
            f"Network: {net_recv_val:.2f}/{NETWORK_BANDWIDTH:.2f} MBs")

    window.close()


if __name__ == '__main__':
    main()
