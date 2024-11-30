from PyQt5.QtWidgets import QDialog
from .additional_schools_dialog_ui import Ui_additionalSchoolsDialog


class AdditionalSchoolsDialog(QDialog, Ui_additionalSchoolsDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.button_execute.clicked.connect(self.on_generate_map)

    def on_generate_map(self):
        city_layer = self.comboBox_cityLayer.currentText()
        eas_layer = self.comboBox_easLayer.currentText()
        schools_layer = self.comboBox_schoolsLayer.currentText()
        population = self.lineEdit_population.text()
        print(f"Generating map with:\nCity Layer: {city_layer}\nEas Layer: {eas_layer}\nSchools Layer: {schools_layer}\nPopulation: {population}")
