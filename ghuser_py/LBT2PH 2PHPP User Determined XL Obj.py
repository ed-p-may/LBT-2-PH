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
For writing a user-determined custom value to any range on any worksheet. Be 
careful with this! It'll let you write anyplace in the Excel workbook - be cautious 
not to accidentaly overwrite an important formula in the PHPP or cause some 
other unintendded error.
-
EM March 1, 2021
    Args:
        _worksheetName: (list) Worksheet names for the data to be writen to. Be 
            sure these match the Worksheet names in the Excel document exactly.
        _rangeAddress: list) Cell Ranges to write to. Should be Excel style 
            ('A1', 'B23', 'AA45', etc...)
        _rangeValue: (list) The actual values to write to the Cell Ranges listed in _rangeAddress. 
    Returns:
        toPHPP_UD_: A DataTree of the final clean, Excel-Ready output objects.
            Each output object has a Worksheet-Name, a Cell Range, and a Value. 
            Connect to the 'UserDefined_' input on the 'Write 2PHPP' Component 
            to write to Excel.
"""

import Grasshopper.Kernel as ghK
from itertools import izip_longest
from collections import namedtuple

import LBT2PH
import LBT2PH.__versions__

reload(LBT2PH)
reload(LBT2PH.__versions__)

ghenv.Component.Name = "LBT2PH 2PHPP User Determined XL Obj"
LBT2PH.__versions__.set_component_params(ghenv, dev=False)

#-------------------------------------------------------------------------------

def display_error(r, v):
    msg = '"_range_addresses" [{}] and "_range_values" [{}] inputs must all be the same\n'\
    'length. Check the inputs and try again.'.format(r, v)
    ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Error, msg )

UD_Write = namedtuple('UD_Write', ['worksheet', 'range', 'value'])
ud_custom_ = []

if _worksheet_names and _range_addresses and _range_values:
    max_len = max(len(_range_addresses), len(_range_values))
    if len(_worksheet_names) != max_len:
        worksheet_names = [ _worksheet_names[0] ]*max_len
    else:
        worksheet_names = _worksheet_names
    
    if len(_range_addresses) != len(_range_values):
        display_error(len(_range_addresses), len(_range_values))
    
    else:
        for w, r, v in izip_longest(worksheet_names, _range_addresses, _range_values):
            ud_custom_.append( UD_Write(w, r, v) )