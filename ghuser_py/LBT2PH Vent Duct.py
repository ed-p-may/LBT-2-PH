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
Collects and organizes data for a duct for a Ventilation System.
-
EM March 1, 2021
    Args:
        ductLength_: List<Float | Curve> Input either a number for the length of 
            the duct from the Ventilation Unit to the building enclusure, or geometry 
            representing the duct (curve / line)
        ductWidth_: List<Float> Input the diameter (mm) of the duct. Default is 101mm (4")
        insulThickness_: List<Float> Input the thickness (mm) of insulation on the 
            duct. Default is 52mm (2")
        insulConductivity_: List<Float> Input the Lambda value (W/m-k) of the 
            insualtion. Default is 0.04 W/mk (Fiberglass)
    Returns:
        hrvDuct_: A Duct object for the Ventilation System. Connect to the 
            'hrvDuct_01_' or 'hrvDuct_02_' input on the 'Create Vent System' to 
            build a PHPP-Style Ventialtion System.
"""

import rhinoscriptsyntax as rs
import ghpythonlib.components as gh
import scriptcontext as sc
import Rhino
import Grasshopper.Kernel as ghK

import LBT2PH
import LBT2PH.__versions__
import LBT2PH.ventilation
import LBT2PH.helpers

reload(LBT2PH)
reload(LBT2PH.__versions__)
reload(LBT2PH.ventilation)
reload(LBT2PH.helpers)

ghenv.Component.Name = "LBT2PH Vent Duct"
LBT2PH.__versions__.set_component_params(ghenv, dev=False)
#-------------------------------------------------------------------------------

def getDuctInputIndexNumbers():
    """ Looks at the component's Inputs and finds the ones labeled 'ductLength_'
    
    Returns:
        The list Index value for the "ductLength_" input 
        Returns None if no match found
    """
    
    hrvDuct_inputNum = None
    
    for i, input in enumerate(ghenv.Component.Params.Input):
        if 'ductLength_' == input.Name:
            hrvDuct_inputNum = i
        
    return hrvDuct_inputNum

def determineDuctToUse(_inputList, _inputIndexNum):
    output = []
    
    if len(_inputList) != 0:
        for i, ductItem in enumerate(_inputList):
            if isinstance(ductItem, Rhino.Geometry.Curve):
                duct01GUID = ghenv.Component.Params.Input[_inputIndexNum].VolatileData[0][i].ReferenceID.ToString()
                output.append( duct01GUID )
            else:
                try:
                    output.append( LBT2PH.helpers.convert_value_to_metric(ductItem, 'M') )
                except:
                    output.append( ductItem )
    
    return output

def getParamValueAsList(_targetLen, _inputList, _unit):
    outputList = []
    
    if len(_inputList) == _targetLen:
        for item in _inputList:
            if item:
                outputList.append(LBT2PH.helpers.convert_value_to_metric(item, _unit))
    elif len(_inputList) != _targetLen and len(_inputList) != 0:
        for i in range(_targetLen):
            try:
                outputList.append(LBT2PH.helpers.convert_value_to_metric(_inputList[i], _unit))
            except:
                outputList.append(LBT2PH.helpers.convert_value_to_metric(_inputList[-1], _unit))
    else:
        outputList = []
    
    return outputList

#-------------------------------------------------------------------------------
# Clean up the inputs
hrvDuct_inputNum = getDuctInputIndexNumbers()
ductLengths = determineDuctToUse(ductLength_, hrvDuct_inputNum)

#-------------------------------------------------------------------------------
# Build the Duct Object

widths = getParamValueAsList(len(ductLengths), ductWidth_,'MM')
thickness = getParamValueAsList(len(ductLengths), insulThickness_, 'MM')
lambdas = getParamValueAsList(len(ductLengths), insulConductivity_, 'W/MK')

hrvDuct_ = LBT2PH.ventilation.PHPP_Sys_Duct(
        _duct_input=ductLengths,
        _wMM=widths,
        _iThckMM=thickness,
        _iLambda=lambdas,
        _ghdoc=ghdoc
        )

#-------------------------------------------------------------------------------
for warning in hrvDuct_.Warnings:
    ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, warning)

LBT2PH.helpers.preview_obj(hrvDuct_)