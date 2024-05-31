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
        self.timer.start(5000)  # Update data every 5 seconds
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

        now = datetime.datetime.now() 
        print(f"\n\n{now} {len(self.data_slices)}\n")
        print(self.data_slices[0:n_slices:20])
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
        """
        self.scatter_plot = self.axs[0].scatter([], [], s=5, alpha=0.5, c='b')
        self.hist_plot = self.axs[1].hist([], bins=50, color='g', alpha=0.7, range=(0, 100))
        """
        self.scatter_plot = self.axs[0].scatter([], [], c='b')
        self.hist_plot = self.axs[1].hist([], bins=50, color='g', range=(0, 100))

        # Create FigureCanvasQTAgg widget
        self.canvas = FigureCanvas(self.fig)
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)

        central_widget = QWidget(self)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def update_plots(self):
        """
        # Update scatter plot
        self.scatter_plot.set_offsets(np.column_stack((np.arange(1), self.data_source.data_slices)))
        """
        self.axs[0].cla()
        #self.scatter_plot.set_offsets(np.column_stack((range(len(self.data_source.data_slices)), list(self.data_source.data_slices))))
        self.axs[0].scatter(range(len(self.data_source.data_slices)), list(self.data_source.data_slices), c='b')  # Use single point for scatter

        """
        # Update histogram
        if self.data_source.data_slices:
            all_data = np.concatenate(self.data_source.data_slices)
            self.hist_plot, _ = self.axs[1].hist(all_data, bins=50, color='g', alpha=0.7, range=(0, 100))
        """
        self.axs[1].cla()
        self.hist_plot = self.axs[1].hist(list(self.data_source.data_slices), bins=50, color='g', alpha=0.7, range=(0, 100))

        self.canvas.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RandomDataApp()
    window.show()
    sys.exit(app.exec_())

