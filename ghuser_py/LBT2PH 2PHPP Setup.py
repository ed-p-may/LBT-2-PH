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
Specify the inputs for 'Verification' and 'Climate' PHPP Worksheet items. Note 
that for climate, if you do not use this component then the LBT-->PHPP component 
will try and  automatically locate your building based on the EPW longitude and 
latitude. If you want to  specify the exact PHPP climate data set to use, you 
can do that with this component.
-
EM March 1, 2021
    Args:
        energyStandard_: <Optional> Input either:
            > "1-Passive House"
            > "2-EnerPHit"
            > "3-PHI Low Energy Building"
            > "4-Other"
        certification_class_: <Optional> Input either:
            > "1-Classic"
            > "2-Plus"
            > "3-Premium"
        primary_energy_: <Optional> Input either: 
            > "1-PE (non-renewable)"
            > "2-PER (renewable)"
        enerPHit_: <Optional> Input either: 
            > "1-Component method"
            > "2-Energy demand method"
        retrofit_: <Optional> Input either:
            > "1-New building"
            > "2-Retrofit"
            > "3-Step-by-step retrofit"
        
        buildingType_: <Optional> Input either: 
            > "1-Residential building"
            > "2-Non-residential building"
        ihgType_: <Optional> Internal Heat Gains Type. Input either: 
            > "10-Dwelling"
            > "11-Nursing home / students"
            > "12-Other"
            > "20-Office / Admin. building"
            > "21-School"
            > "22-Other"
        ighValues_: <Optional> Internal Heat Gains Source. 
            > For Residential, Input either: "2-Standard" or "3-PHPP calculation ('IHG' worksheet)"
            > For Non-Residential, input either: "2-Standard" or "4-PHPP calculation ('IHG non-res' worksheet)"
        thermalMass_: <Optional, Default=60>  Average Specific Heat Capacity (Wh/k-m2 TFA) of the building. 
            > Lightweight=60
            > Mixed=132
            > Heavy=204
        
        country_: <Optional, Default = 'US-United States of America	'>
        region_: <Options, Default = 'New York'>
        climateDataSet_: <Optional, Default='DE-9999-PHPP-Standard'> The name of the 
            PHPP climate data set to use. Just type in for now. Maybe a value-list someday...
        altitude_: <Optional, Default='=J23'> Altitude adjustment factor (m) for 
            the climate dataset. Default links to the weather station altidue loaded in the PHPP.
        
        _HB_model: The Honeybee Model
    Returns:
        HB_model_: 
"""

from datetime import datetime

import LBT2PH
import LBT2PH.__versions__
import LBT2PH.phpp_setup
import LBT2PH.climate
import LBT2PH.helpers

reload( LBT2PH )
reload(LBT2PH.__versions__)
reload( LBT2PH.phpp_setup )
reload( LBT2PH.climate )
reload( LBT2PH.helpers )

ghenv.Component.Name = "LBT2PH 2PHPP Setup"
LBT2PH.__versions__.set_component_params(ghenv, dev=False)

#-------------------------------------------------------------------------------
# Building Name from datetime
prefix = 'Bldg Data from Grasshopper'
suffix = datetime.now().strftime("%Y-%b-%d")
bldgName = '{} {}'.format(prefix, suffix)

#-------------------------------------------------------------------------------
# Verification Worksheet 
verification = LBT2PH.phpp_setup.PHPP_Verification()
verification.bldg_name = bldgName

if energy_standard_: verification.cert_standard = energy_standard_
if certification_class_: verification.cert_class = certification_class_
if primary_energy_: verification.pe = primary_energy_
if enerPHit_: verification.enerPHit = enerPHit_
if retrofit_: verification.retrofit = retrofit_
if thermalMass_: verification.spec_capacity = thermalMass_ 
if country_: verification.bldg_country = country_ 

#-------------------------------------------------------------------------------
# Climate Worksheet
climate = LBT2PH.climate.PHPP_ClimateDataSet()
if climateDataSet_: climate.DataSet = climateDataSet_ 
if altitude_: climate.Altitude = altitude_
if region_: climate.Region = region_
if country_: climate.Country = country_

LBT2PH.helpers.preview_obj( verification )
LBT2PH.helpers.preview_obj( climate )

#-------------------------------------------------------------------------------
# Add Setup and Climate dicts to the HB_Model.user_data
if _HB_model:
    HB_model_ = _HB_model.duplicate()
    
    setup = { verification.id:verification.to_dict() }
    climate = { climate.id:climate.to_dict() }
    HB_model_ = LBT2PH.helpers.add_to_HB_model(HB_model_, 'settings', setup, ghenv )
    HB_model_ = LBT2PH.helpers.add_to_HB_model(HB_model_, 'climate', climate, ghenv )
