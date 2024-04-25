# ### License
#------------------------------------------------------------------------------------------
# Copyright (C) 2022, Xilinx, Inc.
# Copyright (C) 2022-2023, Advanced Micro Devices, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");<br>
# you may not use this file except in compliance with the License.<br><br>
# You may obtain a copy of the License at <a href="http://www.apache.org/licenses/LICENSE-2.0"?>http://www.apache.org/licenses/LICENSE-2.0</a><br><br>
# Unless required by applicable law or agreed to in writing, software<br>
# distributed under the License is distributed on an "AS IS" BASIS,<br>
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.<br>
# See the License for the specific language governing permissions and<br>
# limitations under the License.<br>
#
#------------------------------------------------------------------------------------------
# # IBERT yk scan example
# ## Description
# This example shows how to interact with the IBERT (Integrated Bit Error Ratio Tester) debug core service via ChipScoPy APIs.
# - Program the ChipScoPy CED design onto the XCVP1202 device on a VPK120 board
# - Verify that the expected IBERT quads are instantiated by the design
# - Run and plot YK scans
#
# ## Requirements
# - Local or remote Xilinx Versal board, VPK120 or VHK158 (only)
# - Xilinx hw_server 2023.2 installed and running
# - Xilinx cs_server 2023.2 installed and running
# - Python 3.8 or greater installed
# - ChipScoPy 2023.2 installed
# - Jupyter notebook support installed - Please do so, using the command `pip install chipscopy[jupyter]`
# - Plotting support installed - Please do so, using the command `pip install chipscopy[core-addons]`
# - [External loopback](https://www.samtec.com/kits/optics-fpga/hspce-fmcp/)
# - This example assumes that the device has already been programmed with the example design (ie the debug cores have already been initialized)

#------------------------------------------
"""
export ip="10.20.2.146";     export CS_SERVER_URL="TCP:$ip:3042" HW_SERVER_URL="TCP:$ip:3121"
export HW_PLATFORM="vpk120"; export CREATE_LGROUP=False
export PLOT_1_RESOL_X=900;   export PLOT_1_RESOL_Y=800;  export PLOT_F_RESOL_X=3840;  export PLOT_F_RESOL_Y=2160
export PROG_DEVICE=True;     export PDI_FILE="./VPK120_iBERT_2xQDD_56G.pdi"
export SHOW_FIG_TITLE=True;  export MAX_SLICES=100;
export QUAD_NAME="Quad_202"; export QUAD_CHAN=2;
"""

#------------------------------------------------------------------------------------------
# ## 1 - Initialization: Imports
#
# After this step,
# * Required functions and classes are imported
# * Paths to server(s) and files are set correctly
#------------------------------------------------------------------------------------------
import os
from more_itertools import one

from chipscopy import create_session, report_versions, report_hierarchy, get_design_files
from chipscopy.api.ibert import create_yk_scans
from chipscopy.api.ibert import delete_link_groups, get_all_links, get_all_link_groups, create_links, create_link_groups
from chipscopy.api.ibert.aliases import ( PATTERN,
    EYE_SCAN_HORZ_RANGE, EYE_SCAN_VERT_RANGE, EYE_SCAN_VERT_STEP, EYE_SCAN_HORZ_STEP, EYE_SCAN_TARGET_BER,
    TX_PRE_CURSOR, TX_POST_CURSOR, TX_DIFFERENTIAL_SWING,
    RX_LOOPBACK, RX_BER, RX_STATUS, RX_LINE_RATE, RX_RECEIVED_BIT_COUNT, RX_NORMALIZED_RECEIVED_BIT_COUNT, RX_PATTERN_CHECKER_ERROR_COUNT, RX_TERMINATION_VOLTAGE, RX_COMMON_MODE
)

#------------------------------------------
from PyQt5 import QtWidgets, QtCore, QtGui
import sys
import random
import math
import re
import numpy as np

import matplotlib
matplotlib.use("Qt5Agg")      # 表示使用 Qt5
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar

#------------------------------------------------------------------------------------------
# ## 2 - Create a session and connect to the hw_server and cs_server
#
# The session is a container that keeps track of devices and debug cores.
# After this step,
# - Session is initialized and connected to server(s)
# - Versions are detected and reported to stdout

