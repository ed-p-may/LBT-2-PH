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
EM Nov. 21, 2020
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
ghenv.Component.Message = 'NOV_21_2020'
ghenv.Component.IconDisplayMode = ghenv.Component.IconDisplayMode.application
ghenv.Component.Category = "PH-Tools"
ghenv.Component.SubCategory = "01 | Model"

import scriptcontext as sc
import Rhino
from random import randint

import LBT2PH
import LBT2PH.ventilation
import LBT2PH.helpers

reload(LBT2PH)
reload(LBT2PH.ventilation)
reload(LBT2PH.helpers)

def getDuctInputIndexNumbers():
    """ Looks at the component's Inputs and finds the ones labeled 'hrvDuct_'
    
    Returns:
        The list Index values for both the "hrvDuct_01_" input and the 
        "hrvDuct_02_" input. Returns None if no match found
    """
    
    hrvDuct_01_inputNum, hrvDuct_02_inputNum = None, None
    
    for i, input in enumerate(ghenv.Component.Params.Input):
        if 'hrvDuct_01_' == input.Name:
            hrvDuct_01_inputNum = i
        elif 'hrvDuct_02_' == input.Name:
            hrvDuct_02_inputNum = i
        
    return hrvDuct_01_inputNum, hrvDuct_02_inputNum

def determineDuctToUse(_input, _inputIndexNum):
    
    if not _input:
        return LBT2PH.ventilation.PHPP_Sys_Duct()
    
    try:
        duct_dict = _input[0].to_dict()
        duct = LBT2PH.ventilation.PHPP_Sys_Duct.from_dict( duct_dict )
        return duct
    except:
        pass
    
    ductLengths = []
    for i, item in enumerate(_input):
        try:
            ductLengths.append( float(item) )
        except:
            try:
                duct01GUID = ghenv.Component.Params.Input[_inputIndexNum].VolatileData[0][i].ReferenceID.ToString()
                ductLengths.append( duct01GUID )
            except:
                pass
    
    return LBT2PH.ventilation.PHPP_Sys_Duct(_duct_input=ductLengths, _ghdoc=ghdoc)

def sys_type(_in):
     if '2' in str(_in):
         return "2-Extract air unit"
     elif '3' in str(_in):
         return "3-Only window ventilation" 
     else:
         return "1-Balanced PH ventilation with HR [Default]"


#-------------------------------------------------------------------------------
# Handle Duct Inputs
hrvDuct_01_inputNum, hrvDuct_02_inputNum = getDuctInputIndexNumbers()
hrvDuct1 = determineDuctToUse(hrvDuct_01_, hrvDuct_01_inputNum)
hrvDuct2 = determineDuctToUse(hrvDuct_02_, hrvDuct_02_inputNum)

system_name = vent_system_name_ if vent_system_name_ else 'Vent-1'
system_type = sys_type(vent_system_type_) if vent_system_type_ else '1-Balanced PH ventilation with HR'

if vent_unit_:
    try:
        vent_unit_d = vent_unit_.to_dict()
        vent_unit = LBT2PH.ventilation.PHPP_Sys_VentUnit.from_dict(vent_unit_d)
    except:
        vent_unit = LBT2PH.ventilation.PHPP_Sys_VentUnit()

exhaust_objects = []
if exhaust_vent_units_:
    for exhaust_unit in exhaust_vent_units_:
        exhaust_unit_d_ = exhaust_unit.to_dict()
        new_exhaust_unit = LBT2PH.ventilation.PHPP_Sys_ExhaustVent.from_dict(exhaust_unit_d_)
        exhaust_objects.append(new_exhaust_unit)

#-------------------------------------------------------------------------------
# Build the system
vent_system_ = LBT2PH.ventilation.PHPP_Sys_Ventilation(
                            _ghenv=ghenv,
                            _system_id=randint(1000,9999),
                            _system_type=system_type,
                            _systemName=system_name,
                            _unit=vent_unit,
                            _d01=hrvDuct1,
                            _d02=hrvDuct2,
                            _exhaustObjs=exhaust_objects )

LBT2PH.helpers.preview_obj(vent_system_)