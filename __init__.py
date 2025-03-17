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

def classFactory(iface):
    """
    加载KmlExport插件。
    
    :param iface: QGIS界面实例
    :type iface: QgsInterface
    """
    from .kml_export_plugin import KmlExportPlugin
    return KmlExportPlugin(iface) 