# %%
# Specify locations of the running hw_server and cs_server below.
#------------------------------------------------------------------------------------------

PLOT_1_RESOL_X = int(os.getenv("PLOT_1_RESOL_X", "900"))
PLOT_1_RESOL_Y = int(os.getenv("PLOT_1_RESOL_Y", "800"))
PLOT_F_RESOL_X = int(os.getenv("PLOT_F_RESOL_X", "3200"))
PLOT_F_RESOL_Y = int(os.getenv("PLOT_F_RESOL_Y", "1900"))

QUAD_NAME    =     os.getenv("QUAD_NAME", "Quad_202")
QUAD_CHAN    = int(os.getenv("QUAD_CHAN", "0"))

CS_URL = os.getenv("CS_SERVER_URL", "TCP:localhost:3042")
HW_URL = os.getenv("HW_SERVER_URL", "TCP:localhost:3121")

# specify hw and if programming is desired
HW_PLATFORM = os.getenv("HW_PLATFORM", "vpk120")
PROG_DEVICE = os.getenv("PROG_DEVICE", 'True').lower() in ('true', '1', 't')
CREATE_LGROUP = os.getenv("CREATE_LGROUP", 'True').lower() in ('true', '1', 't')

MAX_SLICES   = int(os.getenv("MAX_SLICES", "200"))
SHOW_FIG_TITLE = os.getenv("SHOW_FIG_TITLE", 'False').lower() in ('true', '1', 't')

# The get_design_files() function tries to find the PDI and LTX files. In non-standard
# configurations, you can put the path for PROGRAMMING_FILE and PROBES_FILE below.
design_files = get_design_files(f"{HW_PLATFORM}/production/chipscopy_ced")
PDI_FILE = design_files.programming_file
PDI_FILE = os.getenv("PDI_FILE", "./VPK120_iBERT_2xQDD_56G.pdi")

print(f"PROGRAMMING_FILE: {PDI_FILE}")
print(f"Servers URL: {CS_URL} {HW_URL} HW: {HW_PLATFORM}  Do_Programming: {PROG_DEVICE}\n")

session = create_session(cs_server_url=CS_URL, hw_server_url=HW_URL)
report_versions(session)

# %% [markdown]
# ## 3 - Program the device with the example design
# After this step,
# * Device is programmed with the example programming file

# %%
# Typical case - one device on the board - get it.
device = session.devices.filter_by(family="versal").get()
if PROG_DEVICE:
    device.program(PDI_FILE)
else:
    print("skipping programming")

# %% [markdown]
# ## 4 - Discover and setup the IBERT core
#
# Debug core discovery initializes the chipscope server debug cores.
#
# After this step,
#
# - The cs_server is initialized and ready for use
# - The first ibert found is used

# %%
# # Set any params as needed
# params_to_set = {"IBERT.internal_mode": True}
# session.set_param(params_to_set)
#device = session.devices.filter_by(family="versal").get()

# Use the first available device and set up its debug cores

print(f"Discovering debug cores...")
device.discover_and_setup_cores(ibert_scan=True)

if len(device.ibert_cores) == 0:
    print("No IBERT core found! Exiting...")
    exit()

# %% [markdown]
# ## 5 - Print the hierarchy of the IBERT core
# We also ensure that all the quads instantiated by the ChipScoPy CED design are found by the APIs

# %%
# Use the first available IBERT core from the device
print(f"--> Found {[f'{ibert.name} ({ibert.handle})' for ibert in device.ibert_cores]}\n")

ibert_gtm = one(device.ibert_cores.filter_by(name="IBERT Versal GTM"))

if len(ibert_gtm.gt_groups) == 0:
    print("No GT Groups available for use! Exiting...")
    exit()

# We also ensure that all the quads instantiated by the ChipScoPy CED design are found by the APIs
report_hierarchy(ibert_gtm)
print(f"--> GT Groups available - {ibert_gtm.gt_groups}")
#rint(f"==> GT Groups available - {[gt_group_obj.name for gt_group_obj in ibert_gtm.gt_groups]}")


#------------------------------------------------------------------------------------------
class FakeYKLink():
    def __init__(self):
        self.status      = "53.109 Gbps"
        self.line_rate   = "53.121 Gbps"
        self.bit_count   = 0
        self.error_count = 0
        self.ber         = random.random() / 1000000

