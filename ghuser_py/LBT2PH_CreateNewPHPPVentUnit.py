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
Collects and organizes data for a Ventilator Unit (HRV/ERV). Used to build up a PHPP-Style Ventilation System.
-
EM November 26, 2020
    Args:
        name_: <Optional> The name of the Ventilator Unit
        HR_Eff_: <Optional> Input the Ventialtion Unit's Heat Recovery %. Default is 75% 
        MR_Eff_: <Optional> Input the Ventialtion Unit's Moisture Recovery %. Default is 0% (HRV)
        Elec_Eff_: <Optional> Input the Electrical Efficiency of the Ventialtion Unit (W/m3h). Default is 0.45 W/m3h
    Returns:
        ventUnit_: A Ventilator object for the Ventilation System. Connect to the 'ventUnit_' input on the 'Create Vent System' to build a PHPP-Style Ventialtion System.
"""

ghenv.Component.Name = "LBT2PH_CreateNewPHPPVentUnit"
ghenv.Component.NickName = "Ventilator"
ghenv.Component.Message = 'NOV_26_2020'
ghenv.Component.IconDisplayMode = ghenv.Component.IconDisplayMode.application
ghenv.Component.Category = "PH-Tools"
ghenv.Component.SubCategory = "01 | Model"

import scriptcontext as sc
import LBT2PH
import LBT2PH.ventilation
import LBT2PH.helpers

reload(LBT2PH)
reload(LBT2PH.ventilation)
reload(LBT2PH.helpers)

def checkInput(_in):
    try:
        if float(_in) > 1:
            return float(_in) / 100
        else:
            return float(_in)
    except:
        return None

#------------------------------------------------------------------------------
ventUnit_ = LBT2PH.ventilation.PHPP_Sys_VentUnit()

if name_: 
    ventUnit_.name = name_
if checkInput(HR_eff_):
    ventUnit_.HR_eff = checkInput(HR_eff_) 
if checkInput(MR_eff_):
    ventUnit_.MR_eff = checkInput(MR_eff_) 
if elec_eff_:
    ventUnit_.elec_eff = elec_eff_
if frost_temp_:
    ventUnit_.frost_temp = LBT2PH.helpers.convert_value_to_metric(frost_temp_, 'C')
if exterior_:
    ventUnit_.exterior = 'x'

LBT2PH.helpers.preview_obj(ventUnit_)