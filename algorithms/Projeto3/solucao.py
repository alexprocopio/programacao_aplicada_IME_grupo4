from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsWkbTypes,
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
                       QgsVectorLayer,
                       QgsProject)
import processing

class Projeto3Solucao(QgsProcessingAlgorithm):
    DIA_1 = 'DIA_1'
    DIA_2 = 'DIA_2'
    TRACKER = 'TRACKER'
    RADIUS = 'RADIUS'
    SELECTED_ATTRIBUTES = 'SELECTED_ATTRIBUTES'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return Projeto3Solucao()

    def name(self):
        return 'projeto3solucao'

    def displayName(self):
        return self.tr('Projeto 3 Solução')

    def group(self):
        return self.tr('Example scripts')

    def groupId(self):
        return 'examplescripts'

    def shortHelpString(self):
        return self.tr("Este algoritmo compara as features entre duas camadas (Dia 1 e Dia 2) e utiliza uma camada de rastreamento para gerar caminhos e realizar comparações.")

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.DIA_1,
                self.tr('Camada Dia 1'),
                [QgsProcessing.TypeVectorAnyGeometry]
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.DIA_2,
                self.tr('Camada Dia 2'),
                [QgsProcessing.TypeVectorAnyGeometry]
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.TRACKER,
                self.tr('Tracker'),
                [QgsProcessing.TypeVectorPoint]
            )
        )

        self.addParameter(
            QgsProcessingParameterEnum(
                self.SELECTED_ATTRIBUTES,
                self.tr('Selecione os atributos a serem utilizados'),
                options=['nome', 'tipo', 'situacao_fisica', 'material_construcao', 'revestimento', 'trafego', 'nr_faixas', 'nr_pistas',
                         'canteiro_divisorio', 'jurisdicao', 'sigla', 'administracao', 'concessionaria'],
                allowMultiple=True,
                defaultValue=[]
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.RADIUS,
                self.tr('Raio do Buffer'),
                type=QgsProcessingParameterNumber.Integer,
                minValue=0,
                maxValue=100,
                defaultValue=10
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Output')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        R = self.parameterAsInt(parameters, self.RADIUS, context)
        layer1 = self.parameterAsVectorLayer(parameters, self.DIA_1, context)
        layer2 = self.parameterAsVectorLayer(parameters, self.DIA_2, context)
        tracker = self.parameterAsVectorLayer(parameters, self.TRACKER, context)
        selected_attributes = self.parameterAsEnums(parameters, self.SELECTED_ATTRIBUTES, context)

        if layer1.wkbType() != layer2.wkbType():
            raise QgsProcessingException(self.tr("As camadas de entrada não possuem o mesmo tipo de geometria"))

        feedback.pushInfo(self.tr('Gerando caminhos a partir da camada de rastreamento...'))

        params = {
            'INPUT': tracker,
            'ORDER_EXPRESSION': '"creation_time"',
            'GROUP_EXPRESSION': '',
            'OUTPUT': 'TEMPORARY_OUTPUT'
        }

        result = processing.run('native:pointstopath', params, context=context, feedback=feedback)
        percurso = result['OUTPUT']

        feedback.pushInfo(self.tr('Gerando buffer ao redor do percurso...'))

        buffer_params = {
            'INPUT': percurso,
            'DISTANCE': R,
            'SEGMENTS': 5,
            'END_CAP_STYLE': 0,  # Round
            'JOIN_STYLE': 0,  # Round
            'MITER_LIMIT': 2,
            'DISSOLVE': True,
            'OUTPUT': 'TEMPORARY_OUTPUT'
        }

        buffer_result = processing.run('native:buffer', buffer_params, context=context, feedback=feedback)
        buffer_layer = buffer_result['OUTPUT']

        feedback.pushInfo(self.tr('Comparando atributos selecionados...'))

        index_layer2 = QgsSpatialIndex(layer2.getFeatures())
        index_layer1 = QgsSpatialIndex(layer1.getFeatures())

        changes_fields = QgsFields()
        for field in layer1.fields():
            changes_fields.append(field)
        changes_fields.append(QgsField('change_type', QVariant.Int))

        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context, changes_fields, layer1.wkbType(), layer1.sourceCrs())

        selected_field_names = [layer1.fields()[i].name() for i in selected_attributes]

        buffer_geometry = QgsGeometry.unaryUnion([f.geometry() for f in buffer_layer.getFeatures()])

        # Verificando modificações
        for feature1 in layer1.getFeatures():
            geom1 = feature1.geometry()
            ids = index_layer2.intersects(geom1.boundingBox())
            found_match = False
            for id in ids:
                feature2 = layer2.getFeature(id)
                if feature2.geometry().intersects(geom1):
                    found_match = True
                    changed = False
                    for field_name in selected_field_names:
                        if feature1[field_name] != feature2[field_name]:
                            changed = True
                            break
                    if changed and buffer_geometry.intersects(geom1):
                        new_feature = QgsFeature(changes_fields)
                        new_feature.setGeometry(geom1)
                        for field in feature1.fields().toList():
                            new_feature.setAttribute(field.name(), feature1[field.name()])
                        new_feature.setAttribute('change_type', 2)  # Modificado
                        sink.addFeature(new_feature, QgsFeatureSink.FastInsert)
            if not found_match and buffer_geometry.intersects(geom1):
                new_feature = QgsFeature(changes_fields)
                new_feature.setGeometry(geom1)
                for field in feature1.fields().toList():
                    new_feature.setAttribute(field.name(), feature1[field.name()])
                new_feature.setAttribute('change_type', 0)  # Removido
                sink.addFeature(new_feature, QgsFeatureSink.FastInsert)

        # Verificando adições
        for feature2 in layer2.getFeatures():
            geom2 = feature2.geometry()
            ids = index_layer1.intersects(geom2.boundingBox())
            found_match = False
            for id in ids:
                feature1 = layer1.getFeature(id)
                if feature1.geometry().intersects(geom2):
                    found_match = True
                    break
            if not found_match and buffer_geometry.intersects(geom2):
                new_feature = QgsFeature(changes_fields)
                new_feature.setGeometry(geom2)
                for field in feature2.fields().toList():
                    new_feature.setAttribute(field.name(), feature2[field.name()])
                new_feature.setAttribute('change_type', 1)  # Adicionado
                sink.addFeature(new_feature, QgsFeatureSink.FastInsert)

        return {self.OUTPUT: dest_id}