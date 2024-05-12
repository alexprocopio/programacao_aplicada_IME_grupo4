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
                       QgsFeatureRequest, QgsGeometry, QgsPoint)
import numpy as np


class Projeto2SolucaoComplementar(QgsProcessingAlgorithm):
    # Declarando os nossos parâmetros que utilizaremos para a resolução da questão.

    OUTPUT = 'OUTPUT'
    OUTPUT1 = 'OUTPUT1'
    OUTPUT2 = 'OUTPUT2'
    OUTPUT3 = 'OUTPUT3'
    OUTPUT4 = 'OUTPUT4'
    PONTOS_PISTA = 'Pistas de Pouso Pontos'
    LINHAS_PISTA = 'Pistas de Pouso Linhas'
    AREAS_PISTA = 'Pistas de Pouso Areas'
    INPUT = 'INPUT'
    ESCALA = 'ESCALA'
    MOLDURA = 'MOLDURA'
    CURVAS = 'Curvas de Nível'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return Projeto2SolucaoComplementar()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'projeto2'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Projeto2')

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
        return 'Projeto2'

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

        # Camada MDT de entrada
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT,
                self.tr('MDT'),
                [QgsProcessing.TypeRaster]
            )
        )

        # Camada vetorial ponto de pistas de pouso
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.PONTOS_PISTA,
                self.tr('Pistas de Pouso Pontos'),
                [QgsProcessing.TypeVectorPoint]
            )
        )
        # Camada vetorial linha de pistas de pouso
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.LINHAS_PISTA,
                self.tr('Pistas de Pouso Linhas'),
                [QgsProcessing.TypeVectorLine]
            )
        )
        # Camada vetorial linha de cuva de nivel
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.CURVAS,
                self.tr('Curvas de Nível'),
                [QgsProcessing.TypeVectorLine]
            )
        )
        # Camada vetorial Área de pistas de pouso
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.AREAS_PISTA,
                self.tr('Pistas de Pouso Areas'),
                [QgsProcessing.TypeVectorAnyGeometry]
            )
        )

        # Adicionando o parâmetro de escala
        options = ['1:25.000', '1:50.000', '1:100.000', '1:250.000']
        self.addParameter(
            QgsProcessingParameterEnum(
                self.ESCALA,
                self.tr('Escala'),
                options,
                defaultValue=options[0]  # Valor padrão
            )
        )
        # Adicionando camada vetorial área para moldura
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.MOLDURA,
                self.tr('Moldura'),
                [QgsProcessing.TypeVectorAnyGeometry]
            )
        )
        # Adicionando o parâmetro de saída (OUTPUT)
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Curvas de nivel output')
            ))
        # Adicionando o parâmetro de saída (OUTPUT1)
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT1,
                self.tr('Altitude Pontos output')
            )

        )
        # Adicionando o parâmetro de saída (OUTPUT2)
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT2,
                self.tr('Altitude Linhas output')
            )

        )
        # Adicionando o parâmetro de saída (OUTPUT3)
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT3,
                self.tr('Altitude Áreas Linhas output')
            )

        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT4,
                self.tr('Pontos Cotados')
            )

        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Aqui será feita o processamento do algoritmo.
        """

        # Alocando na variável escala a escala escolhida pelo usuário
        escala_index = self.parameterAsEnum(parameters, self.ESCALA, context)
        escala_equidistancia = {
            '0': 10,
            '1': 20,
            '2': 50,
            '3': 100}
        equidistancia = escala_equidistancia[str(escala_index)]
        equidistancia_mestre = 5 * equidistancia
        curvas_layer = self.parameterAsVectorLayer(parameters, self.CURVAS, context)
        mdt_layer = self.parameterAsRasterLayer(parameters, self.INPUT, context)
        pontos_layer = self.parameterAsVectorLayer(parameters, self.PONTOS_PISTA, context)
        linhas_layer = self.parameterAsVectorLayer(parameters, self.LINHAS_PISTA, context)
        areas_layer = self.parameterAsVectorLayer(parameters, self.AREAS_PISTA, context)
        moldura_layer = self.parameterAsVectorLayer(parameters, self.MOLDURA, context)

        # Alocando a camada de saída na variável sink
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT,
                                               context, curvas_layer.fields(), curvas_layer.wkbType(),
                                               curvas_layer.sourceCrs())
        (sink2, dest_id2) = self.parameterAsSink(parameters, self.OUTPUT1,
                                                 context, pontos_layer.fields(), pontos_layer.wkbType(),
                                                 pontos_layer.sourceCrs())
        (sink3, dest_id3) = self.parameterAsSink(parameters, self.OUTPUT2,
                                                 context, linhas_layer.fields(), linhas_layer.wkbType(),
                                                 linhas_layer.sourceCrs())
        (sink4, dest_id4) = self.parameterAsSink(parameters, self.OUTPUT3,
                                                 context, areas_layer.fields(), areas_layer.wkbType(),
                                                 areas_layer.sourceCrs())
        (sink5, dest_id5) = self.parameterAsSink(parameters, self.OUTPUT4,
                                                 context, pontos_layer.fields(), pontos_layer.wkbType(),
                                                 pontos_layer.sourceCrs())

        # Adicionando o multistepfeedback para poder mostrar na tela o carregamento
        multiStepFeedback = QgsProcessingMultiStepFeedback(6, feedback)
        multiStepFeedback.setCurrentStep(0)
        multiStepFeedback.setProgressText(self.tr("Verificando estrtutura"))

        for feature in curvas_layer.getFeatures():
            cota = feature['cota']
            if cota % equidistancia == 0 and cota % equidistancia_mestre != 0:
                feature['indice'] = 2
                # Adicione a feature à camada de saída
                sink.addFeature(feature)
                # Atualize o valor do atributo "índice" para 0
            elif cota % equidistancia_mestre == 0:
                # Adicione a feature à camada de saída
                feature['indice'] = 1
                sink.addFeature(feature)
        multiStepFeedback.setCurrentStep(1)
        for feature in pontos_layer.getFeatures():
            ponto = feature.geometry().asPoint()
            value = mdt_layer.dataProvider().identify(ponto, QgsRaster.IdentifyFormatValue).results()[1]
            value = round(value, 1)
            feature['altitude'] = value
            sink2.addFeature(feature)
        multiStepFeedback.setCurrentStep(3)
        for feature in linhas_layer.getFeatures():
            geometry = feature.geometry()
            total_length = geometry.length()
            mid_point = geometry.interpolate(total_length / 2.0)
            mid_point = mid_point.asPoint()
            value = mdt_layer.dataProvider().identify(mid_point, QgsRaster.IdentifyFormatValue).results()[1]
            value = round(value, 1)
            feature['altitude'] = value
            sink3.addFeature(feature)
        multiStepFeedback.setCurrentStep(4)
        for feature in areas_layer.getFeatures():
            geometry = feature.geometry()
            centroid = geometry.centroid()
            centroid = centroid.asPoint()
            value = mdt_layer.dataProvider().identify(centroid, QgsRaster.IdentifyFormatValue).results()[1]
            value = round(value, 1)
            feature['altitude'] = value
            sink4.addFeature(feature)
        alg_params = {
            'INPUT': curvas_layer,
            'OUTPUT': 'TEMPORARY_OUTPUT'
        }

        # Execute o algoritmo
        poligono_moldura = None
        for feature in moldura_layer.getFeatures():
            poligono_moldura = feature.geometry()
            break
        multiStepFeedback.setCurrentStep(5)
        pontos_processados = set()
        lista = []

        def ring(geom_multilinestring):
            """
            Cria um anel fechado a partir de uma geometria MultiLineString.

            :param geom_multilinestring: QgsGeometry representando uma MultiLineString.
            :return: QgsGeometry representando um anel fechado.
            """
            # Inicializa uma lista de pontos para formar o anel
            ring_points = []

            # Itera sobre todas as partes das linhas contidas na geometria MultiLineString
            for part in geom_multilinestring.parts():
                # Adiciona todos os pontos da parte atual à lista de pontos do anel
                ring_points.extend(part)

            # Adiciona o primeiro ponto ao final da lista para fechar o anel
            ring_points.append(ring_points[0])
            ring_points = [QgsPointXY(point) for point in ring_points]
            # Cria um QgsGeometry a partir dos pontos do anel e retorna
            return QgsGeometry.fromPolygonXY([[point for point in ring_points]])

        def max_raster_value(raster_layer, ring_geometry):
            """
            Calcula o valor máximo do raster para todos os pontos contidos dentro do anel de geometria.

            :param raster_layer: QgsRasterLayer representando a camada raster.
            :param ring_geometry: QgsGeometry representando o anel.
            :return: Valor máximo do raster dentro do anel.
            """
            # Inicializa o valor máximo como negativo infinito
            max_value = float("-inf")

            # Obtém todos os pontos dentro do anel
            points_within_ring = [point for point in ring_geometry.asPolygon()[0]]
            count = 0
            # Itera sobre os pontos dentro do anel
            for point in points_within_ring:
                # Identifica o valor do raster no ponto

                #value = raster_layer.dataProvider().identify(point, QgsRaster.IdentifyFormatValue).results()[1]
                count +=1
                value = count
                # Atualiza o valor máximo, se necessário
                if value > max_value:
                    max_value = value
                    max_value_point = point

            return max_value,max_value_point
        for feature in curvas_layer.getFeatures():
            if poligono_moldura.contains(feature.geometry()):
                geometria = feature.geometry()
                anel = ring(geometria)
                valor,ponto = max_raster_value(mdt_layer,anel)
                if ponto:
                    if ponto not in pontos_processados:
                        lista.append((ponto, valor))
                        # Adicionar o ponto ao conjunto de pontos processados
                        pontos_processados.add(ponto)
        for i in range(len(lista)):
            point, value = lista[i]
            # Criar uma nova feature
            nova_feature = QgsFeature()

            # Definir a geometria da nova feature
            nova_feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(point)))

            # Criar uma lista de atributos preenchidos com None, exceto o último atributo (altitude)
            atributos = [None] * 6 + [value]  # 6 representa os primeiros 6 atributos e o último é altitude

            # Definir os atributos da nova feature
            nova_feature.setAttributes(atributos)

            # Adicionar a nova feature ao sink5
            sink5.addFeature(nova_feature)

        multiStepFeedback.setCurrentStep(6)

        # Armazenando para que se consiga mudar o estilo da camada de saída, temos:
        self.dest_id = dest_id
        self.dest_id2 = dest_id2
        self.dest_id3 = dest_id3
        self.dest_id4 = dest_id4
        self.dest_id5 = dest_id5

        # Retornando a saída das feições de resultado
        return {self.OUTPUT: dest_id, self.OUTPUT1: dest_id2, self.OUTPUT2: dest_id3, self.OUTPUT3: dest_id4,
                self.OUTPUT4: dest_id5}

