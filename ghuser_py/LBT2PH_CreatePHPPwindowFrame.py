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
Will combine parameters together to create a new Window Frame object which can be used by the 'PHPP Apertures' component. A PHPP-Style frame includes very detailed information.
-
EM November 26, 2020
    Args:
        _name: The name for the new Window Frame object
        _frameWidths: (List) Input values for the frame face-widths (m). Input values in order: Left, Right, Bottom, Top. If less than 4 values are input, the first value will be used for all four edges.
        _frameUvalues: (List) Input values for the frame U-Values (W/m2-k). Frame U-values to be calculated as per ISO-10077-2. Input values in order: Left, Right, Bottom, Top. If less than 4 values are input, the first value will be used for all four edges.
        _psiGlazings: (List) Input values for the Psi-GlazingEdge Values (W/m-k). Frame Psi-GlazingEdge values to be calculated as per ISO-10077-2. Input values in order: Left, Right, Bottom, Top. If less than 4 values are input, the first value will be used for all four edges.
        _psiInstalls: (List) Input values for the Psi-Install Values (W/m-k). Frame Psi-Install values to be calculated as per ISO 10211. Input values in order: Left, Right, Bottom, Top. If less than 4 values are input, the first value will be used for all four edges.
    Returns:
        PHPPFrame_: A new PHPP-Style Frame Object for use in a PHPP Window. Connect to the 'PHPP Apertures' Component.
"""

ghenv.Component.Name = "LBT2PH_CreatePHPPwindowFrame"
ghenv.Component.NickName = "New PHPP Frame"
ghenv.Component.Message = 'NOV_26_2020'
ghenv.Component.IconDisplayMode = ghenv.Component.IconDisplayMode.application
ghenv.Component.Category = "PH-Tools"
ghenv.Component.SubCategory = "01 | Model"

import LBT2PH
import LBT2PH.windows
import LBT2PH.helpers

reload(LBT2PH)
reload(LBT2PH.windows)
reload(LBT2PH.helpers)

def cleanInputs(_inputList, defaultValue, _unit):
    
    if len(_inputList)==4:
        return [LBT2PH.helpers.convert_value_to_metric(val, _unit) for val in _inputList]
    elif len(_inputList)==1:
        val = LBT2PH.helpers.convert_value_to_metric(_inputList[0], _unit)
        return [val]*4
    else:
        return [defaultValue]*4

if _name:
    PHPPFrame_ = LBT2PH.windows.PHPP_Frame()
    
    if _name: PHPPFrame_.name = _name.replace(" ", "_")
    if _frameUvalues: PHPPFrame_.uValues = cleanInputs(_frameUvalues, 1.0, 'W/M2K')
    if _frameWidths: PHPPFrame_.frameWidths = cleanInputs(_frameWidths, 0.12, 'M')
    if _psiGlazings: PHPPFrame_.PsiGVals = cleanInputs(_psiGlazings, 0.04 , 'W/MK')
    if _psiInstalls: PHPPFrame_.PsiInstalls = cleanInputs(_psiInstalls, 0.04, 'W/MK')
    if _chi_glass_carriers: PHPPFrame_.chiGlassCarrier = LBT2PH.helpers.convert_value_to_metric(_chi_glass_carriers, 'W/K')