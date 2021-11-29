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
Creates DHW Recirculation loops for the 'DHW+Distribution' PHPP worksheet.
Will take in curves from Rhino and calculate their lengths automatically. 
Will try and pull curve object attributes from Rhino as well - use attribute 
setter to assign the pipe diameter, insulation, etc... on the Rhino side.
-
EM November 29, 2021
    Args:
        pipe_geom_: (float: curve:) Recirculation piping. The input here will accept either:
            >   A single number representing the length (m) of the total loop in meters
            >   A list (multiline input) representing multiple pipe lengths (m). 
            These will be summed together for each branch
            >   A curve or curves with no parameter values. The length of the curves 
            will be summed together for each branch. You'll then need to enter the 
            diam, insulation, etc here in the GH Component.
            >   A curve or curves with paramerer values applied back in the Rhino scene. 
        pipe_diam_: <Optional> (mm) A List of numbers representing the nominal 
            diameters (mm) of the pipes in each branch. This will override any 
            values goten from the Rhino scene objects. If only one value is passed, 
            will be used for all objects.
        insul_thickness_: <Optional> (mm) A List of numbers representing the insulation 
            thickness (mm) of the pipes in each branch. This will override any values 
            goten from the Rhino scene objects. If only one value is passed, will 
            be used for all objects.
        insul_conductivity_: <Optional> (W/mk) A List of numbers representing the 
            insulation conductivity (W/mk) of the pipes in each branch. This will 
            override any values goten from the Rhino scene objects. If only one 
            value is passed, will be used for all objects.
        insul_reflective_: <Optional> A List of True/False values for the pipes 
            in each branch. True=Reflective Wrapper, False=No Reflective Wrapper. 
            This will override any values goten from the Rhino scene objects. If 
            only one value is passed, will be used for all objects.
        insul_quality_: ("1-None", "2-Moderate", "3-Good") The Quality of the 
            insulaton installation at the mountings, pipe-suspentions, couplings, 
            valves, etc.. (Note: not the quality of the overall pipe insulation).
        daily_period_: (hours) The usage period in hours/day that the recirculation 
            system operates. Default is 18 hrs/day.
    Returns:
        circulation_piping_: The Recirculation Piping object(s). Connect this to 
            the 'circulation_piping_' input on the 'DHW System' component in 
            order to pass along to the PHPP.
"""

import LBT2PH
import LBT2PH.__versions__
import LBT2PH.dhw
import LBT2PH.dhw_IO
from LBT2PH.helpers import convert_value_to_metric
from LBT2PH.helpers import preview_obj

reload( LBT2PH )
reload(LBT2PH.__versions__)
reload( LBT2PH.dhw )
reload( LBT2PH.dhw_IO )
reload( LBT2PH.helpers )

ghenv.Component.Name = "LBT2PH DHW Piping Recirc"
LBT2PH.__versions__.set_component_params(ghenv, dev='NOV_29_2021')

# --- Build the attr dict from GH UD inputs
# ------------------------------------------------------------------------------
attr_dicts = []
for i, v in enumerate(pipe_geom_):
    attr_dict = {}
    attr_dict['pipe_diameter'] = pipe_diam_[i] if i<len(pipe_diam_) else None
    attr_dict['insulation_thickness'] = insul_thickness_[i] if i<len(insul_thickness_) else None
    attr_dict['insulation_conductivity'] = insul_conductivity_[i] if i<len(insul_conductivity_) else None
    attr_dict['insulation_reflective'] = insul_reflective_[i] if i<len(insul_reflective_) else None
    attr_dict['insulation_quality'] = insul_quality_
    attr_dict['daily_period'] = daily_period_
    
    attr_dicts.append(attr_dict)

# ---- Build the standardized inputs
# ------------------------------------------------------------------------------

piping_inputs = LBT2PH.dhw_IO.piping_input_values(_input_node=0, _user_input=pipe_geom_,
                                    _user_attr_dicts=attr_dicts, _ghenv=ghenv, _ghdoc=ghdoc)

# ---- Create the Pipe Segments
# ------------------------------------------------------------------------------
circulation_piping_ = []
for segment in piping_inputs:
    new_segment = LBT2PH.dhw.PHPP_DHW_Pipe_Segment()
    new_segment.length = segment.get('length')
    if segment.get('pipe_diameter'): new_segment.diameter = segment.get('pipe_diameter')
    if segment.get('insulation_thickness'): new_segment.insulation_thickness = segment.get('insulation_thickness')
    if segment.get('insulation_conductivity'): new_segment.insulation_conductivity = segment.get('insulation_conductivity')
    if segment.get('insulation_reflective'): new_segment.insulation_reflective = segment.get('insulation_reflective')
    if segment.get('insulation_quality'): new_segment.insulation_quality = segment.get('insulation_quality')
    if segment.get('daily_period'): new_segment.daily_period = segment.get('daily_period')
    
    circulation_piping_.append(new_segment)

# ------------------------------------------------------------------------------
for each in circulation_piping_:
    LBT2PH.helpers.preview_obj(each)