class MyYKScan():
    def __init__(self, gt_group, gt_chan):
        self.YKName = f"YK-{gt_group.name}[{gt_chan}]"
        self.fig = plt.figure(FigureClass=MyYKFigure, layout='constrained', num=self.YKName, figsize=[8,6])   # figsize=[12,10]  dpi=100
        self.fig.init_YK_axes(self.YKName)

        self.RX  = gt_group.gts[gt_chan].rx
        self.TX  = gt_group.gts[gt_chan].tx
        self.PLL = gt_group.gts[gt_chan].pll
        self.YK  = create_yk_scans(target_objs=gt_group.gts[gt_chan].rx)[0]
        self.YK.updates_callback = lambda obj: self.yk_scan_updates(obj)

        if CREATE_LGROUP:   self.link = self.RX.link
        else:               self.link = FakeYKLink()
        self.ber   = self.link.ber

        #------------------------------------------------------------------------------
        print(f"GT:{gt_group.name} CH:{gt_chan}::  RX='{self.RX}'  RX-link='{self.RX.link}'  RX-pll='{self.RX.pll}' RX-yk_scan='{self.RX.yk_scan}' ")
        print(f"GT:{gt_group.name} CH:{gt_chan}::  TX='{self.TX}'  TX-link='{self.TX.link}'  TX-pll='{self.TX.pll}' ")
        print(f"GT:{gt_group.name} CH:{gt_chan}::  SELF={self}  LINK='{self.link}' values=({self.link.ber}, {self.link.status}, {self.link.line_rate}, {self.link.bit_count}, {self.link.error_count}) ")
        #       GT:Quad_202 CH:0::  RX='IBERT_0.Quad_202.CH_0.RX(RX)'  RX-link='None'  RX-pll='IBERT_0.Quad_202.PLL_0(PLL/LCPLL0)' RX-yk_scan='YKScan_1' 
        #       GT:Quad_202 CH:0::  TX='IBERT_0.Quad_202.CH_0.TX(TX)'  TX-link='None'  TX-pll='IBERT_0.Quad_202.PLL_0(PLL/LCPLL0)' 
        #------------------------------------------------------------------------------

    def update_link(self):
        self.status      = self.link.status
        self.line_rate   = self.link.line_rate
        self.bit_count   = self.link.bit_count
        self.error_count = self.link.error_count
        self.ber         = self.link.ber                                                                                      # main BER read method: works
        #self.ber1       = self.link.rx.property_for_alias(RX_BER)                                                            # another BER method 1: not working
        #self.ber2       = list(self.link.rx.property.refresh(self.link.rx.property_for_alias[RX_BER]).values())[0]           # another BER method 2: works, almost the same value as <self.link.ber>
        print(f"SELF={self}  LINK='{self.link}' values=({self.ber}, {self.status}, {self.line_rate}, {self.bit_count}, {self.error_count}) ")

    # ## 6 - Define YK Scan Update Method
    def yk_scan_updates(self, obj):
        #------------------------------------------------------------------------------
        # BER by random number simulation: it works
        #------------------------------------------------------------------------------
        ber = random.random() / 1000000
        #self.fig.update_yk_ber(ber)

        #------------------------------------------------------------------------------
        # BER from chipscopy.api.ibert.rx.link for its BER / STAUS ...: NOT work
        #------------------------------------------------------------------------------
        """
        # self.count += 1; if self.count % 64 == 0: self.update_link()
        self.update_link()
        self.fig.update_yk_ber(self.ber)
        """

        #------------------------------------
        self.fig.update_yk_scan(obj)

    def yk_link_updates(self):
        self.update_link()
        self.fig.update_yk_ber(self.ber)

