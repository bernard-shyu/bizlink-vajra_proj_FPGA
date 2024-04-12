# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.15.1
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# <link rel="preconnect" href="https://fonts.gstatic.com">
# <link href="https://fonts.googleapis.com/css2?family=Fira+Code&display=swap" rel="stylesheet">
#
# ### License
#
# <p style="font-family: 'Fira Code', monospace; font-size: 1.2rem">
# Copyright (C) 2022, Xilinx, Inc.
# Copyright (C) 2022-2023, Advanced Micro Devices, Inc.
# <br><br>
# Licensed under the Apache License, Version 2.0 (the "License");<br>
# you may not use this file except in compliance with the License.<br><br>
# You may obtain a copy of the License at <a href="http://www.apache.org/licenses/LICENSE-2.0"?>http://www.apache.org/licenses/LICENSE-2.0</a><br><br>
# Unless required by applicable law or agreed to in writing, software<br>
# distributed under the License is distributed on an "AS IS" BASIS,<br>
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.<br>
# See the License for the specific language governing permissions and<br>
# limitations under the License.<br>
# </p>
#

# %% [markdown]
# # IBERT yk scan example

# %% [markdown]
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

# %% [markdown]
# ## 1 - Initialization: Imports
#
# After this step,
#
# * Required functions and classes are imported
# * Paths to server(s) and files are set correctly

# %%
import os
from more_itertools import one
import matplotlib.pyplot as plt

from chipscopy import create_session, report_versions, report_hierarchy, get_design_files
from chipscopy.api.ibert import create_yk_scans

#------------------------------------------------------------------------------------------
# BXU is here
#------------------------------------------
"""
source ~/venv/bin/activate
cd ~/SDK_WIP/project/vajra_proj_FPGA/ChipScoPy/my_learning/versal_gtm
export ip="10.20.2.146"; export  CS_SERVER_URL="TCP:$ip:3042" HW_SERVER_URL="TCP:$ip:3121"
export QT_QPA_PLATFORM=wayland

python bxu_GTM_test.py
"""
#------------------------------------------
from PyQt5 import QtWidgets
from PyQt5.QtGui  import *
from PyQt5.QtCore import *
import sys
import time

import numpy as np
import matplotlib

matplotlib.use("Qt5Agg")      # 表示使用 Qt5
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


RESOLUTION_X = 800
RESOLUTION_Y = 600

#------------------------------------------
class MyWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('BizLink HPC Cable Test')
        self.resize(RESOLUTION_X, RESOLUTION_Y)
        self.t = 0
        # self.ui()

    def closeEvent(self, event):
        yk.stop() # Stops the YK scan from running.
        event.accept()  # Close the widget

    def ui(self, fig):
        self.canvas = FigureCanvas(fig)

        self.graphicview = QtWidgets.QGraphicsView(self)
        self.graphicview.setGeometry(0, 0, RESOLUTION_X, RESOLUTION_Y)

        self.graphicscene = QtWidgets.QGraphicsScene()
        self.graphicscene.setSceneRect(0, 0, RESOLUTION_X - 20, RESOLUTION_Y - 20)
        self.graphicscene.addWidget(self.canvas)

        self.graphicview.setScene(self.graphicscene)

#------------------------------------------------------------------------------------------

# %% [markdown]
# ## 2 - Create a session and connect to the hw_server and cs_server
#
# The session is a container that keeps track of devices and debug cores.
# After this step,
# - Session is initialized and connected to server(s)
# - Versions are detected and reported to stdout

# %%
# Specify locations of the running hw_server and cs_server below.
CS_URL = os.getenv("CS_SERVER_URL", "TCP:localhost:3042")
HW_URL = os.getenv("HW_SERVER_URL", "TCP:localhost:3121")

# specify hw and if programming is desired
HW_PLATFORM = os.getenv("HW_PLATFORM", "vpk120")
PROG_DEVICE = os.getenv("PROG_DEVICE", 'True').lower() in ('true', '1', 't')

# The get_design_files() function tries to find the PDI and LTX files. In non-standard
# configurations, you can put the path for PROGRAMMING_FILE and PROBES_FILE below.
design_files = get_design_files(f"{HW_PLATFORM}/production/chipscopy_ced")
PDI_FILE = design_files.programming_file

