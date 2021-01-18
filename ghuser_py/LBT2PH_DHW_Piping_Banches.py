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
EM December 9, 2020
    Args:
        pipe_geom_: (Lsit: Curves:) A list of recirculation piping elements. Accepts either numeric values representing the lenghts, or Curve objects from Rhino.
        diameter_: (m) The nominal size of the branch piping lengths. Default is 0.0127m (1/2").
        tapOpenings_: The number of tap openings / person every day. Default is 6 openings/person/day.
        utilisation_: The days/year the DHW system is operational. Default is 365 days/year.
    Returns:
        branch_piping_: The Branch Piping object(s). Connect this to the 'branch_piping_' input on the 'DHW' component in order to pass along to the PHPP.
"""

ghenv.Component.Name = "LBT2PH_DHW_Piping_Banches"
ghenv.Component.NickName = "Piping | Branches"
ghenv.Component.Message = 'DEC_09_2020'
ghenv.Component.IconDisplayMode = ghenv.Component.IconDisplayMode.application
ghenv.Component.Category = "PH-Tools"
ghenv.Component.SubCategory = "01 | Model"

import LBT2PH
from LBT2PH.helpers import convert_value_to_metric
from LBT2PH.dhw import PHPP_DHW_branch_piping
from LBT2PH.dhw import clean_input

reload( LBT2PH )
reload( LBT2PH.dhw )
reload( LBT2PH.helpers )

# ------------------------------------------------------------------------------
branch_piping_ = PHPP_DHW_branch_piping()

if pipe_geom_:
    branch_piping_.set_pipe_lengths(pipe_geom_, ghdoc, ghenv)
    
    if diameter_:
        branch_piping_.diameter = clean_input(diameter_, "diameter_", 'M', ghenv)
    if tap_openings_:
        branch_piping_.tap_openings = clean_input(tap_openings_, "tapOpenings_", '-', ghenv)
    if utilisation_:
        branch_piping_.utilisation = clean_input(utilisation_, "utilisation_", '-', ghenv)

LBT2PH.helpers.preview_obj(branch_piping_)