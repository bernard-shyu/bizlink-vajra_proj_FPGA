import sys
import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
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

        # Create a single figure with subplots
        fig, axs = plt.subplots(2, 1, figsize=(8, 6))
        axs[0].set_title("Scatter Plot of Random Data Slices")
        axs[0].set_xlabel("Index")
        axs[0].set_ylabel("Value")
        axs[1].set_title("Histogram of Random Data")
        axs[1].set_xlabel("Value")
        axs[1].set_ylabel("Frequency")

        # Scatter plot
        for slice_data in data_slices:
            axs[0].scatter(np.arange(100), slice_data, s=5, alpha=0.5, c='b')

        # Histogram plot
        all_data = np.concatenate(data_slices)
        axs[1].hist(all_data, bins=50, color='g', alpha=0.7)

        # Create FigureCanvasQTAgg widget
        canvas = FigureCanvas(fig)
        layout = QVBoxLayout()
        layout.addWidget(canvas)

        central_widget = QWidget(self)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RandomDataApp()
    window.show()
    sys.exit(app.exec_())

