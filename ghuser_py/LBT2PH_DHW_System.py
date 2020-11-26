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
EM November 26, 2020
    Args:
        usage_: The Usage Profile object decribing DHW litres/person/day of HW at the Design Forward temp (unmixed). Input the result from a 'DHW Usage' component.
        design_frwrd_T: (Deg C) Design Forward Temperature. Default is 60 deg C. Unmixed HW temp.
        ['DHW+Distribution', Cell J146]
        circulation_piping_: The Recirculation Piping (not including branches). This is only used if there is a recirc loop in the project. Connect a 'Pipping | Recirc' component here.
        ['DHW+Distribution', Cells J149:N163]
        branch_piping_: All the branch (non-recirc) piping. Connect the 'Piping | Banches' result here. 
        ['DHW+Distribution', Cells J167:N175]
        tank1_: The main DHW tank (if any) used. Input the results of a 'DHW Tank' component.
        ['DHW+Distribution', Cells J186:J204]
        tank2_: The secondary DHW tank (if any) used. Input the results of a 'DHW Tank' component. 
        ['DHW+Distribution', Cells M186:M204]
        buffer_tank_: The DHW buffer tank (if any) used. Input the results of a 'DHW Tank' component. 
        ['DHW+Distribution', Cells P186:P204]
    Returns:
        dhw_: The combined DHW System object with all params. Connect this to the 'dhw_' input on the 'Create Excel Obj - Setup' component to use.
"""

ghenv.Component.Name = "LBT2PH_DHW_System"
ghenv.Component.NickName = "DHW"
ghenv.Component.Message = 'NOV_26_2020'
ghenv.Component.IconDisplayMode = ghenv.Component.IconDisplayMode.application
ghenv.Component.Category = "PH-Tools"
ghenv.Component.SubCategory = "01 | Model"

import scriptcontext as sc
import Grasshopper.Kernel as ghK

import LBT2PH
import LBT2PH.dhw
from LBT2PH.helpers import add_to_HB_model

reload( LBT2PH )
reload( LBT2PH.dhw )


# Classes and Defs
def check_input(_obj, _key, _inputName):
    try:
        result = getattr(_obj, _key)
        return True
    except:
        warning = "Error. The '{}' input doesn't look right?\nMissing or incorrect type of input for: '{}'.\nPlease check your input values.".format(_inputName, _key)
        ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, warning)
        return False

#-------------------------------------------------------------------------------
# Organize up inputs
if circulation_piping_:
    circulation_piping_ = { obj.id:obj for obj in circulation_piping_ }
else:
    circulation_piping_ = { 'default':LBT2PH.dhw.PHPP_DHW_RecircPipe() }

if branch_piping_:
    branch_piping_ = { obj.id:obj for obj in branch_piping_ }
else:
    branch_piping_ = { 'default':LBT2PH.dhw.PHPP_DHW_branch_piping() }

if not _system_name: _system_name = 'DHW'
if not usage_: LBT2PH.dhw.PHPP_DHW_usage_Res()
if not design_frwrd_T: design_frwrd_T = 60
if not tank1_: tank1_ = LBT2PH.dhw.PHPP_DHW_tank()
if not tank2_: tank2_ = LBT2PH.dhw.PHPP_DHW_tank()
if not buffer_tank_: buffer_tank_ = LBT2PH.dhw.PHPP_DHW_tank()

#-------------------------------------------------------------------------------
# Get the HB-Room ID's
hb_rooms_assigned_to = []
for hb_room in _HB_rooms:
    hb_rooms_assigned_to.append( hb_room.display_name )

#-------------------------------------------------------------------------------
# Create the DHW System Object
dhw_system_obj = LBT2PH.dhw.PHPP_DHW_System(hb_rooms_assigned_to, _system_name, usage_, design_frwrd_T,
            circulation_piping_, branch_piping_, tank1_, tank2_, buffer_tank_ )

#-------------------------------------------------------------------------------
# Add the new System onto the HB-Rooms
HB_rooms_ = []
for hb_room in _HB_rooms:
    new_hb_room = hb_room.duplicate()
    new_hb_room = add_to_HB_model(new_hb_room, 'dhw_systems', {dhw_system_obj.id:dhw_system_obj.to_dict()}, ghenv )
    HB_rooms_.append( new_hb_room )