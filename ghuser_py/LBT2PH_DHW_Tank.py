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
Creates DHW Tank for the 'DHW+Distribution' PHPP worksheet.
-
EM November 21, 2020
    Args:
        _tank_type: ("0-No storage tank", "1-DHW and heating", "2-DHW only") The type of use for this tank.
        tank_solar_: (True/False) Is this tank hooked up to a Solar HW system?
        tank_HLrate_: (W/k) Heat Loss rate from the tank. Default is 4.0 W/k
        tank_volume_: (litres) Nominal tank volume. Default is 300 litres (80 gallons)
        tank_standby_frac_: (%) The Standby Fraction. Default is 0.30 (30%)
        tank_location_: ("1-Inside", "2-Outside") The location of this HW tank.
        tank_location_T_: (Deg C) The avg air-temp of the tank location if outside the building. 
    Returns:
        tank_location_T_: A DHW Tank Object. Connect this to one of the 'tank_' inputs on the 'DHW System' component in order to pass along to the PHPP.
"""

ghenv.Component.Name = "LBT2PH_DHW_Tank"
ghenv.Component.NickName = "DHW Tank"
ghenv.Component.Message = 'NOV_21_2020'
ghenv.Component.IconDisplayMode = ghenv.Component.IconDisplayMode.application
ghenv.Component.Category = "PH-Tools"
ghenv.Component.SubCategory = "01 | Model"

import scriptcontext as sc
import Grasshopper.Kernel as ghK
import LBT2PH
import LBT2PH.dhw

reload( LBT2PH )
reload( LBT2PH.dhw )

# Classes and Defs
def cleanInputs(_in, _nm, _default):
    # Apply defaults if the inputs are Nones
    out = _in if _in != None else _default
    
    # Check that output can be float
    if out:
        try:
            out = float(out)
            # Check units
            if _nm == "tank_standby_frac_":
                if out > 1:
                    unitWarning = "Standby Units should be decimal fraction. ie: 30% should be entered as 0.30" 
                    ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, unitWarning)
                    return out/100
            return out
        except:
            ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, '"{}" input should be a number'.format(_nm))
            return out

def clean_type(_type):
    # Clean Inputs
    if _type == None:
        return "0-No storage tank"
    else:
        try:
            if "1" == str(_type)[0]:
                return "1-DHW and heating"
            elif "2" == str(_type)[0]:
                return "2-DHW only"
            elif "0" == str(_type)[0]:
                return "0-No storage tank"
            else:
                raise Exception()
        except Exception:
            ttypeWarning = 'Please enter either "0-No storage tank", "1-DHW and heating", "2-DHW only" for the "_tank_type input"'
            ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, ttypeWarning)
            return "0-No storage tank"

def clean_location(_in):
    # Clean Inputs
    if _in == None:
        return "1-Inside"
    else:
        try:
            if "1" == str(_in)[0]:
                return "1-Inside"
            elif "2" == str(_in)[0]:
                return "2-Outside"
            else:
                raise Exception()
        except Exception:
            ttypeWarning = 'Please enter either "1-Inside" or "2-Outside" for the "tank_location_ input"'
            ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, ttypeWarning)
            return "1-Inside"

# Clean Inputs and defaults
ttype = clean_type(_tank_type)
solar = tank_solar_ if tank_solar_==True else False
hlRate = cleanInputs(tank_HLrate_, 'tank_HLrate_', 4)
vol = cleanInputs(tank_volume_, 'tank_volume_', 300)
stndBy = cleanInputs(tank_standby_frac_, 'tank_standby_frac_', 0.30)
loc = clean_location(tank_location_)
locT = cleanInputs(tank_location_T_, 'tank_location_T_', '')

# Creat Storage Tank
storage_tank_ = LBT2PH.dhw.PHPP_DHW_tank(ttype, solar, hlRate, vol, stndBy, loc, locT )
