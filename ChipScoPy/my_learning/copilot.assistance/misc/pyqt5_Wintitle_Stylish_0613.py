import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QMainWindow
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt

class CustomTitleBar(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(100, 50, 800, 600)  # Set your desired window size
        self.setWindowIcon(QIcon("icon.png"))  # Set an icon for the window

        # Create a custom title bar widget
        self.titleBar = QWidget(self)
        self.titleBar.setGeometry(0, 0, 800, 60)  # Adjust dimensions as needed
        self.titleBar.setStyleSheet("background-color: rgba(255, 255, 255, 120);")

        # Add title text with different colors and font sizes
        title_label = QLabel("My", self.titleBar)
        title_label.move(10, 10)
        title_label.setStyleSheet("color: red; font-size: 20px;")

        title_label2 = QLabel("Stylish", self.titleBar)
        title_label2.move(60, 10)
        title_label2.setStyleSheet("color: green; font-size: 24px;")

        title_label3 = QLabel("App", self.titleBar)
        title_label3.move(150, 10)
        title_label3.setStyleSheet("color: blue; font-size: 18px;")

        # Set the window title with multiple styles
        self.setWindowTitle("My " + "<font color='red'>Stylish</font> " + "<font color='green'>App</font>")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    demo = CustomTitleBar()
    demo.show()
    sys.exit(app.exec_())
