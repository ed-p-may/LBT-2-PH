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
- 
Used to set up any 'Variants' desired in the output PHPP. The 'Variants' worksheet can contol the PHPP all from a single dashboard worksheet. This is useful when doing iterative studies and examining the impacts of varying assembly insulation levels, window products, etc.. To use, set the desired categories to 'True' to have this setup the PHPP to refer to the 'Variants' worksheet.
-
Note: You'll still have to set all the variants parameters in the PHPP 'Variants' worksheet either before or after writing out to the PHPP here. Best practice is to set up the 'source' PHPP with all the variant schemes and parameters desired before writing.
-
Note: For the 'ventilation_' input, use 'True' to set the ventilation system for a default PHPP. If you are using 
a modified PHPP (ie: added rows to the 'Additional Vent' worksheet, etc..) you can alternately input a list of 
values here in place of a boolean value. These values should correspond to to the:
    1) Ventilation Unit
    2) Duct Insualtion Thickness
    3) Duct Length

ie: if you have modified the number of rows on the 'Additional Vent' worksheet such that the Ventilation unit inputs now start on row 141 and the ducting inputs now start on row 171, you would use a multiline panel to enter:
    Additional Vent!F141=Variants!D856
    Additional Vent!H171=Variants!D858
    Additional Vent!H172=Variants!D858
    Additional Vent!L171=Variants!D857
    Additional Vent!L172=Variants!D857
in order to set the variant control for any a typical 2-duct ventilation system.
-
EM December 23, 2020
    Args:
        windows_: (bool) True = control Windows items to the Variants worksheet. Leave empty or set False to leave disconnected.
        u_values_: (bool) True = control U-Values items to the Variants worksheet. Leave empty or set False to leave disconnected.
        airtightness_: (bool) True = control Airtightness items to the Variants worksheet. Leave empty or set False to leave disconnected.
        thermal_bridges_: (bool) True = control Thermal Bridges items to the Variants worksheet. Leave empty or set False to leave disconnected.
        certification_: (bool) True = control Certification items to the Variants worksheet. Leave empty or set False to leave disconnected.
        primary_energy_: (bool) True = control Primary Energy (PER) items to the Variants worksheet. Leave empty or set False to leave disconnected.
        ----------
        ventilation_: (bool: str:) Leave empty or set False to NOT set connect ventilation items to the Variants worksheet. If set to True, will connect the Ventilation items using the 'standard' cell locations. BUT since the Additional Ventilation worksheet sometimes might change (you might add rows if you need more rooms for instance) you can also pass in text for the actual Excel formulas you'd like to write to the Variants worksheet.
    Returns:
        variants_: Connect to the 'LBT-->PHPP' 'variants_' input.
"""

ghenv.Component.Name = "LBT2PH_SetVariants"
ghenv.Component.NickName = "Variants"
ghenv.Component.Message = 'DEC_23_2020'
ghenv.Component.IconDisplayMode = ghenv.Component.IconDisplayMode.application
ghenv.Component.Category = "PH-Tools"
ghenv.Component.SubCategory = "02 | LBT2PH"

import LBT2PH
import LBT2PH.variants
from LBT2PH.helpers import preview_obj

reload(LBT2PH)
reload(LBT2PH.variants)

#-------------------------------------------------------------------------------
variants_ = LBT2PH.variants.Variants(ghenv)

if windows_:        variants_.windows = windows_
if u_values_:       variants_.u_values = u_values_
if airtightness_:   variants_.airtightness = airtightness_
if thermal_bridges_:variants_.thermal_bridges = thermal_bridges_
if certification_:  variants_.certification = certification_
if primary_energy_: variants_.primary_energy = primary_energy_
if ventilation_:    variants_.ventilation = ventilation_

#-------------------------------------------------------------------------------
preview_obj(variants_)