#------------------------------------------
class MyYKFigure(matplotlib.figure.Figure):
    # ## 8 - Run YK Scan
    #
    # Initialize the plots and start the YK Scan to begin updating the plots. 
    # YK Scan plot should contain three subplots, these plots should look something like:
    # ![yk_scan_example.png](./yk_scan_example.png)
    # Note: Depending on the hardware setup and external loopback connection, the plot might look different.
    def __init__(self, *args, **kwargs):
        # Custom initialization logic (if needed)
        super().__init__(*args, **kwargs)

    def init_YK_axes(self, fig_name):
        self.axis_X_Count = 0
        self.axis_X_OFFSET = 0
        self.YKSCAN_SLICER_SIZE = 2000
        X_max = MAX_SLICES * self.YKSCAN_SLICER_SIZE 

        # Initialize circular buffer
        self.YKScan_slicer_buf = np.zeros((0, self.YKSCAN_SLICER_SIZE))  # Assuming 2D data (x, y)
        self.scatter_X_data  = np.linspace( 0, X_max - 1, X_max )

        # Each figure corresponds to a QUAD channel
        self.fig_name = fig_name
        self.suptitle(fig_name)

        # axis of EYE diagram
        self.ax_EYE = plt.subplot2grid((3,2), (0,0), rowspan=2)
        self.ax_EYE.set_xlabel("ES Sample")
        self.ax_EYE.set_ylabel("Amplitude (%)")
        self.ax_EYE.set_xlim(0, MAX_SLICES * self.YKSCAN_SLICER_SIZE)
        self.ax_EYE.set_ylim(0,100)
        self.ax_EYE.set_yticks(range(0, 100, 20))
        if SHOW_FIG_TITLE: self.ax_EYE.set_title("Slicer eye")
        else:              self.ax_EYE.set_xlabel("EYE")

        # Set custom x-axis labels (divide by 2000)
        scatter_X_ticks  = self.scatter_X_data[0::int(X_max/5)]
        scatter_X_labels = [f"{x/self.YKSCAN_SLICER_SIZE:.0f}" for x in scatter_X_ticks]
        self.ax_EYE.set_xticks(scatter_X_ticks, scatter_X_labels)
        self.scatter_plot_EYE = self.ax_EYE.scatter([], [], s=1, color='blue')

        # axis of Histogram diagram
        self.ax_HIST = plt.subplot2grid((3,2), (0,1), rowspan=2)
        self.ax_HIST.set_xlabel("Count")
        self.ax_HIST.set_ylabel("Amplitude (%)")
        self.ax_HIST.set_xlim(0,500)
        self.ax_HIST.set_ylim(0,100)
        self.ax_HIST.set_yticks(range(0, 100, 20))
        if SHOW_FIG_TITLE: self.ax_HIST.set_title("Histogram")
        else:              self.ax_HIST.set_xlabel("Histogram")

        # axis of SNR diagram
        self.ax_SNR = plt.subplot(3,2,5)
        self.ax_SNR.set_xlabel("SNR Sample")
        self.ax_SNR.set_ylabel("SNR (dB)")
        self.ax_SNR.set_xlim(0,10)
        self.ax_SNR.set_ylim(-10,50)
        if SHOW_FIG_TITLE: self.ax_SNR.set_title("Signal-to-Noise Ratio")
        else:              self.ax_SNR.set_xlabel("SNR")

        # axis of BER diagram
        self.ax_BER = plt.subplot(3,2,6)
        self.ax_BER.set_xlabel("BER Sample")
        self.ax_BER.set_ylabel("log10")
        self.ax_BER.set_xlim(0,10)
        self.ax_BER.set_ylim(-1,-20)
        if SHOW_FIG_TITLE: self.ax_BER.set_title("Bit-Error-Rate")
        else:              self.ax_BER.set_xlabel("BER")

    # ## 6 - Define YK Scan Update Method
    # This method will be called each time the yk scan updates, allowing it to update its graphs in real time. 
    def update_yk_scan(self, obj):

        self.axis_X_Count +=1      #  ==> len(obj.scan_data) - 1
        assert self.YKSCAN_SLICER_SIZE == len(obj.scan_data[-1].slicer)

        # Update the circular buffer with new data.
        self.YKScan_slicer_buf = np.append(self.YKScan_slicer_buf, [list(obj.scan_data[-1].slicer)], axis=0)          # append new data
        if self.YKScan_slicer_buf.shape[0] > MAX_SLICES:
            self.YKScan_slicer_buf = np.delete(self.YKScan_slicer_buf, 0, axis=0)                                     # remove oldest slice data
            obj.scan_data.pop(0)
        else:
            self.axis_X_OFFSET += self.YKSCAN_SLICER_SIZE

        # Update the scatter plot with data from the buffer.
        self.scatter_plot_EYE.set_offsets(np.column_stack((self.scatter_X_data[0:self.axis_X_OFFSET], self.YKScan_slicer_buf.flatten())))  # Set new data points

        print("{}: samples#{:5d}  SHAPE: {} / {}   \t\tDATA: ({:.1f}, {:.1f}, {:.1f}, {:.1f})".format( self.fig_name,
           self.axis_X_Count, self.scatter_X_data[0:self.axis_X_OFFSET].shape, self.YKScan_slicer_buf.shape,
           obj.scan_data[-1].slicer[-1], obj.scan_data[-1].slicer[-2], obj.scan_data[-1].slicer[-3], obj.scan_data[-1].slicer[-4]))
        #self.ax_EYE.set_xlabel("ES Sample ({}): ({:.1f}, {:.1f}, {:.1f})".format(self.axis_X_Count, obj.scan_data[-1].slicer[-1], obj.scan_data[-1].slicer[-2], obj.scan_data[-1].slicer[-3]))

        if self.ax_HIST.lines:
            for line2 in self.ax_HIST.lines:
                self.ax_HIST.set_xlim(0, self.ax_HIST.get_xlim()[1] + self.YKSCAN_SLICER_SIZE)
                line2.set_xdata(list(line2.get_xdata()) + list(range(len(line2.get_xdata()), len(line2.get_xdata()) + self.YKSCAN_SLICER_SIZE)))
                line2.set_ydata(list(line2.get_ydata()) + list(obj.scan_data[-1].slicer))
        else:
            #self.ax_HIST.cla()
            #color: blue / green / teal / brown / charcoal / black / gray / silver / cyan / violet
            self.ax_HIST.hist(list(obj.scan_data[-1].slicer), 50, orientation = 'horizontal', color='cyan', stacked=True, range=(0,100))

        if self.ax_SNR.lines:
            for line3 in self.ax_SNR.lines:
                if self.axis_X_Count > self.ax_SNR.get_xlim()[1]:
                    self.ax_SNR.set_xlim(0, self.axis_X_Count+10)
                val_snr =  obj.scan_data[-1].snr
                line3.set_xdata(list(line3.get_xdata()) + [self.axis_X_Count])
                line3.set_ydata(list(line3.get_ydata()) + [val_snr])
                #self.ax_SNR.set_xlabel(f"SNR Sample: {val_snr:.3f}")
        else:
            self.ax_SNR.plot(self.axis_X_Count, obj.scan_data[-1].snr)

    def update_yk_ber(self, ber):

        if self.ax_BER.lines:
            for line4 in self.ax_BER.lines:
                if self.axis_X_Count  > self.ax_BER.get_xlim()[1]:
                    self.ax_BER.set_xlim(0, self.axis_X_Count+10)
                line4.set_xdata(list(line4.get_xdata()) + [self.axis_X_Count])
                line4.set_ydata(list(line4.get_ydata()) + [math.log10(ber)])
                #self.ax_BER.set_xlabel(f"BER Sample: {ber:.3E}")
        else:
            self.ax_BER.plot(self.axis_X_Count, math.log10(ber), color='violet')


