from PySide6 import QtWidgets

# TODO: créer une interface

class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OverBlog vers WordPress")
        self.setup_ui()

    def setup_ui(self):
        self.create_widgets()
        self.create_layouts()
        self.modify_widgets()
        self.setup_connections()

    def create_widgets(self):
        self.lbl_file = QtWidgets.QLabel("Fichier d'entrée :")
        self.lw_file = QtWidgets.QLineEdit()
        self.btn_browse_file = QtWidgets.QPushButton("Parcourir...")
        self.lbl_folder = QtWidgets.QLabel("Dossier de sortie :")
        self.lw_folder = QtWidgets.QLineEdit()
        self.btn_browse_folder = QtWidgets.QPushButton("Parcourir...")
        self.lbl_id = QtWidgets.QLabel("Dernière ID WordPress :")
        self.lw_id = QtWidgets.QSpinBox()
        self.btn_convert = QtWidgets.QPushButton("Lancer la conversion")

    def create_layouts(self):
        self.main_layout = QtWidgets.QGridLayout(self)
        self.main_layout.addWidget(self.lbl_file, 0, 0, 1, 1)
        self.main_layout.addWidget(self.lw_file, 0, 1, 1, 1)
        self.main_layout.addWidget(self.btn_browse_file, 0, 2, 1, 1)
        self.main_layout.addWidget(self.lbl_folder, 1, 0, 1, 1)
        self.main_layout.addWidget(self.lw_folder, 1, 1, 1, 1)
        self.main_layout.addWidget(self.btn_browse_folder, 1, 2, 1, 1)
        self.main_layout.addWidget(self.lbl_id, 2, 0, 1, 1)
        self.main_layout.addWidget(self.lw_id, 2, 1, 1, 2)
        self.main_layout.addWidget(self.btn_convert, 3, 0, 1, 3)

    def modify_widgets(self):
        pass

    def setup_connections(self):
        self.btn_browse_file.clicked.connect(self.select_file)
        self.btn_browse_folder.clicked.connect(self.select_file)
        self.btn_convert.clicked.connect(self.convert_file)

    def select_file(self):
        print("select file")

    def convert_file(self):
        print("convert file")