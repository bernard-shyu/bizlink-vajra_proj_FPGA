import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QMenu, QAction, QWidget
from PyQt5.QtCore import Qt

class MyTableWidget(QTableWidget):
    def __init__(self):
        super().__init__()
        self.setColumnCount(3)
        self.setRowCount(5)
        self.setHorizontalHeaderLabels(["Column 1", "Column 2", "Column 3"])

        # Populate the table with some data (you can replace this with your own data)
        for row in range(5):
            for col in range(3):
                item = QTableWidgetItem(f"Item {row}-{col}")
                self.setItem(row, col, item)

        # Set up the context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, pos):
        menu = QMenu(self)
        edit_action = QAction("Edit", self)
        delete_action = QAction("Delete", self)

        # Connect actions to their respective slots (you can implement these methods)
        edit_action.triggered.connect(self.edit_item)
        delete_action.triggered.connect(self.delete_item)

        menu.addAction(edit_action)
        menu.addAction(delete_action)
        menu.exec_(self.mapToGlobal(pos))

    def edit_item(self):
        # Implement your edit logic here
        selected_item = self.currentItem()
        if selected_item:
            print(f"Editing item: {selected_item.text()}")

    def delete_item(self):
        # Implement your delete logic here
        selected_item = self.currentItem()
        if selected_item:
            print(f"Deleting item: {selected_item.text()}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = QMainWindow()
    table_widget = MyTableWidget()
    window.setCentralWidget(table_widget)
    window.setGeometry(100, 100, 600, 400)
    window.setWindowTitle("Context Menu Example")
    window.show()
    sys.exit(app.exec_())

