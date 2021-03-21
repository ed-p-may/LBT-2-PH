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
EM March 21, 2021
    Args:
        _duct_length: List<Float | Curve> Input either a number for the length of 
            the duct from the Ventilation Unit to the building enclusure, or geometry 
            representing the duct (curve / line)
        duct_width_: List<Float> Input the diameter (mm) of the duct. Default is 101mm (4")
        insul_thickness_: List<Float> Input the thickness (mm) of insulation on the 
            duct. Default is 52mm (2")
        insul_conductivity_: List<Float> Input the Lambda value (W/m-k) of the 
            insualtion. Default is 0.04 W/mk (Fiberglass)
    Returns:
        hrv_duct_: A Duct object for the Ventilation System. Connect to the 
            'hrvDuct_01_' or 'hrvDuct_02_' input on the 'Create Vent System' to 
            build a PHPP-Style Ventialtion System.
"""

import LBT2PH
import LBT2PH.__versions__
import LBT2PH.ventilation
import LBT2PH.helpers

reload(LBT2PH)
reload(LBT2PH.__versions__)
reload(LBT2PH.ventilation)
reload(LBT2PH.helpers)

ghenv.Component.Name = "LBT2PH Vent Duct"
LBT2PH.__versions__.set_component_params(ghenv, dev='MAR_21_2021')

def clean_get(i, _in):
    """Handle mis-match input length issues """
    
    try:
        return _in[i]
    except IndexError:
        try:
            return _in[0]
        except IndexError:
            return None

# Build the Duct Segments
#-------------------------------------------------------------------------------
input_handler = LBT2PH.ventilation.duct_input_handler(ghdoc, ghenv)
duct_segments = []
for i, duct_segment in enumerate(_duct_length):
    
    # Build a basic Duct Segment
    new_duct_segment = LBT2PH.ventilation.PHPP_Sys_Duct_Segment()
    
    # Try and go get any Rhino params for the segment
    duct_len_input_node = 0 #index number
    length, width, i_thickness, i_lambda  = input_handler.get_segment(i, duct_segment, duct_len_input_node)
    if length: new_duct_segment.length = length
    if width: new_duct_segment.width = width
    if i_thickness: new_duct_segment.insul_thick = i_thickness
    if i_lambda: new_duct_segment.insul_lambda = i_lambda
    
    # Update / overwrite params with any GH inputs
    gh_width =         clean_get(i, duct_width_)
    gh_i_thickness =   clean_get(i, insul_thickness_)
    gh_i_lambda =      clean_get(i, insul_conductivity_)
    
    if gh_width:       new_duct_segment.width = gh_width
    if gh_i_thickness: new_duct_segment.insul_thick = gh_i_thickness
    if gh_i_lambda:    new_duct_segment.insul_lambda = gh_i_lambda
    
    duct_segments.append( new_duct_segment )

# Build the Duct from the Segments
#-------------------------------------------------------------------------------
duct_ = LBT2PH.ventilation.PHPP_Sys_Duct()
if duct_segments: duct_.segments = duct_segments

LBT2PH.helpers.preview_obj(duct_)