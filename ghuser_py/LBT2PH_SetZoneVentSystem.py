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
This Component is used to apply a new PHPP-Style Fresh-Air Ventilation System to a Honeybee Zone or Zones.
-
EM Nov. 21, 2020
    Args:
        _VentSystem: Input the Ventilation System PHPP Object created by the 'New Vent System' Component
        _HBZones: The Honeybee Zones to apply this Fresh Air Ventilation System to
    Returns:
        HBZones_: The Honeybee Zones with the new Vent System paramaters applied.
"""

ghenv.Component.Name = "LBT2PH_SetZoneVentSystem"
ghenv.Component.NickName = "Set Zone Vent"
ghenv.Component.Message = 'NOV_21_2020'
ghenv.Component.IconDisplayMode = ghenv.Component.IconDisplayMode.application
ghenv.Component.Category = "PH-Tools"
ghenv.Component.SubCategory = "01 | Model"

from copy import deepcopy

import LBT2PH
import LBT2PH.ventilation
import LBT2PH.helpers

reload(LBT2PH)
reload(LBT2PH.ventilation)
reload(LBT2PH.helpers)

if _vent_system:
    vent_system_dict = _vent_system.to_dict()
else:
    vent_system_dict = None


HB_rooms_ = []
for hb_room in _HB_rooms:
    
    user_data = deepcopy(hb_room.user_data)
    
    if vent_system_dict:
        user_data['phpp']['vent_system'] = vent_system_dict
        
        #Update the vent system name on all the spaces
        for space in user_data['phpp']['spaces'].values():
            space.update( {'phpp_vent_system_id':vent_system_dict['system_id']} )
    
    new_room = hb_room.duplicate()
    new_room.user_data = user_data
    HB_rooms_.append( new_room )
