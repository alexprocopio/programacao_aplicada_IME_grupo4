from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsWkbTypes,
                       QgsPointXY,
                       QgsProcessingMultiStepFeedback,
                       QgsField,
                       QgsProcessingParameterNumber,
                       QgsSpatialIndex,
                       QgsProcessingUtils,
                       QgsProcessingParameterEnum,
                       QgsFeature,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsGeometry,
                       QgsFields,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterRasterLayer,
                       edit,
                       QgsRaster,
                       QgsFeatureRequest, QgsGeometry, QgsPoint,
                       QgsVectorLayer,
                       QgsProject)
import processing
import numpy as np


class Projeto3Solucao(QgsProcessingAlgorithm):
    # Declarando os nossos parâmetros que utilizaremos para a resolução da questão.

    DIA_1 = 'DIA_1'
    DIA_2 = 'DIA_2'
    TRACKER = 'TRACKER'
    RADIUS = 'Raio do buffer'

    OUTPUT = 'OUTPUT'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return Projeto3Solucao()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'projeto 3'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Projeto 3')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr('Example scripts')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Projeto 3'

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        return self.tr("Funciona por favor")

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # Camada de linhas infra dia 1
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.DIA_1,
                self.tr('Camada Dia 1'),
                [QgsProcessing.TypeVectorAnyGeometry]
            )
        )
        # Camada de linhas infra dia 2
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.DIA_2,
                self.tr('Camada Dia 2'),
                [QgsProcessing.TypeVectorAnyGeometry]
            )
        )

        # Camada vetorial tracker
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.TRACKER,
                self.tr('Tracker'),
                [QgsProcessing.TypeVectorPoint]
            )
        )

        # Adicionando o parâmetro de escala
        self.addParameter(
            QgsProcessingParameterNumber(
                self.RADIUS,
                self.tr('Raio do Buffer'),
                type=QgsProcessingParameterNumber.Integer,
                minValue = 0,
                maxValue = 100,
                defaultValue=10
            )
        )

        # Adicionando o parâmetro de saída (OUTPUT)
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Mudanças OUTPUT')
            ))



    def processAlgorithm(self, parameters, context, feedback):
        """
        Aqui será feita o processamento do algoritmo.
        """
        tracker = self.parameterAsVectorLayer(parameters, self.TRACKER, context)
        R = self.parameterAsInt(parameters, self.RADIUS, context)
        deslocamento_linha_2 = self.parameterAsVectorLayer(parameters, self.DIA_2, context)
        deslocamento_linha_1 = self.parameterAsVectorLayer(parameters, self.DIA_1, context)

        if deslocamento_linha_1.wkbType() != deslocamento_linha_2.wkbType():
            raise QgsProcessingException(self.tr("As camadas de entrada não possuem o mesmo tipo de geometria"))

        # Definir os parâmetros para a ferramenta Points to Path
        params = {
            'INPUT': tracker,
            'CLOSE_PATH':False,
            'ORDER_EXPRESSION':'"creation_time"',
            'NATURAL_SORT':False,
            'GROUP_EXPRESSION':'',
            'OUTPUT': 'TEMPORARY_OUTPUT',
        }
        # Executar a ferramenta Points to Path
        result = processing.run('native:pointstopath', params)

        # Adicionar a camada resultante ao projeto
        path_layer = result['OUTPUT']
        
        return {self.OUTPUT: path_layer}