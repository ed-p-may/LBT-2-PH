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
Collects and organizes data for an Exhaust Ventilaiton Object such as a Kitchen
hood, fireplace makeup air, dryer, etc.
For guidance on modeling and design of exhaust air systems, see PHI's guidebook:
"https://passiv.de/downloads/05_extractor_hoods_guideline.pdf"
-
EM March 1, 2021
    Args:
        _name: (String) A Name to describe the Exhaust Vent item. This will be the name given in the 'Additional
        airFlowRate_On: <Optional> (Int) The airflow (m3/h) of the exhaust ventilation devide when ON.
            - PHI Recommened values: 'Efficient Equip.'=250m3/h, 'Standard Equip.'=450m3/h
            - Note: if you prefer, add 'cfm' to the input in order to supply values in IP units. 
            It'll convert this to m3/h before passing along to the PHPP
        airFlowRate_Off: <Optional> (Int) The airflow (m3/h) of the exhaust ventilation devide when OFF.
            - PHI Recommened values: 'Efficient Equip.'=2m3/h, 'Standard Equip.'=10m3/h
            - Note: if you prefer, add 'cfm' to the input in order to supply values in IP units. 
            It'll convert this to m3/h before passing along to the PHPP
        hrsPerDay_On: <Optional> (Float) The hours per day that the device operates. 
        For kitchen extract, assume 0.5 hours / day standard.
        daysPerWeek_On: <Optional> (Int) The days per weel that the devide is used. 
        For kitchen extract, assume 7 days / week standard.
    Returns:
        hrvDuct_: An Exhaust Ventilation Object. Input this into the 'exhaustVent_' 
            input on a 'Create Vent System' component.
"""

import scriptcontext as sc
import LBT2PH
import LBT2PH.__versions__
import LBT2PH.ventilation
import LBT2PH.helpers

reload(LBT2PH)
reload(LBT2PH.__versions__)
reload(LBT2PH.ventilation)
reload(LBT2PH.helpers)

ghenv.Component.Name = "LBT2PH Vent Exhaust Unit"
LBT2PH.__versions__.set_component_params(ghenv, dev=False)

#-------------------------------------------------------------------------------

defaultDuct = LBT2PH.ventilation.PHPP_Sys_Duct(_duct_input=[1])
exhaustVent_ = LBT2PH.ventilation.PHPP_Sys_ExhaustVent()
if _name:
    exhaustVent_.name = _name
if airFlowRate_On:
    exhaustVent_.airFlowRate_On = LBT2PH.helpers.convert_value_to_metric(airFlowRate_On, 'M3/H')
if airFlowRate_Off:
    exhaustVent_.airFlowRate_Off = LBT2PH.helpers.convert_value_to_metric(airFlowRate_Off, 'M3/H')
if hrsPerDay_On:
    exhaustVent_.hrsPerDay_On = hrsPerDay_On
if daysPerWeek_On:
    exhaustVent_.daysPerWeek_On = daysPerWeek_On
if defaultDuct:
    exhaustVent_.default_duct = defaultDuct

LBT2PH.helpers.preview_obj(exhaustVent_)