#------------------------------------------
class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, ykobj=None):
        super().__init__(ykobj.fig)
        self.setParent(parent)
        self.ykobj = ykobj

        # Setup a timer to trigger the redraw by calling update_plot.
        self.timer = QtCore.QTimer()
        self.timer.setInterval(5000)
        self.timer.timeout.connect(self.update_plot)
        self.timer.start()

    def update_plot(self):
        self.flush_events()
        self.ykobj.yk_link_updates()
        self.draw_idle()


#------------------------------------------
class MyWidget(QtWidgets.QMainWindow):
    def __init__(self, n_links):
        super().__init__()
        self.setWindowTitle('BizLink HPC Cable Test')

        self.canvases = []
        self.grid_row = 0
        self.grid_col = 0
        self.n_links  = n_links
        if   n_links > 8:  self.layout_grid_rows = 2; self.layout_grid_cols = 8;  self.setGeometry(0, 0, PLOT_F_RESOL_X, PLOT_F_RESOL_Y)
        elif n_links > 1:  self.layout_grid_rows = 2; self.layout_grid_cols = 4;  self.setGeometry(0, 0, PLOT_F_RESOL_X, PLOT_F_RESOL_Y)
        else:              self.layout_grid_rows = 1; self.layout_grid_cols = 1;  self.resize(PLOT_1_RESOL_X, PLOT_1_RESOL_Y)

        # Create a central widget
        central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(central_widget)

        # Create a vertical layout for the central widget
        self.layout_main = QtWidgets.QVBoxLayout(central_widget)

        # Create a horizontal layout for the toobar
        self.layout_TBar = QtWidgets.QHBoxLayout()
        self.layout_main.addLayout(self.layout_TBar)

        # Create a grid layout for the canvases
        self.layout_grid = QtWidgets.QGridLayout()
        self.layout_main.addLayout(self.layout_grid)

        # Create iBERT multiple channels table 
        self.createTable() 
        self.layout_main.addWidget(self.tableWidget)

    def closeEvent(self, event):
        print("Close Widget & YK-Scan")
        for c in self.canvases:
            c.ykobj.YK.stop() # Stops the YK scan from running.
        event.accept()  # Close the widget

    def show_figures(self): 
        for c in self.canvases:
            #c.draw()
            c.ykobj.yk_link_updates()
            c.ykobj.YK.start()
        self.show()

    def createTable(self): 
        self.tableWidget = QtWidgets.QTableWidget(self.n_links, 10) 

        # Table will fit the screen horizontally 
        self.tableWidget.setHorizontalHeaderLabels( ("Samples", "TX", "RX", "Status", "Bits", "Errors", "BER", "SNR", "NA", "NA") )
        self.tableWidget.horizontalHeader().setStretchLastSection(True) 
        self.tableWidget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

    def create_YKScan_figure(self, gt_group, gt_chan):
        ykobj  = MyYKScan(gt_group, gt_chan)
        canvas = MplCanvas(self, ykobj)
        self.layout_grid.addWidget(canvas, self.grid_row, self.grid_col)
        self.canvases.append(canvas)
        canvas.draw()

        #self.ui2(self.ykobj.fig)
        #ykobj.YK.start()

        self.grid_col += 1
        if  self.grid_col >= self.layout_grid_cols:
            self.grid_col = 0
            self.grid_row += 1

    def ui(self, fig):
        self.canvas = FigureCanvas(fig)

        self.graphicview = QtWidgets.QGraphicsView(self)
        self.graphicview.setGeometry(0, 0, PLOT_1_RESOL_X, PLOT_1_RESOL_Y)

        self.graphicscene = QtWidgets.QGraphicsScene()
        self.graphicscene.setSceneRect(0, 0, PLOT_1_RESOL_X - 20, PLOT_1_RESOL_Y - 20)
        self.graphicscene.addWidget(self.canvas)

        self.graphicview.setScene(self.graphicscene)

    def ui2(self, fig):
        self.canvas = FigureCanvas(fig)

        # Create toolbar, passing canvas as first parament, parent (self, the MainWindow) as second.
        toolbar = NavigationToolbar(self.canvas, self)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(toolbar)
        layout.addWidget(self.canvas)

        # Create a placeholder widget to hold our toolbar and canvas.
        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)


