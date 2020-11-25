
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
Use this component to add summmer ventilation to Honeybee rooms. This controls the inputs on the PHPP 'SummVent' worksheet. Use this to input the total daytime and nighttime ACH from any 'additional' ventilation beyond the basic HRV/ERV. This could be from operable windows, additional fans or any other method used to increase airflow during the summer months.
-
EM November 25, 2020
    Args:
        _HB_rooms: The Honeybee rooms to add summer-ventilation to.
        use_default_: <boolean> Default=False. Set True to use 'default' values for all summer-vent. This is recommended.
        basic_ach_: <float> The Air-Changes-per-Hour (ACH) during the daytime.
        nighttime_ach_: <float> The Air-Changes-per-Hour (ACH) during the nighttime.
    Returns:
        HB_rooms_: The Honeybee rooms with the summer-ventilation added.
"""

ghenv.Component.Name = "LBT2PH_SummerVentilation"
ghenv.Component.NickName = "SummerVent"
ghenv.Component.Message = 'NOV_25_2020'
ghenv.Component.IconDisplayMode = ghenv.Component.IconDisplayMode.application
ghenv.Component.Category = "PH-Tools"
ghenv.Component.SubCategory = "02 | PHPP"

import LBT2PH
import LBT2PH.summer_vent
import LBT2PH.helpers

reload(LBT2PH)
reload(LBT2PH.summer_vent)
reload(LBT2PH.helpers)

#-------------------------------------------------------------------------------
# Build the Summ-Vent Object
summ_vent_obj = LBT2PH.summer_vent.PHPP_SummVent()
if use_default_:
    summ_vent_obj.day_ach = 'default'
    summ_vent_obj.night_ach = 'default'

if basic_ach_: summ_vent_obj.day_ach = basic_ach_
if nighttime_ach: summ_vent_obj.night_ach = nighttime_ach

#-------------------------------------------------------------------------------
# Add the Summ-Vent objects onto the Honeybee Rooms
HB_rooms_ = []
output_dict = {summ_vent_obj.id:summ_vent_obj.to_dict() }
for hb_room in _HB_rooms:
    new_room = hb_room.duplicate()
    new_room = LBT2PH.helpers.add_to_HB_model(hb_room, 'summ_vent', output_dict, ghenv, 'overwrite' )
    
    HB_rooms_.append( new_room )