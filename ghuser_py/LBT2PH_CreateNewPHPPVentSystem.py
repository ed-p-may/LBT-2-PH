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
Collects and organizes data for a simple fresh-air ventilation system (HRV/ERV). Outputs a 'ventilation' class object to apply to a HB Zone.
-
EM January 18, 2020
    Args:
        ventUnitType_: Input Type. Either: "1-Balanced PH ventilation with HR [Default]", "2-Extract air unit", "3-Only window ventilation"
        ventSystemName_: <Optional> A name for the overall system. ie: 'ERV-1', etc.. Will show up in the 'Additional Ventilation' worksheet as the 'Description of Ventilation Units' (E97-E107)
        ventUnit_: Input the HRV/ERV unit object. Connect to the 'ventUnit_' output on the 'Ventilator' Component
        hrvDuct_01_: Input the HRV/ERV Duct object. Connect to the 'hrvDuct_' output on the 'Vent Duct' Component
        hrvDuct_02_: Input the HRV/ERV Duct object. Connect to the 'hrvDuct_' output on the 'Vent Duct' Component
        frostProtectionT_: Min Temp for frost protection to kick in. [deg.  C]. Deffault is -5 C
    Returns:
        ventilation_: A Ventilation Class object with all the params and data related to the simple Ventilation system. Connect this to the '_VentSystem' input on the 'Set Zone Vent' Component.
"""

ghenv.Component.Name = "LBT2PH_CreateNewPHPPVentSystem"
ghenv.Component.NickName = "Create Vent System"
ghenv.Component.Message = 'JAN_18_2020'
ghenv.Component.IconDisplayMode = ghenv.Component.IconDisplayMode.application
ghenv.Component.Category = "PH-Tools"
ghenv.Component.SubCategory = "01 | Model"

import Rhino

import LBT2PH
import LBT2PH.ventilation
import LBT2PH.helpers

reload(LBT2PH)
reload(LBT2PH.ventilation)
reload(LBT2PH.helpers)

def getDuctInputIndexNumbers():
    """ Looks at the component's Inputs and finds the ones labeled 'hrvDuct_'
    
    Returns:
        The list Index values for both the "hrv_duct_01_" input and the 
        "hrv_duct_02_" input. Returns None if no match found
    """
    
    hrvDuct_01_inputNum, hrvDuct_02_inputNum = None, None
    
    for i, input in enumerate(ghenv.Component.Params.Input):
        if 'DUCT_01' in input.Name.upper():
            hrvDuct_01_inputNum = i
        elif 'DUCT_02' in input.Name.upper():
            hrvDuct_02_inputNum = i
    
    return hrvDuct_01_inputNum, hrvDuct_02_inputNum

def determineDuctToUse(_input, _inputIndexNum):
    
    if not _input:
        return None
    
    try:
        duct_dict = _input[0].to_dict()
        duct = LBT2PH.ventilation.PHPP_Sys_Duct.from_dict( duct_dict )
        return duct
    except:
        pass
    
    ductLengths = []
    for i, item in enumerate(_input):
        if isinstance(item, Rhino.Geometry.Curve):
            duct01GUID = ghenv.Component.Params.Input[_inputIndexNum].VolatileData[0][i].ReferenceID.ToString()
            ductLengths.append( duct01GUID )
        else:
            ductLengths.append( LBT2PH.helpers.convert_value_to_metric(item, 'M') )
    
    return LBT2PH.ventilation.PHPP_Sys_Duct(_duct_input=ductLengths, _ghdoc=ghdoc)

def handle_system_type(_in):
     if '2' in str(_in):
         return "2-Extract air unit"
     elif '3' in str(_in):
         return "3-Only window ventilation" 
     else:
         return "1-Balanced PH ventilation with HR [Default]"


# Handle Duct Inputs
#-------------------------------------------------------------------------------
hrvDuct_01_inputNum, hrvDuct_02_inputNum = getDuctInputIndexNumbers()
hrvDuct1 = determineDuctToUse(hrv_duct_01_, hrvDuct_01_inputNum)
hrvDuct2 = determineDuctToUse(hrv_duct_02_, hrvDuct_02_inputNum)


# Build the system
#-------------------------------------------------------------------------------
vent_system_ = LBT2PH.ventilation.PHPP_Sys_Ventilation(_ghenv=ghenv)

if vent_system_type_: vent_system_.system_type = handle_system_type(vent_system_type_)
if vent_system_name_: vent_system_.system_name = vent_system_name_
if vent_unit_: vent_system_.vent_unit = vent_unit_
if hrvDuct1: vent_system_.duct_01 = hrvDuct1
if hrvDuct2: vent_system_.duct_02 = hrvDuct2
if exhaust_vent_units_: vent_system_.exhaust_vent_objs = exhaust_vent_units_

LBT2PH.helpers.preview_obj(vent_system_)


# Add the system to the Honeybee-Rooms
#-------------------------------------------------------------------------------
HB_rooms_ = []
for hb_room in _HB_rooms:
    new_room = hb_room.duplicate()
    new_room = LBT2PH.helpers.add_to_HB_model( new_room, 'vent_system', vent_system_.to_dict(), ghenv )
    
    #Update the vent system name on all the spaces
    for space in new_room.user_data.get('phpp', {}).get('spaces', {}).values():
        space.update( { 'phpp_vent_system_id':vent_system_.system_id } )
    
    HB_rooms_.append( new_room )