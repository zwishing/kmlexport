from typing import Any, Optional

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingParameterMultipleLayers,
    QgsProcessingParameterFileDestination,
    QgsProcessingUtils,
    Qgis
)
from qgis import processing
import os


class KmlExportProcessingAlgorithm(QgsProcessingAlgorithm):
    """
    此算法将多个矢量图层导出为KML文件。
    """

    # 用于引用参数和输出的常量。
    # 当从另一个算法调用此算法时，或者当
    # 从QGIS控制台调用时将使用这些常量。

    INPUTS = "INPUTS"
    OUTPUT = "OUTPUT"

    def name(self) -> str:
        """
        返回算法名称，用于标识算法。
        此字符串应该是固定的，不应该被本地化。
        名称在每个提供者中应该是唯一的。名称应该只包含
        小写字母数字字符，不包含空格或其他
        格式字符。
        """
        return "导出为KML"

    def displayName(self) -> str:
        """
        返回翻译后的算法名称，应该用于任何
        用户可见的算法名称显示。
        """
        return "导出为KML"

    def group(self) -> str:
        """
        返回此算法所属的组的名称。
        此字符串应该被本地化。
        """
        return "导出为KML"

    def groupId(self) -> str:
        """
        返回此算法所属的组的唯一ID。
        此字符串应该是固定的，不应该被本地化。
        组ID在每个提供者中应该是唯一的。组ID应该
        只包含小写字母数字字符，不包含空格或其他
        格式字符。
        """
        return "导出为KML"

    def shortHelpString(self) -> str:
        """
        返回算法的本地化简短帮助字符串。
        此字符串应该提供关于算法功能的基本描述
        以及与之相关的参数和输出。
        """
        return "将多个矢量图层导出为单个KML文件"

    def initAlgorithm(self, config: Optional[dict[str, Any]] = None):
        """
        在这里我们定义算法的输入和输出，
        以及一些其他属性。
        """

        # 添加输入矢量要素源。它可以有任何类型的几何图形。
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.INPUTS,
                "输入图层",
                Qgis.ProcessingSourceType.VectorAnyGeometry,
            )
        )

        # 为KML输出添加文件目标参数
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT, 
                "输出KML文件", 
                fileFilter="KML files (*.kml)"
            )
        )

    def processAlgorithm(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> dict[str, Any]:
        """
        这里是处理过程发生的地方。
        """

        # 获取多个输入图层
        input_layers = self.parameterAsLayerList(parameters, self.INPUTS, context)
        
        if not input_layers:
            raise QgsProcessingException("没有提供输入图层")
        
        # 获取输出KML文件路径
        output_kml = self.parameterAsFileOutput(parameters, self.OUTPUT, context)
        
        if not output_kml:
            raise QgsProcessingException("未指定输出KML文件路径")
        
        feedback.pushInfo(f"将导出 {len(input_layers)} 个图层到 {output_kml}")
        
        # 创建或清空输出KML文件
        if os.path.exists(output_kml):
            feedback.pushInfo(f"输出文件已存在，将被删除: {output_kml}")
            os.remove(output_kml)
        
        # 计算总进度步数
        total_steps = len(input_layers) + 1  # 所有图层 + 最终转换
        
        # 创建临时GeoPackage文件（使用完整路径）
        temp_folder = QgsProcessingUtils.tempFolder()
        temp_gpkg = os.path.join(temp_folder, "temp_layers.gpkg")
        feedback.pushInfo(f"创建临时GeoPackage文件: {temp_gpkg}")
        
        # 如果临时文件已存在，先删除
        if os.path.exists(temp_gpkg):
            os.remove(temp_gpkg)
            feedback.pushInfo(f"删除已存在的临时文件: {temp_gpkg}")
        
        # 用于跟踪已使用的图层名称
        used_layer_names = set()
        
        # 将所有图层写入到GeoPackage
        for current, layer in enumerate(input_layers):
            if feedback.isCanceled():
                break
                
            # 获取原始图层名称
            original_layer_name = layer.name()
            
            # 处理图层名称重复的情况
            layer_name = original_layer_name
            suffix = 1
            while layer_name in used_layer_names:
                layer_name = f"{original_layer_name}_{suffix}"
                suffix += 1
            
            # 记录已使用的图层名称
            used_layer_names.add(layer_name)
            
            if layer_name != original_layer_name:
                feedback.pushInfo(f"图层名称重复，使用新名称: {layer_name}")
            
            feedback.pushInfo(f"处理图层: {layer_name}")
            
            try:
                # 使用native:savefeatures保存图层到GeoPackage
                save_options = {
                    'INPUT': layer,
                    'OUTPUT': temp_gpkg,
                    'LAYER_NAME': layer_name,
                    'DATASOURCE_OPTIONS': '',
                    'LAYER_OPTIONS': ''
                }
                
                # 设置正确的ACTION_ON_EXISTING_FILE参数
                if current == 0:
                    # 第一个图层，创建或覆盖文件
                    save_options['ACTION_ON_EXISTING_FILE'] = 0  # 创建或覆盖文件
                    feedback.pushInfo(f"创建新的GeoPackage并添加第一个图层: {layer_name}")
                else:
                    # 后续图层，创建或覆盖图层
                    save_options['ACTION_ON_EXISTING_FILE'] = 1  # 创建或覆盖图层
                    feedback.pushInfo(f"追加图层到GeoPackage: {layer_name}")
                
                # 执行保存操作
                processing.run(
                    "native:savefeatures",
                    save_options,
                    context=context,
                    feedback=feedback,
                    is_child_algorithm=True
                )
                
                feedback.pushInfo(f"成功将图层 {layer_name} 添加到GeoPackage")
            except Exception as e:
                feedback.pushInfo(f"添加图层 {layer_name} 到GeoPackage时出错: {str(e)}")
                # 尝试删除临时文件
                if os.path.exists(temp_gpkg):
                    try:
                        os.remove(temp_gpkg)
                    except Exception as e:
                        feedback.pushInfo(f"删除临时文件时出错: {str(e)}")
                raise QgsProcessingException(f"添加图层 {layer_name} 到GeoPackage时出错: {str(e)}")
            
            # 更新进度
            feedback.setProgress(int((current + 1) / total_steps * 100))
        
        # 检查GeoPackage是否成功创建
        if not os.path.exists(temp_gpkg):
            raise QgsProcessingException(f"未能创建临时GeoPackage文件: {temp_gpkg}")
        
        feedback.pushInfo(f"所有图层已成功写入到GeoPackage: {temp_gpkg}")
        
        # 将GeoPackage导出为KML，使用CONVERT_ALL_LAYERS=True选项
        feedback.pushInfo("将GeoPackage导出为KML...")
        gdal_options = "-dim XY"
        
        try:
            # 使用gdal:convertformat将GeoPackage转换为KML
            processing.run(
                "gdal:convertformat",
                {
                    "INPUT": temp_gpkg,
                    "CONVERT_ALL_LAYERS": True,
                    "OUTPUT": output_kml,
                    "OPTIONS": gdal_options
                },
                context=context,
                feedback=feedback,
                is_child_algorithm=True
            )
            
            if not os.path.exists(output_kml):
                raise QgsProcessingException(f"gdal:convertformat未能生成KML文件: {output_kml}")
                
            feedback.pushInfo(f"成功将GeoPackage转换为KML: {output_kml}")
            
        except Exception as e:
            feedback.pushInfo(f"将GeoPackage转换为KML时出错: {str(e)}")
            raise QgsProcessingException(f"将GeoPackage转换为KML时出错: {str(e)}")
        finally:
            # 无论成功还是失败，都尝试删除临时文件
            if os.path.exists(temp_gpkg):
                try:
                    os.remove(temp_gpkg)
                    feedback.pushInfo(f"已删除临时GeoPackage文件: {temp_gpkg}")
                except Exception as e:
                    feedback.pushInfo(f"无法删除临时GeoPackage文件: {str(e)}")
                    # 不抛出异常，因为主要任务已经完成
            else:
                feedback.pushInfo("临时GeoPackage文件不存在或已被删除")
        
        feedback.pushInfo(f"成功导出 {len(input_layers)} 个图层到 {output_kml}")
        
        # 返回结果
        return {self.OUTPUT: output_kml}

    def createInstance(self):
        return self.__class__()
