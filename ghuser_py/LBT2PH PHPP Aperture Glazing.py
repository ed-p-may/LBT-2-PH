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
EM March 1, 2021
    Args:
        _name: The name for the new Window Glazing object
        _uValue: (List) Input value for the glazing U-Value (W/m2-k). Glass U-Value to be calculate as per EN-673 / ISO 10292
        _gValue: (List) Input value for the glazing g-Value (SHGC) . Glass g-Value (~SHGC) to be calculate as per EN-410
    Return:
        PHPPGlazing_: A new PHPP-Style Glazing Object for use in a PHPP Window. Connect to the 'PHPP Apertures' Component.
"""

import LBT2PH
import LBT2PH.__versions__
import LBT2PH.windows
from LBT2PH.helpers import convert_value_to_metric
from LBT2PH.helpers import preview_obj

reload(LBT2PH)
reload(LBT2PH.__versions__)
reload(LBT2PH.windows)
reload(LBT2PH.helpers)

ghenv.Component.Name = "LBT2PH PHPP Aperture Glazing"
LBT2PH.__versions__.set_component_params(ghenv, dev=False)
#-------------------------------------------------------------------------------

if _name:
    _name = _name.replace(" ", "_")
    
    PHPPGlazing_ = LBT2PH.windows.PHPP_Glazing()
    if _name:   PHPPGlazing_.name = _name
    if _gValue: PHPPGlazing_.gValue = convert_value_to_metric(_gValue, '-')
    if _uValue: PHPPGlazing_.uValue = convert_value_to_metric(_uValue, 'W/M2K')
    
    preview_obj(PHPPGlazing_)