from qgis.core import (
    QgsProject, QgsVectorLayer, QgsField, QgsFeature,
    QgsProcessingAlgorithm, QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField, QgsProcessingParameterFeatureSink
)
from qgis.PyQt.QtCore import QVariant
from qgis.PyQt.QtWidgets import QAction
from .additional_schools_dialog import AdditionalSchoolsDialog

class AdditionalSchools:
    INPUT_SCHOOLS_LAYER = 'INPUT_SCHOOLS_LAYER'
    INPUT_CITY_LAYER = 'INPUT_CITY_LAYER'
    POPULATION_FIELD = 'POPULATION_FIELD'
    OUTPUT_LAYER = 'OUTPUT_LAYER'
    REQUIRED_SCHOOL_FIELD = 'REQUIRED_SCHOOLS'

    def __init__(self, iface):
        """
        Constructor method that initializes the plugin.
        :param iface: The QGIS interface instance
        """
        self.iface = iface  # Store iface for use in other methods if needed
        self.output_layer = None
        self.dialog = AdditionalSchoolsDialog()

    def name(self):
        return 'additional_schools'

    def displayName(self):
        return 'Calculate Required Schools'

    def initGui(self):
        """
        This method initializes the plugin's GUI elements.
        """
        self.action = QAction('Additional Schools', self.iface.mainWindow())
        self.action.triggered.connect(self.run)

        # Add the action to the QGIS interface (e.g., to the Plugins menu)
        self.iface.addPluginToMenu('&Additional Schools', self.action)
        self.iface.addToolBarIcon(self.action)

    def unload(self):
        """
        This method removes the plugin's GUI elements.
        """
        self.iface.removePluginMenu('&Additional Schools', self.action)
        self.iface.removeToolBarIcon(self.action)

    def run(self):
        """
        This method is called when the plugin's action is triggered.
        """
        # Show the dialog when the plugin is run
        self.dialog.exec_()

    def initAlgorithm(self, config=None):
        """
        Initializes the algorithm parameters.
        """
        self.addParameter(
            QgsProcessingParameterFeatureSource(self.INPUT_SCHOOLS_LAYER, 'Schools Layer', types=[QgsProcessing.TypeVectorPoint])
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(self.INPUT_CITY_LAYER, 'City Layer', types=[QgsProcessing.TypeVectorPolygon])
        )
        self.addParameter(
            QgsProcessingParameterField(self.POPULATION_FIELD, 'Population Field', parentLayerParameterName=self.INPUT_CITY_LAYER)
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(self.OUTPUT_LAYER, 'Output Layer', type=QgsProcessing.TypeVectorPolygon)
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Main processing method where the algorithm logic happens.
        """
        schools_layer = self.parameterAsSource(parameters, self.INPUT_SCHOOLS_LAYER, context)
        city_layer = self.parameterAsSource(parameters, self.INPUT_CITY_LAYER, context)
        population_field = self.parameterAsString(parameters, self.POPULATION_FIELD, context)

        output_layer = self.parameterAsSink(parameters, self.OUTPUT_LAYER, context)

        self._calculate_required_schools(city_layer, schools_layer, population_field)

        return {self.OUTPUT_LAYER: output_layer}

    def _calculate_required_schools(self, city_layer, schools_layer, population_field):
        """
        Calculates the required number of schools for each city area based on population.
        """
        required_schools_field = self.REQUIRED_SCHOOL_FIELD
        school_capacity = 1000  # Define how many people each school serves, e.g., 1000 people per school

        # Start editing the city layer to add the required schools field
        if city_layer.isEditable():
            city_layer.startEditing()
        else:
            city_layer.startEditing()

        # Add the 'required_schools' field if it doesn't already exist
        if required_schools_field not in [field.name() for field in city_layer.fields()]:
            city_layer.dataProvider().addAttributes([QgsField(required_schools_field, QVariant.Int)])
            city_layer.updateFields()

        # Loop through each city polygon and calculate required schools
        for city_feature in city_layer.getFeatures():
            city_id = city_feature.id()
            city_population = city_feature[population_field]
            required_schools = city_population // school_capacity  # Basic calculation of required schools

            # Assign the calculated value to the 'required_schools' field
            city_layer.changeAttributeValue(city_id, city_layer.fields().indexFromName(required_schools_field), required_schools)

        city_layer.commitChanges()

        # Optional: Export the updated layer to the output sink
        self.output_layer = city_layer

# Register your plugin
def classFactory(iface):
    return AdditionalSchools(iface)
