#
# LBT2PH: A Plugin for creating Passive House Planning Package (PHPP) models from LadybugTools. Created by blgdtyp, llc
# 
# This component is part of the PH-Tools toolkit <https://github.com/PH-Tools>.
# 
# Copyright (c) 2020, bldgtyp, llc <phtools@bldgtyp.com> 
# LBT2PH is free software; you can redistribute it and/or modify 
# it under the terms of the GNU General Public License as published 
# by the Free Software Foundation; either version 3 of the License, 
# or (at your option) any later version. 
# 
# LBT2PH is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the 
# GNU General Public License for more details.
# 
# For a copy of the GNU General Public License
# see <http://www.gnu.org/licenses/>.
# 
# @license GPL-3.0+ <http://spdx.org/licenses/GPL-3.0+>
#
"""
DHW Solar Thermal System
-
EM March 1, 2021
    Args:
        _angle_off_north: (degree) Panel normal deviation off north
            0=North, 90=East, 180=South, West=270
        _angle_off_horizontal: (degree) Panel normal deviation off horizontal.
            0=Horizontal, 90=Vertical
        _host_surface: (str) The name of the PHPP Surface (from the PHPP Areas Worksheet)
            the panels are mounted on.
        
        _collector_type: The type of solar thermal panel. Input either:
            > 6-Standard flat plate collector
            > 7-Improved flat place collector
            > 8-Evacuated tube collector
        _collector_area: (m2) The total surface area of the solar thermal panels
        _collector_height: (m) Default=1. Distance between upper and lower rim of collector. 
            Required for shading calculation at small horizon heights.
            If no shading object, please enter 1.
        _horizon_height: (m) Default=0. Shading object height above the lower edge of 
            the collector. If no shading object present, enter 0.
        _horizon_distance: (m) Default=1000. Horizontal distance to the shading object.
            In case no shading object exists, then enter 1000.
        
        _additional_reduction_fac: (%) e.g. oriel windows, trees, other buildings, etc.
            > no additional shading: 100%
            > totally shaded: 0%
        
        _heating_support: (True | False) Default=False. 
        _dhw_priority: (True | False) Default=True. Only relevant if solar system supports 
            both heating and DHW
    Returns:
        solar_: A PHPP solar thermal hot water system. Connect to the "_solar" input
            on an LBT2PH "DHW" Component.
"""

import LBT2PH
import LBT2PH.__versions__
from LBT2PH.helpers import preview_obj
import LBT2PH.dhw

reload(LBT2PH)
reload(LBT2PH.dhw)
reload(LBT2PH.__versions__)

ghenv.Component.Name = "LBT2PH DHW Solar Thermal"
LBT2PH.__versions__.set_component_params(ghenv, dev=False)

#-------------------------------------------------------------------------------

solar_ = LBT2PH.dhw.PHPP_DHW_Solar()

if _angle_off_north: solar_.angle_off_north = _angle_off_north
if _angle_off_horizontal: solar_.angle_off_horizontal = _angle_off_horizontal
if _host_surface: solar_.host_surface = _host_surface
if _collector_type: solar_.collector_type = _collector_type
if _collector_area: solar_.collector_area = _collector_area
if _collector_height: solar_.collector_height = _collector_height
if _horizon_height: solar_.horizon_height = _horizon_height
if _horizon_distance: solar_.horion_distance = _horizon_distance
if _additional_reduction_fac: solar_.additional_reduction_fac = _additional_reduction_fac
if _heating_support: solar_.heating_support = _heating_support
if _dhw_priority: solar_.dhw_priority = _dhw_priority

preview_obj(solar_)