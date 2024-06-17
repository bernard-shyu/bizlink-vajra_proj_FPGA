"""
With Python, Pandas, Numpy, matplotlib, pyqt5, can you help me on these 2 example codes?

(1) Random data source whose statistics pattern are 4 peaks of normal distributions, at these positions: 20, 40, 60, 80 respectively. Each normal distribution has standard deviation of 5. Data value range is 0 to 100.
This Random data source is generated every 5 sec, with 2000 values each time, which we will name it as one SLICE of data.
The data will be drawn on figure with 2 axises: (a) scatter-plot of the data slices.  (b) histogram plot of the same data.

(2) For the above data source, please show on separate QLabel with the corresponding statistics values: the mean and standard deviation value for these 4 normal distributions.
"""


import sys
import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

class RandomDataApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Random Data Visualization")
        self.setGeometry(100, 100, 800, 600)

        # Generate random data
        np.random.seed(42)
        n_slices = 2000
        n_peaks = 4
        peak_positions = [20, 40, 60, 80]
        std_dev = 5
        data_slices = []

        for _ in range(n_slices):
            slice_data = np.zeros(100)
            for peak_pos in peak_positions:
                slice_data += np.random.normal(loc=peak_pos, scale=std_dev, size=100)
            data_slices.append(slice_data)

        # Create scatter plot
        self.figure_scatter = plt.figure(figsize=(6, 4))  # Adjust the figure size. You may try with smaller value
        ax_scatter = self.figure_scatter.add_subplot(111)
        for slice_data in data_slices:
            ax_scatter.scatter(np.arange(100), slice_data, s=5, alpha=0.5, c='b')
        ax_scatter.set_title("Scatter Plot of Random Data Slices")
        ax_scatter.set_xlabel("Index")
        ax_scatter.set_ylabel("Value")
        ax_scatter.grid(True)

        # Create histogram plot
        self.figure_hist = plt.figure(figsize=(6, 4))  # Adjust the figure size. You may try with smaller value
        ax_hist = self.figure_hist.add_subplot(111)
        all_data = np.concatenate(data_slices)
        ax_hist.hist(all_data, bins=50, color='g', alpha=0.7)
        ax_hist.set_title("Histogram of Random Data")
        ax_hist.set_xlabel("Value")
        ax_hist.set_ylabel("Frequency")
        ax_hist.grid(True)

        # Calculate mean and standard deviation
        means = [np.mean(slice_data) for slice_data in data_slices]
        stds = [np.std(slice_data) for slice_data in data_slices]

        # Create QLabel widgets
        self.label_means = QLabel(self)
        self.label_means.setText(f"Means: {', '.join(map(str, means))}")
        self.label_stds = QLabel(self)
        self.label_stds.setText(f"Standard Deviations: {', '.join(map(str, stds))}")

        # Set up layout
        central_widget = QWidget(self)
        layout = QVBoxLayout()
        layout.addWidget(FigureCanvas(self.figure_scatter))
        layout.addWidget(FigureCanvas(self.figure_hist))
        layout.addWidget(self.label_means)
        layout.addWidget(self.label_stds)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RandomDataApp()
    window.show()
    sys.exit(app.exec_())

"""
Traceback (most recent call last):
  File "/home/bernard/.local/lib/python3.10/site-packages/matplotlib/backends/backend_qt.py", line 459, in _draw_idle
    self.draw()
  File "/home/bernard/.local/lib/python3.10/site-packages/matplotlib/backends/backend_agg.py", line 383, in draw
    self.renderer = self.get_renderer()
  File "/home/bernard/.local/lib/python3.10/site-packages/matplotlib/backends/backend_agg.py", line 398, in get_renderer
    self.renderer = RendererAgg(w, h, self.figure.dpi)
  File "/home/bernard/.local/lib/python3.10/site-packages/matplotlib/backends/backend_agg.py", line 70, in __init__
    self._renderer = _RendererAgg(int(width), int(height), dpi)
ValueError: Image size of 303545x265 pixels is too large. It must be less than 2^16 in each direction.
Traceback (most recent call last):
  File "/home/bernard/.local/lib/python3.10/site-packages/matplotlib/backends/backend_qt.py", line 459, in _draw_idle
    self.draw()
  File "/home/bernard/.local/lib/python3.10/site-packages/matplotlib/backends/backend_agg.py", line 383, in draw
    self.renderer = self.get_renderer()
  File "/home/bernard/.local/lib/python3.10/site-packages/matplotlib/backends/backend_agg.py", line 398, in get_renderer
    self.renderer = RendererAgg(w, h, self.figure.dpi)
  File "/home/bernard/.local/lib/python3.10/site-packages/matplotlib/backends/backend_agg.py", line 70, in __init__
    self._renderer = _RendererAgg(int(width), int(height), dpi)
    
"""
