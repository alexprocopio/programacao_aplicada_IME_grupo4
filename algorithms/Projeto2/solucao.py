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
                       QgsFeatureRequest)
import processing



class Projeto2Solucao(QgsProcessingAlgorithm):
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
        return Projeto2Solucao()

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
        poligonos_preenchidos_layer = processing.run("qgis:linestopolygons", {'INPUT':curvas_layer,'OUTPUT':'TEMPORARY_OUTPUT'})['OUTPUT']

        poligono_moldura = None
        for feature in moldura_layer.getFeatures():
            poligono_moldura = feature.geometry()
            break
        multiStepFeedback.setCurrentStep(5)


        def achar_maximo(mdt_layer, polygon):
            max_valor = -float('inf')
            max_ponto = None

            extent = polygon.boundingBox()

            for x in range(int(extent.xMinimum()), int(extent.xMaximum())):
                for y in range(int(extent.yMinimum()), int(extent.yMaximum())):
                    point = QgsPointXY(x, y)
                    if polygon.contains(point):
                        value = mdt_layer.dataProvider().identify(point, QgsRaster.IdentifyFormatValue).results()[1]
                        if value > max_valor:
                            max_valor = value
                            max_ponto = point

            return max_valor, max_ponto

        added_points = set()
        for feature in poligonos_preenchidos_layer.getFeatures():
            print('count')
            if poligono_moldura.contains(feature.geometry()):
                max_valor, max_ponto = achar_maximo(mdt_layer, feature.geometry())
                if max_ponto is not None:
                    if max_ponto not in added_points:
                        nova_feature = QgsFeature()
                        nova_feature.setGeometry(QgsGeometry.fromPointXY(max_ponto))
                        nova_feature.setAttributes([None] * 7)
                        nova_feature['altitude'] = max_valor
                        sink5.addFeature(nova_feature)
                        added_points.add(max_ponto)

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

