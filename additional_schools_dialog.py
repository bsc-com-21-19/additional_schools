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

    def calculate_required_schools(self):
        """Calculate the required number of schools based on the population and people per school."""
        try:
            city_layer_name = self.comboBox_cityLayer.currentText()
            schools_layer_name = self.comboBox_schoolsLayer.currentText()
            
            if city_layer_name == "Select a city layer" or schools_layer_name == "Select schools layer":
                self.show_error("Please select both the city and schools layers.")
                return
            
            connection = self.connect_to_db()
            cursor = connection.cursor()
            
            population_field = self.comboBox_populationField.currentText()
            print(f"Selected Population Field: {population_field}")  # Debug statement

            if population_field == "Select a population field":
                self.show_error("Please select a population field.")
                return
            
            people_per_school = self.spinBox_peoplePerSchool.value()

            cursor.execute(sql.SQL("SELECT adm3_en, {population_field}, ST_Transform(geom, 4326) AS geom FROM {city_layer}").format(
                population_field=sql.Identifier(population_field),
                city_layer=sql.Identifier(city_layer_name)
            ))

            city_features = cursor.fetchall()
            total_population = sum([row[1] for row in city_features])

            results = []

            for feature in city_features:
                area_name = feature[0]
                population = feature[1]
                geom = feature[2]

                required_schools = round(population / people_per_school)
                cursor.execute(sql.SQL("""
                    SELECT COUNT(*) FROM {schools_layer}
                    WHERE ST_Within(ST_Transform(geom, 4326), %s)
                """).format(
                    schools_layer=sql.Identifier(schools_layer_name)
                ), [geom])
                available_schools = cursor.fetchone()[0]
                schools_to_add = max(0, round(required_schools - available_schools))
                label = f"{area_name} = {schools_to_add}"

                results.append([area_name, required_schools, available_schools, schools_to_add])

                cursor.execute("""
                    INSERT INTO results_table (area_name, required_schools, available_schools, schools_to_add, geom)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (area_name) DO UPDATE SET
                    required_schools = EXCLUDED.required_schools,
                    available_schools = EXCLUDED.available_schools,
                    schools_to_add = EXCLUDED.schools_to_add,
                    geom = EXCLUDED.geom
                """, [area_name, required_schools, available_schools, schools_to_add, geom])

            # Ask the user for the save location
            save_path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv)")
            if save_path:
                # Save the results to a CSV file
                with open(save_path, 'w', newline='') as csvfile:
                    fieldnames = ['Area', 'Required Schools', 'Available Schools', 'Schools to Add']
                    writer = csv.writer(csvfile)
                    writer.writerow(fieldnames)
                    writer.writerows(results)
                self.show_info(f"Results have been updated in the database and saved to {save_path}.")
            else:
                self.show_info(f"Results have been updated in the database, but no CSV file was saved.")

            connection.commit()
            cursor.close()
            connection.close()
        except (Exception, psycopg2.DatabaseError) as error:
            self.show_error(f"Error during calculation: {error}")

    def connect_to_db(self):
        """Establish a database connection."""
        return psycopg2.connect(database="additional schools", user="postgres", password="fargo", host="localhost", port="5432")

    def show_error(self, message):
        """Show error message to the user."""
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.critical(self, "Error", message)

    def show_info(self, message):
        """Show informational message to the user."""
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self, "Information", message)
