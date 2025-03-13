import sys
import os
import subprocess
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel, QTreeView, QFileSystemModel, QStyledItemDelegate, QHBoxLayout
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize, Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("IMS BOLLARD")
        self.setGeometry(100, 100, 800, 600)

        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        self.add_tabs()

    def add_tabs(self):
        self.tab_widget.addTab(self.create_file_explorer_tab("docs/modules"), "Procedures")
        self.tab_widget.addTab(self.create_file_explorer_tab("docs/forms"), "Forms")
        self.tab_widget.addTab(self.create_tab("Dictionary"), "Dictionary")

    def create_file_explorer_tab(self, directory):
        tab = QWidget()
        layout = QVBoxLayout()
        file_model = QFileSystemModel()
        file_model.setRootPath(directory)
        tree_view = QTreeView()
        tree_view.setModel(file_model)
        tree_view.setRootIndex(file_model.index(directory))
        tree_view.setHeaderHidden(True)  # Скрыть заголовок
        tree_view.setColumnHidden(1, True)  # Скрыть столбец Size
        tree_view.setColumnHidden(2, True)  # Скрыть столбец Type
        tree_view.setColumnHidden(3, True)  # Скрыть столбец Date Modified
        tree_view.setIconSize(QSize(0, 0))  # Убрать иконки
        tree_view.doubleClicked.connect(self.open_file)  # Обработка двойного нажатия
        tree_view.setItemDelegate(FileNameDelegate(tree_view))  # Убрать расширения
        layout.addWidget(tree_view)
        tab.setLayout(layout)
        return tab

    def open_file(self, index):
        file_path = self.sender().model().filePath(index)
        if os.path.isfile(file_path):
            if sys.platform == "win32":
                os.startfile(file_path)
            elif sys.platform == "darwin":
                subprocess.call(["open", file_path])
            else:
                subprocess.call(["xdg-open", file_path])

    def create_tab(self, name):
        tab = QWidget()
        layout = QVBoxLayout()
        label = QLabel(f"This is the {name} tab")
        layout.addWidget(label)
        tab.setLayout(layout)
        return tab

class FileNameDelegate(QStyledItemDelegate):
    def displayText(self, value, locale):
        parts = value.split('_', 2)
        if len(parts) > 2:
            return f"{parts[0]}_{parts[1]}_", parts[2]
        return value, ""

    def paint(self, painter, option, index):
        value, number = self.displayText(index.data(), None)
        painter.save()
        painter.drawText(option.rect, Qt.AlignLeft, value)
        painter.drawText(option.rect, Qt.AlignRight, number)
        painter.restore()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
