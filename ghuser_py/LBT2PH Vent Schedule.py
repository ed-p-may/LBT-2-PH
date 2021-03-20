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
This component is used to create a simplified PHPP-Style Ventilation Schedule for 
a room or zone. Input values here for time of operation and fan speed for HIGH 
| MED | LOW modes.
> By entering reduction factors, full or reduced ventilation operation modes 
within the utilisation period can be considered. All of these attributes can 
be manually input using the Rhino-Scene PHPP tool 'Set TFA Surface Factor(s)'.
> All times % values should add up to 100%
-
EM March 20, 2021

    Args:
        _fanSpeed_high: Fan Speed factor (in %) in relation to the maximum volume 
            flow when running at HIGH speed.
        _operationTime_high: Total operation time (in %) of HIGH SPEED ventilation
            mode in relation to the total.
        _fanSpeed_med: Fan Speed factor (in %) in relation to the maximum volume 
            flow when running at MEDIUM speed.
        _operationTime_med: Total operation time (in %) of MEDIUM SPEED ventilation 
            mode in relation to the total.
        _fanSpeed_low: Fan Speed factor (in %) in relation to the maximum volume 
            flow when running at LOW speed.
        _operationTime_low:Total operation time (in %) of LOW SPEED ventilation 
            mode in relation to the total.
    Returns:
        phpp_ventilation_sched_: A PHPP Room Ventilation Schedule Object. Plug 
            into the 'phpp_vent_schedule_' input on the 'PHPP Spaces' component.
"""

import Grasshopper.Kernel as ghK

import LBT2PH
import LBT2PH.__versions__
import LBT2PH.helpers
import LBT2PH.ventilation

reload(LBT2PH)
reload(LBT2PH.__versions__)
reload(LBT2PH.helpers)
reload(LBT2PH.ventilation)

ghenv.Component.Name = "LBT2PH Vent Schedule"
LBT2PH.__versions__.set_component_params(ghenv, dev='MAR_20_2021')
#-------------------------------------------------------------------------------

def cleanGet(_in, _default=None):
    # Clean up the inputs
    # Turn into decimal if >1
    try:
        result = float(_in)
        if result > 1:
            result = result / 100
        
        return result
    except:
        return _default

phpp_ventilation_sched_ = LBT2PH.ventilation.PHPP_Sys_VentSchedule()

# Have to check is non None cus' if you want to pass 0 ever...
if _fan_speed_high is not None: phpp_ventilation_sched_.speed_high = _fan_speed_high
if _fan_speed_med is not None:  phpp_ventilation_sched_.speed_med = _fan_speed_med
if _fan_speed_low is not None:  phpp_ventilation_sched_.speed_low = _fan_speed_low

if _operation_time_high is not None: phpp_ventilation_sched_.time_high = cleanGet(_operation_time_high)
if _operation_time_med is not None:  phpp_ventilation_sched_.time_med = cleanGet(_operation_time_med)
if _operation_time_low is not None:  phpp_ventilation_sched_.time_low = cleanGet(_operation_time_low)

msg = phpp_ventilation_sched_.check_total()
if msg:
    ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, msg)

LBT2PH.helpers.preview_obj(phpp_ventilation_sched_)