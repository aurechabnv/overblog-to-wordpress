import logging
from functools import cached_property
from pathlib import Path

from PySide6 import QtWidgets, QtCore

from package.api.formatter import ExportFormatter

BASE_BROWSE_DIR = QtCore.QStandardPaths().standardLocations(QtCore.QStandardPaths.StandardLocation.DesktopLocation)[0]


class Worker(QtCore.QObject):
    finished = QtCore.Signal(bool)

    def __init__(self, file_to_convert, output_folder, last_db_id):
        super().__init__()
        self.file_to_convert = file_to_convert
        self.output_folder = output_folder
        self.last_db_id = last_db_id

    def convert_file(self):
        formatter = ExportFormatter(file_path=self.file_to_convert,
                                    output_folder=self.output_folder,
                                    last_wp_id=self.last_db_id)
        success = formatter.convert_to_wp_format()
        self.finished.emit(success)


class Bridge(QtCore.QObject):
    receive_log = QtCore.Signal(str)


class QTextEditLogger(logging.Handler):
    @cached_property
    def bridge(self):
        return Bridge()

    def __init__(self, parent):
        super().__init__()
        self.widget = QtWidgets.QPlainTextEdit(parent)
        self.widget.setReadOnly(True)
        self.bridge.receive_log.connect(self.widget.appendPlainText)

    def emit(self, record):
        msg = self.format(record)
        self.bridge.receive_log.emit(msg)


class MainWindow(QtWidgets.QWidget):
    thread: QtCore.QThread
    worker: Worker
    main_layout: QtWidgets.QGridLayout
    lbl_file: QtWidgets.QLabel
    lbl_folder: QtWidgets.QLabel
    lbl_id: QtWidgets.QLabel
    le_file: QtWidgets.QLineEdit
    le_folder: QtWidgets.QLineEdit
    sb_id: QtWidgets.QSpinBox
    btn_browse_file: QtWidgets.QPushButton
    btn_browse_folder: QtWidgets.QPushButton
    btn_convert: QtWidgets.QPushButton
    te_logger: QTextEditLogger

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
        self.le_file = QtWidgets.QLineEdit()
        self.btn_browse_file = QtWidgets.QPushButton("Parcourir...")
        self.lbl_folder = QtWidgets.QLabel("Dossier de sortie :")
        self.le_folder = QtWidgets.QLineEdit("output")
        self.btn_browse_folder = QtWidgets.QPushButton("Parcourir...")
        self.lbl_id = QtWidgets.QLabel("Dernière ID WordPress :")
        self.sb_id = QtWidgets.QSpinBox()
        self.btn_convert = QtWidgets.QPushButton("Lancer la conversion")
        self.te_logger = QTextEditLogger(self)

    def create_layouts(self):
        self.main_layout = QtWidgets.QGridLayout(self)
        self.main_layout.addWidget(self.lbl_file, 0, 0, 1, 1)
        self.main_layout.addWidget(self.le_file, 0, 1, 1, 1)
        self.main_layout.addWidget(self.btn_browse_file, 0, 2, 1, 1)
        self.main_layout.addWidget(self.lbl_folder, 1, 0, 1, 1)
        self.main_layout.addWidget(self.le_folder, 1, 1, 1, 1)
        self.main_layout.addWidget(self.btn_browse_folder, 1, 2, 1, 1)
        self.main_layout.addWidget(self.lbl_id, 2, 0, 1, 1)
        self.main_layout.addWidget(self.sb_id, 2, 1, 1, 2)
        self.main_layout.addWidget(self.btn_convert, 3, 0, 1, 3)
        self.main_layout.addWidget(self.te_logger.widget, 4, 0, 1, 4)

    def modify_widgets(self):
        self.te_logger.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(self.te_logger)

    def setup_connections(self):
        self.btn_browse_file.clicked.connect(self.select_file)
        self.btn_browse_folder.clicked.connect(self.select_folder)
        self.btn_convert.clicked.connect(self.convert_file)

    def select_file(self):
        file_name = QtWidgets.QFileDialog.getOpenFileName(caption="Fichier d'entrée",
                                                          dir=BASE_BROWSE_DIR,
                                                          filter="*.xml")[0]
        if file_name:
            self.le_file.setText(file_name)

    def select_folder(self):
        file_name = QtWidgets.QFileDialog.getExistingDirectory(caption="Dossier de sortie", dir=BASE_BROWSE_DIR)
        if file_name:
            self.le_folder.setText(file_name)

    def check_validity(self):
        wp_file = self.le_file.text()
        out_folder = self.le_folder.text()
        last_wp_id = self.sb_id.value()

        if not wp_file or not out_folder:
            QtWidgets.QMessageBox.warning(self,
                                          title="Paramètres manquants",
                                          text="Il semble manquer des paramètres. Veuillez re-vérifier.")
            return False

        if not last_wp_id:
            msg_box = QtWidgets.QMessageBox.question(self,
                                                     title="Vérification de l'ID WordPress",
                                                     text=f"Le dernier ID de votre base WordPress est paramétré à :\n{last_wp_id}\n\nÊtes-vous sûr ?")
            if msg_box == QtWidgets.QMessageBox.StandardButton.No:
                return False

        if not Path(wp_file).exists():
            QtWidgets.QMessageBox.warning(self,
                                          title="Fichier introuvable",
                                          text="Le fichier sélectionné est introuvable. Veuillez re-vérifier.")
            return False

        return True

    def enable_fields(self, enable=True):
        self.le_file.setEnabled(enable)
        self.btn_browse_file.setEnabled(enable)
        self.le_folder.setEnabled(enable)
        self.btn_browse_folder.setEnabled(enable)
        self.sb_id.setEnabled(enable)
        self.btn_convert.setEnabled(enable)

    def convert_file(self):
        if not self.check_validity():
            return False

        self.enable_fields(False)
        self.te_logger.widget.clear()

        self.thread = QtCore.QThread(self)
        self.worker = Worker(file_to_convert=self.le_file.text(), output_folder=self.le_folder.text(),
                             last_db_id=self.sb_id.value())
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.convert_file)
        self.worker.finished.connect(self.finished_process)
        self.thread.start()

    def finished_process(self, success):
        self.thread.quit()
        self.enable_fields()
        if success:
            QtWidgets.QMessageBox.information(self,
                                              title="Opération terminée",
                                              text="C'est fini !\nDirection WP All Import pour importer vos fichiers dans l'ordre.")
        else:
            QtWidgets.QMessageBox.critical(self,
                                           title="Erreur",
                                           text="Une erreur est survenue au cours de l'opération.\nVeuillez consulter les logs dans l'interface.")
