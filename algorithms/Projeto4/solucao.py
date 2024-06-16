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


class Projeto4Solucao(QgsProcessingAlgorithm):
    # Declarando os nossos parâmetros que utilizaremos para a resolução da questão.
    DRENAGEM = 'DRENAGEM'
    VIARIO = 'VIARIO'
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
        return Projeto4Solucao()

    def name(self):
        return 'solucao_projeto4'

    def displayName(self):
        return self.tr('Solução Projeto 4')

    def group(self):
        return self.tr('Projeto 4')

    def groupId(self):
        return 'projeto4'

    def shortHelpString(self):
        return self.tr("Funciona por favor")

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.DRENAGEM,
                self.tr('VIA DE DRENAGEM'),
                [QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.VIARIO,
                self.tr('ELEMENTO VIARIO'),
                [QgsProcessing.TypeVectorPoint]
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.DESLOCAMENTO,
                self.tr('VIA DE DESLOCAMENTO'),
                [QgsProcessing.TypeVectorLine]
            )
        )

    #    self.addParameter(
    #        QgsProcessingParameterFeatureSource(
    #            self.BARRAGEM,
    #           self.tr('BARRAGEM'),
    #            [QgsProcessing.TypeVectorLine]
    #        )
    #    )
    #    self.addParameter(
    #        QgsProcessingParameterFeatureSource(
    #            self.MASSADAGUA,
    #            self.tr('MASSA DAGUA'),
    #            [QgsProcessing.TypeVectorLine]
    #        )
    #    )

        self.addParameter(
                QgsProcessingParameterFeatureSink(
                    self.OUTPUT,
                    self.tr('Erros Output')
                )
            )

    def processAlgorithm(self, parameters, context, feedback):
        drenagem = self.parameterAsSource(parameters, self.DRENAGEM, context)
        viario = self.parameterAsSource(parameters, self.VIARIO, context)
        deslocamento = self.parameterAsSource(parameters, self.DESLOCAMENTO, context)

        new_fields = QgsFields()
        new_field = QgsField("regra", QVariant.Int)
        new_fields.append(new_field)

        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT,
                                               context, new_fields, viario.wkbType(),
                                               viario.sourceCrs())

        multiStepFeedback = QgsProcessingMultiStepFeedback(6, feedback)
        multiStepFeedback.setCurrentStep(0)
        multiStepFeedback.setProgressText(self.tr("Verificando estrtutura"))

        for feature in viario.getFeatures():
            if feature['situacao_fisica']:
                new_feature = QgsFeature()
                new_feature.setGeometry(feature.geometry())

                new_feature.setAttributes([1])

                sink.addFeature(new_feature, QgsFeatureSink.FastInsert)
            if feature['tipo'] == 401 and  feature['material_construcao'] != 97:
                new_feature = QgsFeature()
                new_feature.setGeometry(feature.geometry())

                new_feature.setAttributes([1])

                sink.addFeature(new_feature, QgsFeatureSink.FastInsert)
        multiStepFeedback.setCurrentStep(1)
        for feature in deslocamento.getFeatures():
            if feature['situacao_fisica']:
                new_feature = QgsFeature()
                new_feature.setGeometry(feature.geometry())

                new_feature.setAttributes([1])

                sink.addFeature(new_feature, QgsFeatureSink.FastInsert)
            if feature['nr_pistas'] > feature['nr_faixas']:
                new_feature = QgsFeature()
                new_feature.setGeometry(feature.geometry())

                new_feature.setAttributes([1])

                sink.addFeature(new_feature, QgsFeatureSink.FastInsert)
        multiStepFeedback.setCurrentStep(2)
        intersect = processing.run("native:lineintersections", {
            'INPUT': drenagem,
            'INTERSECT': deslocamento,
            'INPUT_FIELDS': [], 'INTERSECT_FIELDS': [], 'INTERSECT_FIELDS_PREFIX': '', 'OUTPUT': 'TEMPORARY_OUTPUT'})
        dic_int = {}
        for feature in intersect['OUTPUT'].getFeatures():
            dic_int[(feature['id'],feature['id_2'])] +=1
            #Regra 3
            for feature1 in viario.getFeatures():
                if feature1.geometry().intersects(feature.geometry()):
                    if feature1['tipo'] not in [501, 201, 203, 202,204, 402, 401]:
                        new_feature = QgsFeature()
                        new_feature.setGeometry(feature.geometry)
                        new_feature.setAttributes([3])
                        sink.addFeature(new_feature, QgsFeatureSink.FastInsert)
                        break

        #Regra 2
        for (id1,id2),n in dic_int.items():
            if n>1:
                for feature in drenagem.getFeatures():
                    if feature['id'] == id1:
                        line_geom = feature.geometry()
                        length = line_geom.length()
                        midpoint = line_geom.interpolate(length / 2)

                        new_feature = QgsFeature()
                        new_feature.setGeometry(midpoint)
                        new_feature.setAttributes([2])
                        sink.addFeature(new_feature, QgsFeatureSink.FastInsert)



        multiStepFeedback.setCurrentStep(3)
        # regra 4
        for feature in viario.getFeatures():
            if feature['model_uso'] == 4 and feature['tipo'] in [501, 201, 203, 202,204, 402, 401]:
                r = 0
                for feature1 in intersect['OUTPUT'].getFeatures():
                    if feature.geometry().intersects(feature1.geometry()):
                        r = r+1
                        break
                if r>0:
                    new_feature = QgsFeature()
                    new_feature.setGeometry(feature.geometry())
                    new_feature.setAttributes([4])
                    sink.addFeature(new_feature, QgsFeatureSink.FastInsert)

        multiStepFeedback.setCurrentStep(4)
        for bridge_feature in viario.getFeatures():
            if bridge_feature['modal_uso'] == 4 and bridge_feature['tipo'] in [201,202,203,204] :
                bridge_geom = bridge_feature.geometry()
                coinciding = False
                for via_feature in deslocamento.getFeatures():
                    via_geom = via_feature.geometry()
                    for vertex in via_geom.vertices():
                        if bridge_geom.intersects(QgsGeometry.fromPointXY(QgsPointXY(vertex))):
                            coinciding = True
                            if bridge_feature['nr_faixas'] != via_feature['nr_faixas'] or \
                                    bridge_feature['nr_pistas'] != via_feature['nr_pistas'] or \
                                    bridge_feature['situacao_fisica'] != via_feature['situacao_fisica']:
                                new_feature = QgsFeature()
                                new_feature.setGeometry(bridge_geom)
                                new_feature.setAttributes([5])
                                sink.addFeature(new_feature, QgsFeatureSink.FastInsert)
                            break
                    if coinciding:
                        break
                if not coinciding:
                    new_feature = QgsFeature()
                    new_feature.setGeometry(bridge_geom)
                    new_feature.setAttributes([5])
                    sink.addFeature(new_feature, QgsFeatureSink.FastInsert)
        multiStepFeedback.setCurrentStep(5)
        # Armazenando para que se consiga mudar o estilo da camada de saída, temos:
        self.dest_id = dest_id


        # Retornando a saída das feições de resultado
        return {self.OUTPUT: dest_id}