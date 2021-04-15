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
Creates DHW Branch Piping set for the 'DHW+Distribution' PHPP worksheet.
-
EM April 15, 2021
    Args:
        pipe_segments_: list[float] (meters) | list[Rhino.Geometry.Curve] A list of branch piping elements. Accepts 
            either numeric values representing the lengths (m), or Polyline/Curve objects from Rhino.
        diameters_: list[float] (meters) The nominal size of the branch piping lengths. Default is 0.0127m (1/2").
    Returns:
        branch_piping_: [List] The Branch Piping object(s). Connect this to the 'branch_piping_' 
            input on the 'DHW' component in order to pass along to the PHPP.
"""

from itertools import izip_longest
import Grasshopper.Kernel as ghK
import rhinoscriptsyntax as rs

import LBT2PH
import LBT2PH.__versions__
import LBT2PH.dhw
import LBT2PH.dhw_IO
from LBT2PH.helpers import convert_value_to_metric, context_rh_doc

reload( LBT2PH )
reload( LBT2PH.__versions__ )
reload( LBT2PH.dhw )
reload( LBT2PH.dhw_IO )
reload( LBT2PH.helpers )

ghenv.Component.Name = "LBT2PH DHW Piping Branches"
LBT2PH.__versions__.set_component_params(ghenv, dev='APR_15_2021')

if diameters_ and  len(pipe_segments_) != len(diameters_):
    msg = 'Warning: Your diameters_ input length does not match the pipe_segments length.\n'\
        'I will use the default diameter for all missing inputs.'
    ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, msg)

#----- Build the standardized inputs
#-------------------------------------------------------------------------------
attr_dicts = []
for i, v in enumerate(pipe_segments_):
    attr_dict = {}
    attr_dict['pipe_diameter'] = diameters_[i] if i<len(diameters_) else None
    attr_dicts.append(attr_dict)

piping_inputs = LBT2PH.dhw_IO.piping_input_values(_input_node=0, _user_input=pipe_segments_, 
                                _user_attr_dicts=attr_dicts, _ghenv=ghenv, _ghdoc=ghdoc)

#---- Build the actual Piping Objects
#-------------------------------------------------------------------------------
branch_piping_ = []
for segment in piping_inputs:
    new_segment = LBT2PH.dhw.PHPP_DHW_Pipe_Segment()
    new_segment.length = segment.get('length')
    if segment.get('pipe_diameter'): new_segment.diameter = segment.get('pipe_diameter')
    
    branch_piping_.append(new_segment)

for each in branch_piping_:
    LBT2PH.helpers.preview_obj(each)