#------------------------------------------------------------------------------------------
def create_links_common(RXs, TXs):
    global myLinks

    print(f"Links_TXs: {TXs}")
    print(f"Links_RXs: {RXs}")
    myLinks = create_links(txs=TXs, rxs=RXs)

    dbg_print = True
    for link in myLinks:
        link.gt_name = re.findall(".*(Quad_[0-9]*).*", str(link.rx))[0]
        link.channel = int(re.findall(".*CH_([0-9]*).*", str(link.rx))[0])
        link.gt_grp  = ibert_gtm.gt_groups.filter_by(name=link.gt_name)[0]
        print(f"\n----- {link.name} :: RX={link.rx} TX={link.tx}  GT={link.gt_name} CH={link.channel} -------")
        _, tx_pattern_report = link.tx.property.report(link.tx.property_for_alias[PATTERN]).popitem()
        _, rx_pattern_report = link.rx.property.report(link.rx.property_for_alias[PATTERN]).popitem()
        _, rx_loopback_report = link.tx.property.report(
            link.rx.property_for_alias[RX_LOOPBACK]
        ).popitem()

        if dbg_print:
            print(f"--> Valid values for TX pattern - {tx_pattern_report['Valid values']}")
            print(f"--> Valid values for RX pattern - {rx_pattern_report['Valid values']}")
            print(f"--> Valid values for RX loopback - {rx_loopback_report['Valid values']}\n")
            print(f"==> link.RX: {link.rx} / {link.rx.parent} RX_NAME={link.rx.name} GT_NAME={link.rx.parent.name} GT_alias={link.rx.parent.aliases} ")
            print(f"==> link.TX: {link.tx} / {link.tx.parent} TX_NAME={link.tx.name} GT_NAME={link.tx.parent.name} GT_alias={link.tx.parent.aliases} ")
            link.generate_report()
            dbg_print = False

        props = {link.tx.property_for_alias[PATTERN]: "PRBS 31"}
        link.tx.property.set(**props)
        link.tx.property.commit(list(props.keys()))

        props = {
            link.rx.property_for_alias[PATTERN]: "PRBS 31",
            link.rx.property_for_alias[RX_LOOPBACK]: "Near-End PMA",
        }
        link.rx.property.set(**props)
        link.rx.property.commit(list(props.keys()))
        print(f"\n--> Set both patterns to 'PRBS 31' & loopback to 'Near-End PMA' for {link}")

        assert link.rx.pll.locked and link.tx.pll.locked
        print(f"--> RX and TX PLLs are locked for {link}. Checking for link lock...")
        #assert link.status != "No link"
        print(f"--> {link} Link Status: '{link.status}'")

        #print(f"--> {link} properties:  BER={link.ber}  Count={link.bit_count}")

