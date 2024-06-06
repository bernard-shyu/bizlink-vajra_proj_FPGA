import sys
import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import datetime

class RandomDataSource:
    def __init__(self):
        self.data_slices = []
        self.timer = QTimer()
        self.timer.timeout.connect(self.generate_data)
        self.timer.start(5000)  # Update data every 5 seconds
        np.random.seed(42)
        self.generate_data()

    def generate_data(self):
        n_slices = 2000
        n_peaks = 4
        peak_positions = [20, 40, 60, 80]
        std_dev = 5
        self.data_slices.clear()

        for _ in range(n_slices):
            peak_pos = peak_positions[np.random.randint(4)]  # Randomly select a peak position
            slice_data = np.random.normal(loc=peak_pos, scale=std_dev)
            self.data_slices.append(slice_data)
        now = datetime.datetime.now() 
        print(f"\n\n{now} {len(self.data_slices)}\n")
        print(self.data_slices[0:n_slices:20])
        #canvas.draw_idle()

class RandomDataApp(QMainWindow):
    def __init__(self):
        #global canvas
        super().__init__()
        self.setWindowTitle("Random Data Visualization")
        self.setGeometry(100, 100, 800, 600)

        # Create random data source
        self.data_source = RandomDataSource()

        # Create a single figure with subplots
        fig, axs = plt.subplots(2, 1, figsize=(8, 6))
        axs[0].set_title("Scatter Plot of Random Data Slices")
        axs[0].set_xlabel("Index")
        axs[0].set_ylabel("Value")
        axs[1].set_title("Histogram of Random Data")
        axs[1].set_xlabel("Value")
        axs[1].set_ylabel("Frequency")

        """
        # Scatter plot
        for slice_data in self.data_source.data_slices:
            axs[0].scatter(np.arange(100), slice_data, s=5, alpha=0.5, c='b')
        """
        axs[0].scatter(range(len(self.data_source.data_slices)), list(self.data_source.data_slices), c='b')  # Use single point for scatter

        """
        # Histogram plot
        if self.data_source.data_slices:
            all_data = np.concatenate(self.data_source.data_slices)
            axs[1].hist(all_data, bins=50, color='g', alpha=0.7, range=(0, 100))  # Corrected data range
        """
        axs[1].hist(list(self.data_source.data_slices), bins=50, color='g', range=(0, 100))  # Corrected data range

        # Calculate mean and standard deviation
        means = [np.mean(slice_data) for slice_data in self.data_source.data_slices]
        stds = [np.std(slice_data) for slice_data in self.data_source.data_slices]

        # Create QLabel widgets
        """
        self.label_means = QLabel(self)
        self.label_means.setText(f"Means: {', '.join(map(str, means))}")
        self.label_stds = QLabel(self)
        self.label_stds.setText(f"Standard Deviations: {', '.join(map(str, stds))}")
        """

        # Set up layout
        central_widget = QWidget(self)
        layout = QVBoxLayout()
        layout.addWidget(FigureCanvas(fig))
        """
        layout.addWidget(self.label_means)
        layout.addWidget(self.label_stds)
        """
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        #canvas = FigureCanvas(fig)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RandomDataApp()
    window.show()
    sys.exit(app.exec_())

"""
Figure is shown and scatter & hist are plotted.
But data can't be live-updated.
"""

