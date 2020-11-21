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
This component is used to create a simplified PHPP-Style Ventilation Schedule for a room or zone. Input values here for time of operation and fan speed for HIGH | MED | LOW modes.
> By entering reduction factors, full or reduced ventilation operation modes within the utilisation period can be considered. All of these attributes can be manually input using the Rhino-Scene PHPP tool 'Set TFA Surface Factor(s)'.
> All times % values should add up to 100%
-
EM November 21, 2020

    Args:
        _fanSpeed_high: Fan Speed factor (in %) in relation to the maximum volume flow when running at HIGH speed.
        _operationTime_high: Total operation time (in %) of HIGH SPEED ventilation mode in relation to the total. 
        _fanSpeed_med: Fan Speed factor (in %) in relation to the maximum volume flow when running at MEDIUM speed.
        _operationTime_med: Total operation time (in %) of MEDIUM SPEED ventilation mode in relation to the total.
        _fanSpeed_low: Fan Speed factor (in %) in relation to the maximum volume flow when running at LOW speed.
        _operationTime_low:Total operation time (in %) of LOW SPEED ventilation mode in relation to the total.
    Returns:
        phpp_ventilation_sched_: A PHPP Room Ventilation Schedule Object. Plug into the 'phpp_vent_schedule_' input on the 'PHPP Spaces' component.
"""

ghenv.Component.Name = "LBT2PH_CreateRoomVentSched"
ghenv.Component.NickName = "PHPP Vent Sched"
ghenv.Component.Message = 'NOV_21_2020'
ghenv.Component.IconDisplayMode = ghenv.Component.IconDisplayMode.application
ghenv.Component.Category = "PH-Tools"
ghenv.Component.SubCategory = "01 | Model"

from collections import namedtuple
import Grasshopper.Kernel as ghK

import LBT2PH
import LBT2PH.helpers
import LBT2PH.ventilation


reload(LBT2PH)
reload(LBT2PH.helpers)
reload(LBT2PH.ventilation)

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

def checkInputs(_in):
    total = _in._time_high + _in._time_med + _in._time_low
    if int(total) != 1:
        mssgLostRoom = "The Operation times don't add up to 100%? Please correct the inputs."
        ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, mssgLostRoom)

phpp_ventilation_sched_ = LBT2PH.ventilation.PHPP_Sys_VentSchedule(cleanGet(_fanSpeed_high, 1.0),
                            cleanGet(_operationTime_high, 1.0),
                            cleanGet(_fanSpeed_med, 0.77),
                            cleanGet(_operationTime_med, 0.0),
                            cleanGet(_fanSpeed_low, 0.4),
                            cleanGet(_operationTime_low, 0.0)
                            )

checkInputs( phpp_ventilation_sched_ )
LBT2PH.helpers.preview_obj(phpp_ventilation_sched_)