#------------------------------------------
"""
    Self-looped onnection scheme (TCL_scripts/vpk120_ibert_ChMap_56G.tcl / 112G):
            VPK120 QDD-1 cage <--------+
                                       | QSFP-DD cable
            VPK120 QDD-2 cage <--------+
"""
def create_links_selfLooped():
    global q205, q204, q203, q202
    pass


#------------------------------------------
"""
    Cross-connected connection scheme (TCL_scripts/vpk120_ibert_ChMap2_56G.tcl / 112G):
    
            VPK120 (S/N 111)                             VPK120 (S/N 112)
            QDD-1 cage <-------------------------------> cage QDD-1
                            2x QSFP-DD 400G cables
            QDD-2 cage <-------------------------------> cage QDD-2
"""
def create_links_crossConnected():
    global q202, q203, q204, q205

    RXs = list(); TXs = list();
    for q in (q202, q203):
        for ch in range(4):
            RXs.append(q.gts[ch].rx)
            TXs.append(q.gts[ch].tx)

    for q, ch in ( (q204,0), (q204,2), (q205,0), (q205,2), (q204,1), (q204,3), (q205,1), (q205,3) ):
        RXs.append(q.gts[ch].rx)
        TXs.append(q.gts[ch].tx)

    create_links_common(RXs, TXs)


#------------------------------------------
all_links = []
if CREATE_LGROUP:
    q205 = one(ibert_gtm.gt_groups.filter_by(name="Quad_205"))
    q204 = one(ibert_gtm.gt_groups.filter_by(name="Quad_204"))
    q203 = one(ibert_gtm.gt_groups.filter_by(name="Quad_203"))
    q202 = one(ibert_gtm.gt_groups.filter_by(name="Quad_202"))

    create_links_crossConnected()

    all_lnkgrps = get_all_link_groups()
    all_links   = get_all_links()
    print(f"\n--> All Link Groups available - {all_lnkgrps}")
    print(f"\n--> All Links available - {all_links}")


#------------------------------------------------------------------------------------------
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    MainForm = MyWidget(len(all_links))

    # ## 7 - Create YK Scan
    # This step initializes the YK scan, setting its update method to the method we defined in the last step. 
    if CREATE_LGROUP:
        for link in myLinks:
            MainForm.create_YKScan_figure(link.gt_grp, link.channel)
    else:
        gt_group = ibert_gtm.gt_groups.filter_by(name=QUAD_NAME)[0]
        print(f"--> GT Group channels - {gt_group.gts}")
        MainForm.create_YKScan_figure(gt_group, QUAD_CHAN)

    MainForm.show_figures()

    sys.exit(app.exec_())

#------------------------------------------------------------------------------------------
