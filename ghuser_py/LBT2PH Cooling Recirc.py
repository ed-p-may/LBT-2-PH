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
Set the parameters for a Recirculation Cooling element (AC). Sets the values 
on the 'Cooling Unit' worksheet.
-
EM March 1, 2021
    Args:
        on_offMode_: ('x' or '') Default=''. Cyclical operation works through an 
            on/off regulation of the compressor. If this field is left empty, 
                then the assumption is that the unit has a VRF (variant refrigerant 
                flow), which works by modulating the efficiency of the compressor.
        maxCoolingCap_: (kW) Default = 1000
        volFlowAtNomPower_: (m3/h) Default = 40,000 
        variableVol_: ('x' or '') Default='x'. VAV system: The volume flow changes 
            proportionally to the cooling capacity, thereby reducing the temperature 
            remains constant (usually better dehumidification).
        SEER_: (W/W) Default = 3
- bad devices: 2.5
- split units, energy efficiency class A: > 3.2
- compact units, energy efficiency class A: > 3.0
- turbo compressor > 500 kW with water cooling: up to more than 6

    Returns:
        recircAirCooling_: 
"""

import scriptcontext as sc
import Grasshopper.Kernel as ghK

import LBT2PH
import LBT2PH.__versions__
import LBT2PH.heating_cooling
from LBT2PH.helpers import preview_obj
from LBT2PH.helpers import convert_value_to_metric

reload( LBT2PH )
reload(LBT2PH.__versions__)
reload( LBT2PH.heating_cooling )
reload(LBT2PH.helpers)

ghenv.Component.Name = "LBT2PH Cooling Recirc"
LBT2PH.__versions__.set_component_params(ghenv, dev=False)

#-------------------------------------------------------------------------------
recirc_air_cooling_ = LBT2PH.heating_cooling.PHPP_Cooling_RecircAir()

if on_off_mode_:            recirc_air_cooling_.on_off = on_off_mode_
if max_cooling_cap_:        recirc_air_cooling_.max_capacity = convert_value_to_metric(max_cooling_cap_, 'KW')
if vol_flow_at_nom_power_:  recirc_air_cooling_.nominal_vol = convert_value_to_metric(vol_flow_at_nom_power_, 'M3/H')
if variable_vol_:           recirc_air_cooling_.variable_vol = variable_vol_
if SEER_:                   recirc_air_cooling_.seer = convert_value_to_metric(SEER_, 'W/W')

preview_obj(recirc_air_cooling_)