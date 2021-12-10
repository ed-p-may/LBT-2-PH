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
Use this component to add summmer ventilation to Honeybee rooms. This controls 
the inputs on the PHPP 'SummVent' worksheet. Use this to input the total daytime 
and nighttime ACH from any 'additional' ventilation beyond the basic HRV/ERV. 
This could be from operable windows, additional fans or any other method used to 
increase airflow during the summer months.
-
EM March 21, 2021
    Args:
        _HB_rooms: The Honeybee rooms to add summer-ventilation to.
        use_default_: <boolean> Default=False. Set True to use 'default' values 
            for all summer-vent. This is recommended.
        basic_ach_: <float> The Air-Changes-per-Hour (ACH) during the daytime. 
            Note, this value gets applied to EACH HB-Room you pass in. In the 
            PHPP, the SummVent worksheet will be the Total of all the HB-Room ACH values.
        nighttime_ach_: <float> The Air-Changes-per-Hour (ACH) during the nighttime. 
            Note, this value gets applied to EACH HB-Room you pass in. In the PHPP, 
            the SummVent worksheet will be the Total of all the HB-Room ach values.
    Returns:
        HB_rooms_: The Honeybee rooms with the summer-ventilation added.
"""

import LBT2PH
import LBT2PH.__versions__
import LBT2PH.summer_vent
import LBT2PH.helpers

reload(LBT2PH)
reload(LBT2PH.__versions__)
reload(LBT2PH.summer_vent)
reload(LBT2PH.helpers)

ghenv.Component.Name = "LBT2PH Summer Ventilation"
LBT2PH.__versions__.set_component_params(ghenv, dev='MAR_21_2021')

#-------------------------------------------------------------------------------
# Build the Summ-Vent Object
summ_vent_obj = LBT2PH.summer_vent.PHPP_SummVent()
if use_default_:
    summ_vent_obj.day_ach = 'default'
    summ_vent_obj.night_ach = 'default'

if basic_ach_ is not None: summ_vent_obj.day_ach = float(basic_ach_)
if nighttime_ach is not None: summ_vent_obj.night_ach = float(nighttime_ach)

#-------------------------------------------------------------------------------
# Add the Summ-Vent objects onto the Honeybee Rooms
HB_rooms_ = []
output_dict = {summ_vent_obj.id:summ_vent_obj.to_dict() }
for hb_room in _HB_rooms:
    new_room = hb_room.duplicate()
    new_room = LBT2PH.helpers.add_to_HB_model(hb_room, 'summ_vent', output_dict, ghenv, 'overwrite' )
    
    HB_rooms_.append( new_room )