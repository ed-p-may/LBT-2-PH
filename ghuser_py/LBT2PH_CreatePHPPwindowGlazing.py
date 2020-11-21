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
Will combine parameters together to create a new PHPP Window Glazing object which can be used by the 'PHPP Apertures' component.
-
EM November 21, 2020
    Args:
        _name: The name for the new Window Glazing object
        _uValue: (List) Input value for the glazing U-Value (W/m2-k). Glass U-Value to be calculate as per EN-673 / ISO 10292
        _gValue: (List) Input value for the glazing g-Value (SHGC) . Glass g-Value (~SHGC) to be calculate as per EN-410
    Return:
        PHPPGlazing_: A new PHPP-Style Glazing Object for use in a PHPP Window. Connect to the 'PHPP Apertures' Component.
"""

ghenv.Component.Name = "LBT2PH_CreatePHPPwindowGlazing"
ghenv.Component.NickName = "New PHPP Glazing"
ghenv.Component.Message = 'NOV_21_2020'
ghenv.Component.IconDisplayMode = ghenv.Component.IconDisplayMode.application
ghenv.Component.Category = "PH-Tools"
ghenv.Component.SubCategory = "01 | Model"

import rhinoscriptsyntax as rs
import scriptcontext as sc
import LBT2PH
import LBT2PH.windows

reload(LBT2PH)
reload(LBT2PH.windows)

if _name:
    _name = _name.replace(" ", "_")
    
    PHPPGlazing_ = LBT2PH.windows.PHPP_Glazing(
                        _name if _name else 'Unnamed_Glazing',
                        float(_gValue) if _gValue else 0.4,
                        float(_uValue) if _uValue else 1.0
                        )