import sys

from PySide6 import QtWidgets

from package.main_window import MainWindow

app = QtWidgets.QApplication(sys.argv)
main_window = MainWindow()
main_window.resize(550, 400)
main_window.show()
sys.exit(app.exec())