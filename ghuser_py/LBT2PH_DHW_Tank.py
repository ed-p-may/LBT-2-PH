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
Creates DHW Tank for the 'DHW+Distribution' PHPP worksheet.
-
EM November 26, 2020
    Args:
        _tank_type: ("0-No storage tank", "1-DHW and heating", "2-DHW only") The type of use for this tank.
        tank_solar_: (True/False) Is this tank hooked up to a Solar HW system?
        tank_HLrate_: (W/k) Heat Loss rate from the tank. Default is 4.0 W/k
        tank_volume_: (litres) Nominal tank volume. Default is 300 litres (80 gallons)
        tank_standby_frac_: (%) The Standby Fraction. Default is 0.30 (30%)
        tank_location_: ("1-Inside", "2-Outside") The location of this HW tank.
        tank_location_T_: (Deg C) The avg air-temp of the tank location if outside the building. 
    Returns:
        tank_location_T_: A DHW Tank Object. Connect this to one of the 'tank_' inputs on the 'DHW System' component in order to pass along to the PHPP.
"""

ghenv.Component.Name = "LBT2PH_DHW_Tank"
ghenv.Component.NickName = "DHW Tank"
ghenv.Component.Message = 'NOV_26_2020'
ghenv.Component.IconDisplayMode = ghenv.Component.IconDisplayMode.application
ghenv.Component.Category = "PH-Tools"
ghenv.Component.SubCategory = "01 | Model"

import scriptcontext as sc
import Grasshopper.Kernel as ghK

import LBT2PH
import LBT2PH.dhw
import LBT2PH.helpers

reload( LBT2PH )
reload( LBT2PH.dhw )
reload( LBT2PH.helpers )

#-------------------------------------------------------------------------------
# Creat Storage Tank
storage_tank_ = LBT2PH.dhw.PHPP_DHW_tank()
if _tank_type: storage_tank_.type = _tank_type
if tank_solar_: storage_tank_.solar = tank_solar_
if tank_HLrate_: storage_tank_.hl_rate = LBT2PH.dhw.clean_input(tank_HLrate_, 'tank_HLrate_', 'W/K', ghenv)
if tank_volume_: storage_tank_.vol = LBT2PH.dhw.clean_input(tank_volume_, 'tank_volume_', 'L', ghenv)
if tank_standby_frac_: storage_tank_.stndbyFrac = LBT2PH.dhw.clean_input(tank_standby_frac_, 'tank_standby_frac_', '-', ghenv)
if tank_location_: storage_tank_.location = tank_location_
if tank_location_T_: storage_tank_.location_t = LBT2PH.dhw.clean_input(tank_location_T_, 'tank_location_T_', 'C', ghenv)

LBT2PH.helpers.preview_obj(storage_tank_)