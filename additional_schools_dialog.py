from PyQt5.QtWidgets import QDialog, QFileDialog
from PyQt5.QtCore import QVariant
from qgis.core import QgsProject, QgsVectorLayer, QgsField, QgsFeature, QgsPalLayerSettings, QgsTextFormat, QgsVectorLayerSimpleLabeling
from qgis import processing
import psycopg2
from psycopg2 import sql
import csv
import os
from .additional_schools_dialog_ui import Ui_additionalSchoolsDialog

class AdditionalSchoolsDialog(QDialog, Ui_additionalSchoolsDialog):
    def __init__(self, parent=None):
        """Initialize the QDialog and set up the UI."""
        super().__init__(parent)
        self.setupUi(self)

        # Populate combo boxes with available layers
        self.populate_layer_comboboxes()

        # Connect the city layer combo box to update population field combo box
        self.comboBox_cityLayer.currentIndexChanged.connect(self.populate_population_fields)

        # Connect the execute button to calculate the required schools
        self.button_execute.clicked.connect(self.calculate_required_schools)

    def populate_layer_comboboxes(self):
        """Populate the combo boxes with available layers."""
        try:
            connection = self.connect_to_db()
            cursor = connection.cursor()
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            layer_names = [row[0] for row in cursor.fetchall()]

            # Clear existing items in the combo boxes
            self.comboBox_cityLayer.clear()
            self.comboBox_schoolsLayer.clear()

            # Add placeholder text to combo boxes
            self.comboBox_cityLayer.addItem("Select a city layer")
            self.comboBox_schoolsLayer.addItem("Select schools layer")

            # Add available layer names to each combo box
            self.comboBox_cityLayer.addItems(layer_names)
            self.comboBox_schoolsLayer.addItems(layer_names)

            cursor.close()
            connection.close()
        except (Exception, psycopg2.DatabaseError) as error:
            self.show_error(f"Error connecting to the database: {error}")

    def populate_population_fields(self):
        """Populate the population fields combo box based on the selected city layer."""
        try:
            self.comboBox_populationField.clear()
            self.comboBox_populationField.addItem("Select a population field")

            city_layer_name = self.comboBox_cityLayer.currentText()
            print(f"Selected City Layer: {city_layer_name}")  # Debug statement

            if city_layer_name != "Select a city layer":
                connection = self.connect_to_db()
                cursor = connection.cursor()
                cursor.execute(sql.SQL("SELECT column_name FROM information_schema.columns WHERE table_name = %s"), [city_layer_name])
                field_names = [row[0] for row in cursor.fetchall()]
                print(f"Available Fields: {field_names}")  # Debug statement
                self.comboBox_populationField.addItems(field_names)

                cursor.close()
                connection.close()
        except (Exception, psycopg2.DatabaseError) as error:
            self.show_error(f"Error retrieving population fields: {error}")

    