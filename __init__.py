# -*- coding: utf-8 -*-
"""
/***************************************************************************
 additionalSchools
                                 A QGIS plugin
 this plugin calculates additional schools to be added in city
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2024-11-30
        copyright            : (C) 2024 by bsc-inf-01-20
        email                : bsc-inf-01-20@unima.ac.mw
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):
    from .additional_schools import AdditionalSchools
    return AdditionalSchools(iface)
