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
Collects and organizes data for a DHW System. Hook up inputs from DHW components and this will organize for the excel writere.
Connect the output to the 'dhw_' input on the 'Create Excel Obj - Setup' component to use.
-
EM February 22, 2021
    Args:
        _system_name: (str) The name / idenfitier for the System.
        _HB_rooms: The Honeybee-Rooms you would like to apply the DHW System to.
        usage_: The Usage Profile object decribing DHW litres/person/day of HW at the Design Forward temp (unmixed). Input the result from a 'DHW Usage' component.
        design_frwrd_T: (Deg C) Design Forward Temperature. Default is 60 deg C. Unmixed HW temp.
        ['DHW+Distribution', Cell J146]
        circulation_piping_: The Recirculation Piping (not including branches). This is only used if there is a recirc loop in the project. Connect a 'Pipping | Recirc' component here.
        ['DHW+Distribution', Cells J149:N163]
        branch_piping_: All the branch (non-recirc) piping. Connect the 'Piping | Banches' result here. 
        ['DHW+Distribution', Cells J167:N175]
        tank1_: The main DHW tank (if any) used. Input the results of a 'DHW Tank' component.
        ['DHW+Distribution', Cells J186:J204]
        Note - Optionally, pass in the string 'default' in order to assign a default tank with a heat loss rate of 4 W/k.
        tank2_: The secondary DHW tank (if any) used. Input the results of a 'DHW Tank' component.
        ['DHW+Distribution', Cells M186:M204]
        Note - Optionally, pass in the string 'default' in order to assign a default tank with a heat loss rate of 4 W/k.
        buffer_tank_: The DHW buffer tank (if any) used. Input the results of a 'DHW Tank' component.
        ['DHW+Distribution', Cells P186:P204]
    Returns:
        dhw_: The combined DHW System object with all params. Connect this to the 'dhw_' input on the 'Create Excel Obj - Setup' component to use.
"""

ghenv.Component.Name = "LBT2PH_DHW_System"
ghenv.Component.NickName = "DHW"
ghenv.Component.Message = 'FEB_22_2021'
ghenv.Component.IconDisplayMode = ghenv.Component.IconDisplayMode.application
ghenv.Component.Category = "PH-Tools"
ghenv.Component.SubCategory = "01 | Model"

import LBT2PH
import LBT2PH.dhw
from LBT2PH.helpers import add_to_HB_model, preview_obj

reload( LBT2PH )
reload( LBT2PH.dhw )

#-------------------------------------------------------------------------------
# Create the DHW System Object
dhw_system_obj = LBT2PH.dhw.PHPP_DHW_System()
dhw_system_obj.rooms_assigned_to = [ hb_room.display_name for hb_room in _HB_rooms ]

if _system_name: dhw_system_obj.SystemName = _system_name
if usage_: dhw_system_obj.usage = usage_
if design_frwrd_T: dhw_system_obj.forwardTemp = design_frwrd_T

if circulation_piping_:
    try:
        dhw_system_obj.circulation_piping = { obj.id:obj for obj in circulation_piping_ }
    except AttributeError:
        recirc_obj = LBT2PH.dhw.PHPP_DHW_RecircPipe()
        recirc_obj.set_values_from_Rhino( circulation_piping_, ghenv, _input_num=3 )
        dhw_system_obj.circulation_piping[recirc_obj.id] = recirc_obj

if branch_piping_:
    try:
        dhw_system_obj.branch_piping = { obj.id:obj for obj in branch_piping_ }
    except AttributeError:
        branch_obj = LBT2PH.dhw.PHPP_DHW_branch_piping()
        branch_obj.set_pipe_lengths( branch_piping_, ghdoc, ghenv )
        dhw_system_obj.branch_piping[branch_obj.id] = branch_obj

if tank1_: dhw_system_obj.tank1 = tank1_
if tank2_: dhw_system_obj.tank2 = tank2_
if buffer_tank_: dhw_system_obj.tank_buffer = buffer_tank_

preview_obj(dhw_system_obj)

#-------------------------------------------------------------------------------
# Add the new System onto the HB-Rooms
HB_rooms_ = []
for hb_room in _HB_rooms:
    new_hb_room = hb_room.duplicate()
    new_hb_room = add_to_HB_model(new_hb_room, 'dhw_systems', {dhw_system_obj.id:dhw_system_obj.to_dict()}, ghenv )
    HB_rooms_.append( new_hb_room )