print(f"PROGRAMMING_FILE: {PDI_FILE}")
print(f"Servers URL: {CS_URL} {HW_URL}   Do_Programming: {PROG_DEVICE}")

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
device = session.devices.filter_by(family="versal").get()

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

print(f"--> Enabled GT Groups - {ibert_gtm.gt_groups}")

gt_group = ibert_gtm.gt_groups.filter_by(name="Quad_204")[0]


# %% [markdown]
# ## 6 - Define YK Scan Update Method
#
# This method will be called each time the yk scan updates, allowing it to update its graphs in real time. 

# %%
# %matplotlib widget

def yk_scan_updates(obj):
    global count, figure, ax_EYE, ax_HIST, ax_SNR
    if ax_EYE.lines:
        for line in ax_EYE.lines:
            line.set_xdata(range(len(obj.scan_data[-1].slicer)))
            line.set_ydata(list(obj.scan_data[-1].slicer))
    else:
        ax_EYE.scatter(range(len(obj.scan_data[-1].slicer)), list(obj.scan_data[-1].slicer), color='blue')
    
    if ax_HIST.lines:
        for line2 in ax_HIST.lines:
            ax_HIST.set_xlim(0, ax_HIST.get_xlim()[1] + len(obj.scan_data[-1].slicer))
            line2.set_xdata(list(line2.get_xdata()) + list(range(len(line2.get_xdata()), len(line2.get_xdata()) + len(obj.scan_data[-1].slicer))))
            line2.set_ydata(list(line2.get_ydata()) + list(obj.scan_data[-1].slicer))
    else:
        ax_HIST.scatter(range(len(obj.scan_data[-1].slicer)), list(obj.scan_data[-1].slicer), color='blue')
        
    if ax_SNR.lines:
        for line3 in ax_SNR.lines:
            if len(obj.scan_data) - 1 > ax_SNR.get_xlim()[1]:
                ax_SNR.set_xlim(0, ax_SNR.get_xlim()[1]+10)
            line3.set_xdata(list(line3.get_xdata()) + [len(obj.scan_data) - 1])
            val_snr =  obj.scan_data[-1].snr
            line3.set_ydata(list(line3.get_ydata()) + [val_snr])
            ax_SNR.set_xlabel(f"SNR Sample: {val_snr:.3f}")
    else:
        ax_SNR.plot(len(obj.scan_data) - 1, obj.scan_data[-1].snr)


    figure.canvas.draw_idle()

# %% [markdown]
# ## 7 - Create YK Scan
#
# This step initializes the YK scan, setting its update method to the method we defined in the last step. 

# %%
yk = create_yk_scans(target_objs=gt_group.gts[0].rx)[0]

yk.updates_callback = yk_scan_updates

# %% [markdown]
# ## 8 - Run YK Scan
#
# Initialize the plots and start the YK Scan to begin updating the plots. 
# YK Scan plot should contain three subplots, these plots should look something like:
# ![yk_scan_example.png](./yk_scan_example.png)
# Note: Depending on the hardware setup and external loopback connection, the plot might look different.

# %%
# %matplotlib widget

#This sets up the subplots necessary for the 
figure, (ax_EYE, ax_HIST, ax_SNR) = plt.subplots(3, constrained_layout = True, num="YK Scan")

ax_EYE.set_xlabel("ES Sample")
ax_EYE.set_ylabel("Amplitude (%)")
ax_EYE.set_xlim(0,2000)
ax_EYE.set_ylim(0,100)
ax_EYE.set_yticks(range(0, 100, 20))
ax_EYE.set_title("Slicer eye")

ax_HIST.set_xlabel("Count")
ax_HIST.set_ylabel("Amplitude (%)")
ax_HIST.set_xlim(0,2000)
ax_HIST.set_ylim(0,100)
ax_HIST.set_yticks(range(0, 100, 20))
ax_HIST.set_title("Histogram")

ax_SNR.set_xlabel("SNR Sample")
ax_SNR.set_ylabel("SNR (dB)")
ax_SNR.set_xlim(0,10)
ax_SNR.set_ylim(-10,50)
ax_SNR.set_title("Signal-to-Noise Ratio")

#------------------------------------------------------------------------------------------
# BXU is here
#------------------------------------------
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    Form = MyWidget()

    Form.ui(figure)
    yk.start()
    Form.show()
    #yk.stop() # Stops the YK scan from running.

    sys.exit(app.exec_())

#------------------------------------------------------------------------------------------


