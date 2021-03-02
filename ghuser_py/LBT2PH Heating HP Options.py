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
Set the control options for a Air- or Water-Source Heat Pump (HP). Sets the values 
on the 'HP' worksheet.
-
EM March 1, 2021
    Args:
        _designForwardWaterTemp: (Deg C) Default=35. If using the PHI 'Heat Pump Tool', 
            input the Design Forward Temp from the 'Main Results' worksheet here. 
            Usually like 25-30 Deg C. This value will get set back on the 'DHW' worksheet. 
            Don't ask me what this is or why it's done this way. I'm just just 
            followin' the tool here...
        hp_distribution_: The Heat Pump heating distribution method. Input either:
            > "1-Underfloor heating"
            > "2-Radiators"
            > "3-Supply air heating"
        nom_power_: (kW) Only to be entered in special cases. Most users leave blank.
        rad_exponent_: Only to the entered in special cases. Most users leave blank.
        backup_type_: Type of backup heater. Default is "1-Elec Immersion heater". Enter either:
            > "1-Elec. Immersion heater"
            > "2-Electric continuous flow water heater"
        dT_elec_flow_water_: (Deg C) delta-Temp of electric continuous flow water heater
        hp_priority_: Heat Pump priority. Default is "1-DHW-priority". Enter either:
            > "1-DHW-priority"
            > "2-Heating priority"
        hp_control_: Default is "1-On/Off". Enter either:
            > "1-On/Off"
            > "2-Ideal"
        depth_groundwater_: (m) Depth ground water / Ground collector / Ground probe.
        power_groundpump_: (kW) Power of pump for ground heat exchanger.
    Returns:
        hpOptions_: A Heat Pump object. Connect this output to the 'hpOptions_' 
            input on a 'Heating/Cooling System' component.
"""

import LBT2PH
import LBT2PH.__versions__
import LBT2PH.heating_cooling
from LBT2PH.helpers import preview_obj
from LBT2PH.helpers import convert_value_to_metric

reload( LBT2PH )
reload(LBT2PH.__versions__)
reload( LBT2PH.heating_cooling )
reload(LBT2PH.helpers)

ghenv.Component.Name = "LBT2PH Heating HP Options"
LBT2PH.__versions__.set_component_params(ghenv, dev=False)

#-------------------------------------------------------------------------------
hp_options_ = LBT2PH.heating_cooling.PHPP_HP_Options()

if _design_forward_water_temp:  hp_options_.frwd_temp = convert_value_to_metric(_design_forward_water_temp, 'C')
if hp_distribution_:            hp_options_.hp_distribution = hp_distribution_
if nom_power_:                  hp_options_.nom_power = convert_value_to_metric(nom_power_, 'KW')
if rad_exponent_:               hp_options_.rad_exponent = rad_exponent_
if backup_type_:                hp_options_.backup_type = backup_type_
if dT_elec_flow_water_:         hp_options_.dT_elec_flow = convert_value_to_metric(dT_elec_flow_water_, 'C')
if hp_priority_:                hp_options_.hp_priority = hp_priority_
if hp_control_:                 hp_options_.hp_control = hp_control_
if depth_groundwater_:          hp_options_.depth_groundwater = convert_value_to_metric(depth_groundwater_, 'M')
if power_groundpump_:           hp_options_.power_groundwater = convert_value_to_metric(power_groundpump_, 'KW')

preview_obj(hp_options_)