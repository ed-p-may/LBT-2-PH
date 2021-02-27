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
Creates a PHPP Hot-Water Boiler to provide space-heating and/or domestic hot water. Connect this 
component to the "_boiler" input on the "Heating/Cooling System" LBT2PH Component in order
to pass these values to PHPP.
Note that by default, 'standard' performance values will be used. If you would like to 
specify the performance values in detail, supply that information to the '_detailed_params' input.
See the PHPP, 'Boiler' worksheet for more information on how to configure this equipment.
-
EM February 27, 2021
    Args:
        _name: (str) A name for the Boiler object
        _detailed_params: By default, typical values will be applied for all equipment.
performance values. This is recommended for most users. Leave blank to use the defaults.
---
If you would like to override these, eneter the detailed attributes here. Enter values
as strings in the format "Range:Value" using a semicolon (":") as the separator - 
so for example entering "R34:12" will enter the value "12" in cell Range R34 
of the 'Boiler' worksheet in the PHPP. Use a multiline panel to input the
values for all bioler parameters. Check the PHPP 'Boiler' worksheet for the required values needed.
        _type: (str) The Type of the Boiler. Input either:
1-None
10-Improved gas condensing boiler
11-Improved oil condensing boiler
12-Gas condensing boiler
13-Oil condensing boiler
20-Low temperature boiler gas
21-Low temperature boiler oil
30-Firewood pieces (direct and indirect heat emission)
31-Wood pellets (direct and indirect heat emission)
32-Wood pellets (only indirect heat emission)
40-Reserve
        _fuel: (str) The Type of fuel to use. Input either:
20-Heating oil
21-Pyrolysis oil or bio oil
22-RE-Methanol (Oil)
30-Natural gas
31-LPG
32-Biogas
33-RE-Gas
44-Wood logs
46-Forest woodchips
47-Poplar woodchips
41-Hard coal
42-Brown coal
50-Pellets
    Returns:
        boiler_: A Boiler object for use in the PHPP. Connect this output to the 'boiler_' 
        input on the 'Heating/Cooling Systems' LBT2PH Component.
"""

ghenv.Component.Name = "LBT2PH_CreateHeating_Boiler"
ghenv.Component.NickName = "Heating | Boiler"
ghenv.Component.Message = 'FEB_27_2021'
ghenv.Component.IconDisplayMode = ghenv.Component.IconDisplayMode.application
ghenv.Component.Category = "PH-Tools"
ghenv.Component.SubCategory = "01 | Model"

import Grasshopper.Kernel as ghK

import LBT2PH
import LBT2PH.heating_cooling
from LBT2PH.helpers import preview_obj

reload(LBT2PH)
reload(LBT2PH.heating_cooling)

#-------------------------------------------------------------------------------
boiler_ = LBT2PH.heating_cooling.PHPP_Boiler()

if _type: boiler_.type = _type
if _fuel:  boiler_.fuel = _fuel
if _detailed_params: boiler_.params = _detailed_params

warning_message = boiler_.check_valid_fuel()
ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, warning_message)

preview_obj(boiler_)