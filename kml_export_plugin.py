"""
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

from qgis.PyQt.QtCore import QCoreApplication, QTranslator
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsApplication, QgsProcessingAlgorithm, QgsProcessingRegistry, QgsProcessingProvider
import os.path

from .export_kml import KmlExportProcessingAlgorithm


class KmlExportPlugin:
    """QGIS插件实现"""

    def __init__(self, iface):
        """
        构造函数

        :param iface: QGIS界面实例，将存储以便您可以访问QGIS界面
        :type iface: QgsInterface
        """
        # 保存对QGIS界面的引用
        self.iface = iface
        
        # 初始化插件目录
        self.plugin_dir = os.path.dirname(__file__)
        
        # 初始化本地化
        locale = QgsApplication.locale()
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'KmlExport_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)
        
        # 声明实例属性
        self.actions = []
        self.menu = self.tr('&KML导出工具')
        
        # 检查是否是第一次运行
        self.first_start = None
        
        # 创建处理算法提供者
        self.provider = None

    def tr(self, message):
        """获取翻译后的字符串

        :param message: 要翻译的字符串
        :type message: str
        :returns: 翻译后的字符串
        :rtype: str
        """
        return QCoreApplication.translate('KmlExport', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """添加一个工具栏图标到QGIS GUI
        
        :param icon_path: 图标路径
        :type icon_path: str
        :param text: 按钮文本
        :type text: str
        :param callback: 点击时调用的函数
        :type callback: function
        :param enabled_flag: 是否启用按钮
        :type enabled_flag: bool
        :param add_to_menu: 是否添加到菜单
        :type add_to_menu: bool
        :param add_to_toolbar: 是否添加到工具栏
        :type add_to_toolbar: bool
        :param status_tip: 状态栏提示
        :type status_tip: str
        :param whats_this: 这是什么提示
        :type whats_this: str
        :param parent: 父组件
        :type parent: QWidget
        :returns: 创建的操作
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # 添加工具栏图标并将操作添加到插件菜单
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """创建图形用户界面"""
        # 注册处理算法
        self.provider = KmlExportProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)
        
        # 添加操作按钮
        icon_path = os.path.join(self.plugin_dir, 'icon.png')
        if not os.path.exists(icon_path):
            icon_path = ''
            
        self.add_action(
            icon_path,
            text=self.tr('导出为KML'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # 将first_start设置为True，以便在第一次启动时执行run()方法
        self.first_start = True

    def unload(self):
        """卸载插件时移除QGIS GUI项"""
        # 从处理框架中移除提供者
        QgsApplication.processingRegistry().removeProvider(self.provider)
        
        # 移除插件菜单项和图标
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr('&KML导出工具'),
                action)
            self.iface.removeToolBarIcon(action)

    def run(self):
        """插件的运行方法"""
        # 如果是第一次启动，显示对话框
        if self.first_start:
            self.first_start = False
            
        # 打开处理工具箱并显示我们的算法
        self.iface.openProcessingToolbox()
        

class KmlExportProvider(QgsProcessingProvider):
    """KML导出处理算法提供者"""
    
    def __init__(self):
        super().__init__()
        self.algs = []
        
    def id(self):
        return 'kmlexport'
        
    def name(self):
        return 'KML导出工具'
        
    def icon(self):
        return QgsApplication.getThemeIcon("/processingAlgorithm.svg")
        
    def svgIconPath(self):
        return QgsApplication.iconPath("processingAlgorithm.svg")
        
    def loadAlgorithms(self):
        self.algs = []
        self.algs.append(KmlExportProcessingAlgorithm())
        for alg in self.algs:
            self.addAlgorithm(alg) 