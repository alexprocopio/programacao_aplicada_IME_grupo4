from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import (
    QgsProcessing,
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
    QgsFeatureRequest
)
import processing
from collections import defaultdict


class Projeto4SolucaoComplementar(QgsProcessingAlgorithm):
    # Declarando os nossos parâmetros que utilizaremos para a resolução da questão.
    DESLOCAMENTO = 'DESLOCAMENTO'
    BARRAGEM = 'BARRAGEM'
    MASSADAGUA = 'MASSADAGUA'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return Projeto4SolucaoComplementar()

    def name(self):
        return 'solucao_projeto4Complementar'

    def displayName(self):
        return self.tr('Solução Projeto 4 Complementar')

    def group(self):
        return self.tr('Projeto 4 Complementar')

    def groupId(self):
        return 'projeto4Complementar'

    def shortHelpString(self):
        return self.tr("Funciona por favor")

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.DESLOCAMENTO,
                self.tr('VIA DE DESLOCAMENTO'),
                [QgsProcessing.TypeVectorLine]
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.BARRAGEM,
               self.tr('BARRAGEM'),
                [QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.MASSADAGUA,
                self.tr('MASSA DAGUA'),
                [QgsProcessing.TypeVectorPolygon]
            )
        )

        self.addParameter(
                QgsProcessingParameterFeatureSink(
                    self.OUTPUT,
                    self.tr('Erros Output')
                )
            )

    def processAlgorithm(self, parameters, context, feedback):
        barragem = self.parameterAsVectorLayer(parameters, self.BARRAGEM, context)
        massadagua = self.parameterAsVectorLayer(parameters, self.MASSADAGUA, context)
        deslocamento = self.parameterAsVectorLayer(parameters, self.DESLOCAMENTO, context)

        new_fields = QgsFields()
        new_field = QgsField('Tipo de Erro', QVariant.String)
        new_fields.append(new_field)

        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT,
                                               context, new_fields, QgsWkbTypes.Point,
                                               deslocamento.sourceCrs())

        multiStepFeedback = QgsProcessingMultiStepFeedback(3, feedback)
        multiStepFeedback.setCurrentStep(0)
        multiStepFeedback.setProgressText(self.tr("Verificando estrtutura"))
        for agua in massadagua.getFeatures():
            if agua['tipo'] in [10,11]:
                r = 0

                for bar in barragem.getFeatures():
                    if agua.geometry().touches(bar.geometry()):
                        r = 1
                        break
                if r == 0 :
                    centro = agua.geometry().centroid()
                    new_feature = QgsFeature()
                    new_feature.setGeometry(centro)
                    new_feature.setAttributes(['Regra 6: Toda represa/açude deve ter parte de sua borda coincidindo com uma barragem'])
                    sink.addFeature(new_feature, QgsFeatureSink.FastInsert)
        multiStepFeedback.setCurrentStep(1)
        for bar in barragem.getFeatures():
            p = 0
            for estrada in deslocamento.getFeatures():
                if bar.geometry().intersects(estrada.geometry()):
                    p = 1
                    break
            if p == 1 and bar['sobreposto_transportes'] == 2:
                line_geom = estrada.geometry()
                length = line_geom.length()
                midpoint = line_geom.interpolate(length / 2)

                new_feature = QgsFeature()
                new_feature.setGeometry(midpoint)
                new_feature.setAttributes(
                    ['Regra 7: Existe Interseção com estrada'])
                sink.addFeature(new_feature, QgsFeatureSink.FastInsert)
            if p== 0 and bar['sobreposto_transportes'] == 1:
                line_geom = estrada.geometry()
                length = line_geom.length()
                midpoint = line_geom.interpolate(length / 2)

                new_feature = QgsFeature()
                new_feature.setGeometry(midpoint)
                new_feature.setAttributes(
                    ['Regra 7: Não existe interseção com estrada'])
                sink.addFeature(new_feature, QgsFeatureSink.FastInsert)
            multiStepFeedback.setCurrentStep(2)



        # Armazenando para que se consiga mudar o estilo da camada de saída, temos:
        self.dest_id = dest_id

        # Retornando a saída das feições de resultado
        return {self.OUTPUT: dest_id}