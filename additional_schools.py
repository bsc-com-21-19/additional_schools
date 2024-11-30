from qgis.core import QgsProject, QgsVectorLayer, QgsField, QgsExpression
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QVariant

class AdditionalSchools:
    def __init__(self, iface):
        """Constructor."""
        self.iface = iface
        self.dialog = AdditionalSchoolsDialog()  # Initialize the dialog
        self.dialog.button_execute.clicked.connect(self.run)  # Connect the button to the run method
        self.action = None

    def classFactory(self, iface):
        """This method is used to initialize the plugin."""
        return AdditionalSchools(iface)

    def initGui(self):
        """Initialize the plugin's GUI (e.g., toolbar, menu)."""
        self.action = QAction("Additional Schools", self.iface.mainWindow())
        self.action.triggered.connect(self.run)  # Connect to the run method

        # Add the action to the QGIS toolbar
        self.iface.addToolBarIcon(self.action)

    def unload(self):
        """Clean up the plugin (e.g., remove toolbar actions)."""
        if self.action:
            self.iface.removeToolBarIcon(self.action)

    def run(self):
        """Start the plugin's functionality."""
        # Get the user inputs from the dialog
        city_layer_name = self.dialog.comboBox_cityLayer.currentText()
        area_layer_name = self.dialog.comboBox_areaLayer.currentText()
        eas_layer_name = self.dialog.comboBox_easLayer.currentText()
        schools_layer_name = self.dialog.comboBox_schoolsLayer.currentText()
        population_field = self.dialog.comboBox_populationField.currentText()
        people_per_school = self.dialog.spinBox_peoplePerSchool.value()

        # Validate the input
        if not city_layer_name or not area_layer_name or not eas_layer_name or not schools_layer_name:
            QMessageBox.warning(self.iface.mainWindow(), "Input Error", "Please fill in all the fields.")
            return

        # Fetch the selected layers by name
        city_layer = self._get_layer_by_name(city_layer_name)
        area_layer = self._get_layer_by_name(area_layer_name)
        eas_layer = self._get_layer_by_name(eas_layer_name)
        schools_layer = self._get_layer_by_name(schools_layer_name)

        if not city_layer or not area_layer or not eas_layer or not schools_layer:
            QMessageBox.warning(self.iface.mainWindow(), "Layer Error", "One or more layers could not be found.")
            return

        # Extract schools within selected city layer
        self._extract_schools_in_lilongwe(city_layer, schools_layer)

        # Join layers to calculate population sum per area
        self._join_city_with_area(city_layer, area_layer, population_field)

        # Count schools in each area
        count_layer = self._count_schools_in_areas(schools_layer, area_layer)

        # Join the count layer with the city, area, and eas layer
        joined_layer = self._join_count_with_population(area_layer, count_layer)

        # Calculate the required schools per area
        self._calculate_required_schools(joined_layer, people_per_school)

        # Calculate schools to be added
        self._calculate_schools_to_be_added(joined_layer)

        # Add label display with the area and required schools
        self._setup_labels_and_display(joined_layer)

        # Create and display map layout
        self._create_map_layout()

    def _get_layer_by_name(self, layer_name):
        """Helper function to get a layer by name."""
        layers = QgsProject.instance().mapLayers().values()
        for layer in layers:
            if layer.name() == layer_name:
                return layer
        return None

    def _extract_schools_in_lilongwe(self, city_layer, schools_layer):
        """Extract schools located in the city."""
        processing.run("qgis:extractbylocation", {
            'INPUT': schools_layer,
            'PREDICATE': [0],  # Intersects predicate
            'INTERSECT': city_layer,
            'OUTPUT': 'memory:extracted_schools'
        })

    def _join_city_with_area(self, city_layer, area_layer, population_field):
        """Join city layer with area layer to calculate population sum."""
        processing.run("qgis:joinbylocation", {
            'INPUT': city_layer,
            'JOIN': area_layer,
            'PREDICATE': [0],  # Intersects predicate
            'SUMMARY_FIELD': population_field,
            'STATISTICS': [2],  # Sum
            'OUTPUT': 'memory:joined_city_area'
        })

    def _count_schools_in_areas(self, schools_layer, area_layer):
        """Count schools in each area using 'Count Points in Polygon'."""
        processing.run("qgis:countpointsinpolygon", {
            'POINTS': schools_layer,
            'POLYGONS': area_layer,
            'OUTPUT': 'memory:count_layer'
        })

    def _join_count_with_population(self, area_layer, count_layer):
        """Join the count layer with population data."""
        processing.run("qgis:joinbylocation", {
            'INPUT': area_layer,
            'JOIN': count_layer,
            'PREDICATE': [0],
            'OUTPUT': 'memory:joined_layer'
        })

    def _calculate_required_schools(self, joined_layer, people_per_school):
        """Calculate the required schools based on population."""
        joined_layer.dataProvider().addAttributes([QgsField('required_schools', QVariant.Double)])
        joined_layer.updateFields()
        
        for feature in joined_layer.getFeatures():
            population = feature['SUM_' + str(population_field)]  # Assuming population is summed and named like 'SUM_Population'
            required_schools = population / people_per_school
            feature.setAttribute('required_schools', required_schools)
            joined_layer.updateFeature(feature)

    def _calculate_schools_to_be_added(self, joined_layer):
        """Calculate how many schools need to be added."""
        joined_layer.dataProvider().addAttributes([QgsField('schools_to_be_added', QVariant.Int)])
        joined_layer.updateFields()
        
        for feature in joined_layer.getFeatures():
            current_schools = feature['NUMPOINTS']  # Number of existing schools
            required_schools = feature['required_schools']
            schools_to_be_added = max(0, required_schools - current_schools)  # Ensure no negative values
            feature.setAttribute('schools_to_be_added', schools_to_be_added)
            joined_layer.updateFeature(feature)

    def _setup_labels_and_display(self, joined_layer):
        """Add labels and display concatenated data."""
        joined_layer.dataProvider().addAttributes([QgsField('display', QVariant.String)])
        joined_layer.updateFields()
        
        for feature in joined_layer.getFeatures():
            area_name = feature['ADM_EN']  # Assuming 'ADM_EN' holds the area name
            schools_to_add = feature['schools_to_be_added']
            display_value = f"{area_name}: {schools_to_add} Schools to Add"
            feature.setAttribute('display', display_value)
            joined_layer.updateFeature(feature)
        
        # Set the label to show the concatenated display value
        joined_layer.setLabelsEnabled(True)
        label_field = QgsExpression("display")
        joined_layer.setLabeling(QgsVectorLayerSimpleLabeling(QgsPalLayerSettings()))
        joined_layer.labeling().fieldName = label_field

    def _create_map_layout(self):
        """Create and display the map layout with the necessary elements."""
        layout = QgsPrintLayout(QgsProject.instance())
        layout.initializeDefaults()

        # Add the map and other elements
        map_item = QgsLayoutItemMap(layout)
        map_item.setRect(20, 20, 200, 200)  # Adjust size and position
        layout.addLayoutItem(map_item)
        
        legend = QgsLayoutItemLegend(layout)
        layout.addLayoutItem(legend)
        
        # Optional: Add North Arrow, Scale Bar, etc.
        north_arrow = QgsLayoutItemMapNorthArrow(layout)
        layout.addLayoutItem(north_arrow)
        
        scale_bar = QgsLayoutItemScaleBar(layout)
        layout.addLayoutItem(scale_bar)

        # Render the layout
        QgsProject.instance().layoutManager().addLayout(layout)
        layout.refresh()
