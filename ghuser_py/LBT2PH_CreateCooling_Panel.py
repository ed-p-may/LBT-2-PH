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
Set the parameters for a Panel Cooling Element. Sets the values on the 'Cooling Unit' worksheet.
-
EM November 26, 2020
    Args:
        SEER_: (W/W) Default=3
    Returns:
        panelCooling_: 
"""

ghenv.Component.Name = "LBT2PH_CreateCooling_Panel"
ghenv.Component.NickName = "Cooling | Panel"
ghenv.Component.Message = 'NOV_26_2020'
ghenv.Component.IconDisplayMode = ghenv.Component.IconDisplayMode.application
ghenv.Component.Category = "PH-Tools"
ghenv.Component.SubCategory = "01 | Model"

import LBT2PH
import LBT2PH.heating_cooling
from LBT2PH.helpers import preview_obj
from LBT2PH.helpers import convert_value_to_metric

reload( LBT2PH )
reload( LBT2PH.heating_cooling )
reload(LBT2PH.helpers)

#-------------------------------------------------------------------------------
panel_cooling_ = LBT2PH.heating_cooling.PHPP_Cooling_Panel()
if SEER_: panel_cooling_.seer = convert_value_to_metric(SEER_, 'W/W')

preview_obj(panel_cooling_)