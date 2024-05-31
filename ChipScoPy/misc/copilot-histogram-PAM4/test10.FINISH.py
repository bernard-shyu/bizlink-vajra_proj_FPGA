"""
For this code, can you add the code with statistical analysis on the list of self.data_slices?
From this list data, analyze what are the 4 normal distribution mean values? And what's the 4 corresponding standard deviation values are?
For these 4 values of mean, and 4 values of standard deviation, update their value in QLabel within update_plots() method.
"""

import sys
import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtCore import QTimer, QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import datetime

class RandomDataSource(QThread):
    data_updated = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.data_slices = []
        self.timer = QTimer()
        self.timer.timeout.connect(self.generate_data)
        self.timer.start(20000)  # Update data every 20 seconds
        np.random.seed(42)
        #self.generate_data()

    def generate_data(self):
        #np.random.seed(42)
        n_slices = 2000
        n_peaks = 4
        #peak_positions = np.array([20, 40, 60, 80]) + 8*(np.random.rand() - 0.5)     #  Adding randomness to PEAK position by +3/-3
        peak_positions = [20, 40, 60, 80]
        for i in range(4): peak_positions[i] +=  8*(np.random.rand() - 0.5)           #  Adding randomness to PEAK position by +3/-3
        std_dev = 1.5
        self.data_slices.clear()

        for _ in range(n_slices):
            peak_pos = peak_positions[np.random.randint(4)]  # Randomly select a peak position
            slice_data = np.random.normal(loc=peak_pos, scale=std_dev)
            self.data_slices.append(slice_data)

        """
        now = datetime.datetime.now() 
        print(f"\n\n{now} {len(self.data_slices)}\n")
        print(self.data_slices[0:n_slices:20])
        """
        self.data_updated.emit()  # Emit signal when data is updated

class RandomDataApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Random Data Visualization")
        self.setGeometry(100, 100, 800, 600)

        # Create random data source
        self.data_source = RandomDataSource()
        self.data_source.data_updated.connect(self.update_plots)  # Connect signal to update_plots method

        # Create a single figure with subplots
        self.fig, self.axs = plt.subplots(2, 1, figsize=(8, 6))
        self.axs[0].set_title("Scatter Plot of Random Data Slices")
        self.axs[0].set_xlabel("Index")
        self.axs[0].set_ylabel("Value")
        self.axs[1].set_title("Histogram of Random Data")
        self.axs[1].set_xlabel("Value")
        self.axs[1].set_ylabel("Frequency")

        # Initialize plots (empty data)
        self.scatter_plot = self.axs[0].scatter([], [], c='b')
        self.hist_plot = self.axs[1].hist([], bins=100, color='g', range=(0, 100))

        # Create FigureCanvasQTAgg widget
        self.canvas = FigureCanvas(self.fig)
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)

        # Set up layout
        central_widget    = QWidget(self)
        self.label_peaks  = QLabel(self);  layout.addWidget(self.label_peaks)
        self.label_valeys = QLabel(self);  layout.addWidget(self.label_valeys)
        self.label_stds   = QLabel(self);  layout.addWidget(self.label_stds)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Update plots initially
        #self.update_plots()
        self.data_source.generate_data()

    def update_plots(self):
        """
        # Update scatter plot
        self.scatter_plot.set_offsets(np.column_stack((np.arange(1), self.data_source.data_slices)))
        """
        self.axs[0].cla()
        self.axs[0].scatter(range(len(self.data_source.data_slices)), list(self.data_source.data_slices), c='b')  # Use single point for scatter

        """
        # Update histogram
        if self.data_source.data_slices:
            all_data = np.concatenate(self.data_source.data_slices)
            self.hist_plot, _ = self.axs[1].hist(all_data, bins=100, color='g', alpha=0.7, range=(0, 100))
        """
        self.axs[1].cla()
        hist, edges, _ = self.axs[1].hist(list(self.data_source.data_slices), bins=100, color='g', alpha=0.7, range=(0, 100))
        print(f"\n\n=============================================== {len(hist)} {len(edges)} =============================================== ")
        print(hist)
        print(edges)
        if len(self.data_source.data_slices) == 0:
            return

        """
        h_list = [  0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   1, 2,  10,  31,  83, 127, 117,  80,  36,  19,   3,   0,   0,   0,   0,  0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   3,  17,  56,  97, 125, 104,  65,  30,   5,   2,   0,   0,   0,   0,   0,   0,   0,  1,   2,  13,  53,  86, 107, 137,  64,  24,  13,   0,   0,   0,   0,  0,   0,   0,   0,   0,   2,   0,   9,  45,  78, 126, 119,  78,  26,  4,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,  0,   0]
        hist = np.array(h_list)

        hist[:50].max()  # 127
        hist[:50].argmax() # 18
        hist[18]   # 127

        hist[50:].max()  # 137
        hist[50:].argmax() # 12
        hist[62]   # 137
        """

        MIN_WIDTH = 3
        #  ----------- 00 -------------------------------- 50 -------------------------------- 100 ---------
        #  peaks:              Peak0           Peak1                  Peak2           Peak3
        #  valeys:                    Valey0             Valey1               Valey2
        #---------------------------------------------------------------------------------------------------
        # find the highest peak in [0:50], it can be Peak0 or Peak1
        p  = hist[0:50].max()
        i  = hist[0:50].argmax()
        # find the 2nd peak in [0:50] to the LEFT or RIGHT side
        L = hist[0:i-MIN_WIDTH].max()
        R = hist[i+MIN_WIDTH:50].max()
        if L < R:
            # 2nd peak is RIGHT side
            Peak0 = p;  i_P0 = i
            Peak1 = R;  i_P1 = hist[i+MIN_WIDTH:50].argmax() + i + MIN_WIDTH
        else:
            # 2nd peak is LEFT  side
            Peak1 = p;  i_P1 = i
            Peak0 = L;  i_P0 = hist[0:i-MIN_WIDTH].argmax()

        #---------------------------------------------------------------------------------------------------
        # find the highest peak in [50:100], it can be Peak2 or Peak3
        P  = hist[50:100].max()
        i  = hist[50:100].argmax() + 50
        # find the 2nd peak in [50:100] to the LEFT or RIGHT side
        L = hist[50:i-MIN_WIDTH].max()
        R = hist[i+MIN_WIDTH:100].max()
        if L < R:
            # 2nd peak is RIGHT side
            Peak2 = p;  i_P2 = i
            Peak3 = R;  i_P3 = hist[i+MIN_WIDTH:100].argmax() + i + MIN_WIDTH
        else:
            # 2nd peak is LEFT  side
            Peak3 = p;  i_P3 = i
            Peak2 = L;  i_P2 = hist[50:i-MIN_WIDTH].argmax() + 50
        txt_peaks = f"Peaks:   {i_P0}={Peak0:<6}    {i_P1}={Peak1:<6}    {i_P2}={Peak2:<6}    {i_P3}={Peak3:<6}"
        print(txt_peaks)
        self.label_peaks.setText(txt_peaks)

        #---------------------------------------------------------------------------------------------------
        # find the valeys
        Valey0 = hist[i_P0:i_P1].min();   i_V0 = hist[i_P0:i_P1].argmin() + i_P0
        Valey1 = hist[i_P1:i_P2].min();   i_V1 = hist[i_P1:i_P2].argmin() + i_P1
        Valey2 = hist[i_P2:i_P3].min();   i_V2 = hist[i_P2:i_P3].argmin() + i_P2
        txt_valeys = f"Valeys:         {i_V0}={Valey0:<6}    {i_V1}={Valey1:<6}    {i_V2}={Valey2:<6} "
        print(txt_valeys)
        self.label_valeys.setText(txt_valeys)

        # find the standard-deviation
        stdvar0 = np.std(hist[0:i_V0])
        stdvar1 = np.std(hist[i_V0:i_V1])
        stdvar2 = np.std(hist[i_V1:i_V2])
        stdvar3 = np.std(hist[i_V2:100])

        txt_stds = f"std:   {stdvar0:9.3f}    {stdvar1:9.3f}    {stdvar2:9.3f}    {stdvar3:9.3f} "
        print(txt_stds)
        self.label_stds.setText(txt_stds)

        self.canvas.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RandomDataApp()
    window.show()
    sys.exit(app.exec_())

