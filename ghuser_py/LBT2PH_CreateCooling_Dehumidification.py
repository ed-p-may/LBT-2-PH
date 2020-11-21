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
Set the parameters for an Additional Dehumidification Element. Sets the values on the 'Cooling Unit' worksheet.
-
EM November 21, 2020
    Args:
        wasteHeatToRoom_: ('x' or '') Default=''. If this field is checked, then the waste heat from the dehumidification unit will be considered as an internal heat gain. On the contrary, dehumidification has no influence on the thermal balance.
        SEER_: Default=1. 1 litre water per kWh electricity result in an energy efficiency ratio of 0.7. Good devices, e.g. with internal heat recovery, achieve values of up to 2.
    Returns:
        dehumidCooling_: 
"""

ghenv.Component.Name = "LBT2PH_CreateCooling_Dehumidification"
ghenv.Component.NickName = "Cooling | Dehumid"
ghenv.Component.Message = 'NOV_21_2020'
ghenv.Component.IconDisplayMode = ghenv.Component.IconDisplayMode.application
ghenv.Component.Category = "PH-Tools"
ghenv.Component.SubCategory = "01 | Model"


import LBT2PH
import LBT2PH.heating_cooling

reload( LBT2PH )
reload( LBT2PH.heating_cooling )

# ------------------------------------------------------------------------------
dehumid_cooling_ = LBT2PH.heating_cooling.PHPP_Cooling_Dehumid()

if waste_heat_to_room_: dehumid_cooling_.waste_to_room = waste_heat_to_room_
if SEER_:               dehumid_cooling_.seer = SEER_