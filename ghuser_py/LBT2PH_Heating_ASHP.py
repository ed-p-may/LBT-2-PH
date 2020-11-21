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
Set the parameters for a Air- or Water-Source Heat Pump (HP). Sets the values on the 'HP' worksheet.
-
EM November 21, 2020
    Args:
        _unit_name: The name for the heat pump unit
        _source: The Heat Pump exterior 'source'. Input either:
> "1-Outdoor air"
> "2-Ground water"
> "3-Ground probes"
> "4-Horizontal ground collector"
        _fromPHPP: <Optional> If you prefer, you can just grab all the values from a PHPP or the 'Heat Pump Tool' from PHI and input here as a single element. Paste the values into a multiline component and connect to this input. The values will be separated by an invisible tab stop ("\t") which will be used to split the lines into the various columns. This is just an optional input to help make it easier. You can alwasys just use the direct entry inputs below if you prefer.
        _temps_source: (Deg C) List of test point values. List length should match the other inputs.
        _temps_sink: (Deg C) List of test point values. List length should match the other inputs.
        _heating_capacities: (kW) List of test point values. List length should match the other inputs.
        _COPs: (W/W) A list of the COP values at the various test points (source/sink). List length should match the other inputs.
        dt_sink_: (Deg C, Default = 5) A single temperature for the difference in sink. If using the 'Heat Pump Tool' from PHI, set this value to 0.
    Returns:
        heat_pump_: A Heat Pump object. Connect this output to the 'hp_heating_' input on a 'Heating/Cooling System' component.
"""

ghenv.Component.Name = "LBT2PH_Heating_ASHP"
ghenv.Component.NickName = "Heating | HP"
ghenv.Component.Message = 'NOV_21_2020'
ghenv.Component.IconDisplayMode = ghenv.Component.IconDisplayMode.application
ghenv.Component.Category = "PH-Tools"
ghenv.Component.SubCategory = "01 | Model"

import Grasshopper.Kernel as ghK

import LBT2PH
import LBT2PH.heating_cooling

reload( LBT2PH )
reload( LBT2PH.heating_cooling )

#-------------------------------------------------------------------------------
def check_input_lengths(*args):
    check_length = len(args[0])
    msg = 'Error: It looks like your input lists are not all the same length?\n'\
    'Check the input list lengths for _temp_source, _temps_sinks, _heating_capacities and _COPs inputs.'
    
    for list in args:
        if len(list) != check_length:
            ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, msg)
            return 0
    
    return 1

def parse_from_PHPP(_inputList):
    if not isinstance(_inputList, list):
        return None, None, None, None
    
    src, snk, hc, cop = [], [], [], []
    for line in _inputList:
        row = line.split('\t')
        src.append(row[0])
        snk.append(row[1])
        hc.append(row[2])
        cop.append(row[3])
    
    return src, snk, hc, cop

#-------------------------------------------------------------------------------
# First, try and use any copy/paste from PHPP
# Then, get any user inputs lists

list_lengths = check_input_lengths(_temps_source, _temps_sink, _heating_capacities, _COPs)
tsrcs, tsnks, hcs, cops = parse_from_PHPP(_fromPHPP)

if _temps_source:       tsrcs = _temps_source
if _temps_sink:         tsnks = _temps_sink
if _heating_capacities: hcs   = _heating_capacities
if _COPs:               cops  = _COPs
print tsrcs
#-------------------------------------------------------------------------------
# Create the Heat Pump Object

heat_pump_ = LBT2PH.heating_cooling.PHPP_HP_AirSource()
if _unit_name: heat_pump_.name = _unit_name
if _source: heat_pump_.source = _source
if tsrcs: heat_pump_.temps_sources = tsrcs
if tsnks: heat_pump_.temps_sinks = tsnks
if hcs: heat_pump_.heating_capacities = hcs
if cops: heat_pump_.cops = cops
if dt_sink_: heat_pump_.sink_dt = dt_sink_

for warning in heat_pump_.warnings:
    ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, warning)