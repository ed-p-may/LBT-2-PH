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
Builds Thermal Bridge (linear, point) objects to add to the PHPP. Use this component AFTER you create the Honeybee model - the TB values here are applied to the entire model.
-
Note that these objects are generally not inluced in the EnergyPlus model and so may be a source or discrepancy between the EnergyPlus reslults and the PHPP results. It will be more accurate to include these items in the final model.
-
EM November 21, 2020

    Args:
        estimated_tb_: <Optional> A single number (0 to 1) which represents the % increase in heat loss due to thermal bridging.
        Typical values could be: Passive House: +0.05, Good: +0.10,Medium: +0.25, Bad +0.40
        linear_tb_names_: <Optional> A list of names for the Thermal Bridge items to add to the PHPP. This will override any inputs in 'linear_tb_geom_'
        linear_tb_lengths_: <Optional> A list of Lengths (m) for the Thermal Bridge items to add to the PHPP. This will override any inputs in 'linear_tb_geom_'
        linear_tb_PsiValues_: <Optional> Either a single number or a list of Psi-Values (W/mk) to use for any Thermal Bridge items.
        If no values are passed, a default 0.01 W/mk value will be used for all Thermal Bridge items. If only one number is input, it will be used for all Psi-Value items output.
        linear_tb_geom_: <Optional> A list of Rhino Geometry (curves, lines) to use for finding lengths and names automatically.
        ------
        If you want this to read from Rhino rather than GH, pass all your referenced geometry thorugh an 'ID' (Primitive/GUID) object first before inputting.
        This will try and read the name from the Rhino-Scene object and use the object's name for the PHPP entry (Rhino: Properties/Object Name/...)
        -----
        point_tb_Names_: <Optional> A list of the Point-Thermal-Bridge names. Each name will become a unique point-TB object in the PHPP.
        point_tb_ChiValues_: <Optional> A list of Chi Values (W/mk) to use for the Point thermal bridges. If this list matches the 'point_tb_Names' input each will be used. If only one value is input, it will be used for all Chi-Values. If no values are input, a default of 0.1-W/mk will be used for all.
        Returns:
        thermalBridges_: Thermal Bridge objects to write to Excel. Connect to the 'thermalBridges_' input on the '2XL |  PHPP Geom' Component
"""

ghenv.Component.Name = "LBT2PH_SetTB"
ghenv.Component.NickName = "Thermal Bridges"
ghenv.Component.Message = 'NOV_21_2020'
ghenv.Component.IconDisplayMode = ghenv.Component.IconDisplayMode.application
ghenv.Component.Category = "PH-Tools"
ghenv.Component.SubCategory = "01 | Model"

import Grasshopper.Kernel as ghK
from copy import deepcopy

import LBT2PH
import LBT2PH.tb
import LBT2PH.helpers

reload( LBT2PH )
reload( LBT2PH.tb )
reload( LBT2PH.helpers )

def default_get(i, _input_list, _default=None):
    try:
        return _input_list[i]
    except IndexError:
        try:
            return _input_list[0]
        except IndexError:
            return _default

tb_objs = []

# ------------------------------------------------------------------------------
# Create the Linear Thermal Bridges
if linear_tb_lengths_:
    # Get Rhino scene inputs
    input_param_sets = LBT2PH.tb.organize_input_values( linear_tb_lengths_, linear_tb_psi_values_, linear_tb_fRsi_values_, ghenv, ghdoc )
    
    for param_set in input_param_sets:
        tb_obj = LBT2PH.tb.PHPP_ThermalBridge()
        tb_obj.typename = param_set.typename
        tb_obj.group_number = param_set.group
        tb_obj.length = param_set.length
        tb_obj.fRsi = param_set.fRsi
        tb_obj.psi_value = param_set.psi_value
        
        tb_objs.append( tb_obj )

# ------------------------------------------------------------------------------
# Include Point TBs
for i, point_tb in enumerate(point_tb_ChiValues_):
    tb_obj = LBT2PH.tb.PHPP_ThermalBridge()
    
    tb_obj.typename = default_get(i, point_tb_Names_, 'Point Thermal Bridge')
    tb_obj.group_number = '15: Ambient'
    tb_obj.length = 1
    tb_obj.fRsi = default_get(i, point_tb_fRsi_values_, 0.7)
    tb_obj.psi_value = point_tb
    
    tb_objs.append( tb_obj )

# ------------------------------------------------------------------------------
# Inlcude estimated TBs if there are any input
if estimated_tb_:
    if float(estimated_tb_) > 1:
        estimated_tb_ = float(estimated_tb_) / 100
    
    tb_obj = LBT2PH.tb.PHPP_ThermalBridge()
    tb_obj.typename = 'Estimated'
    tb_obj.length = float( estimated_tb_ )
    tb_obj.psi_value = "=SUM('Annual heating'!O12:O19)/'Annual heating'!M12"
    tb_obj.group_number = '15: Ambient'
    
    tb_objs.append( tb_obj )

# ------------------------------------------------------------------------------
# Add the TB Dicts to the model
if _model:
    HB_model_ = _model.duplicate()
    
    tb_dict = {}
    for tb_obj in tb_objs:
        tb_dict.update( {tb_obj.id:tb_obj.to_dict()} )
    
    HB_model_ = LBT2PH.helpers.add_to_HB_model(HB_model_, 'tb', tb_dict, ghenv ) 

