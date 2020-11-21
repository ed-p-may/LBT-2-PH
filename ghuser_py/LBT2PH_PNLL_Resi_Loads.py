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
This component stores a library of values (Loads and Schedules) which match the typical Single Family (SF) residential loads found in the PNNL sample IDF files provided by the U.S. Dept of Energy. These sample files can be found online at https://www.energycodes.gov/development/residential/iecc_models all values here are from the 2018 IECC, Zone 4a IDF Sampe file.
-
EM November 21, 2020

    Args:
        _HBZones: Honeybee Zones to apply this leakage rate to. Note, this should be the set of all the zones which were tested together as part of a Blower Door test. IE: if the blower door test included Zones A, B, and C then all three zones should be passed in here together. Use 'Merge' to combine zones if need be.
        refrigerator_: (W) Default = 91.058
        dishwasher_: (W) Default = 65.699
        clothesWasher_: (W) Default = 28.478 
        clothesDryer_: (W) Default = 213.065
        range_: (W) Default = 248.154
        mel_: (W) Default = 1.713
        plugLoads_: (W) Default = 1.544 
    Returns:
        _HBZones:
        PNNL_ElecEquip_Load_: (W/m2) Connect this the 'equipmentLoadPerArea_' input on a Honeybee 'setEPZoneLoads' Component
        PNNL_Lighting_Load_: (W//m2) Connect this the 'lightingDensityPerArea_' input on a Honeybee 'setEPZoneLoads' Component
        PNNL_Occup_Load_: (PPL/m2) Connect this the 'numOfPeoplePerArea_' input on a Honeybee 'setEPZoneLoads' Component
        PNNL_SF_Occup_Sched_: (Fractional) Hourly values (24). Connect these to the inputs on a new Honeybee 'AnnualSchedule' Component. Set the '_schedTypeLimits' to 'Fraction'. Connect this new schedule to the 'occupancySchedules_' input on a Honeybee 'setEPZoneSchedules' Component.
        PNNL_SF_Lighting_Sched_: (Fractional) Hourly values (24). Connect these to the inputs on a new Honeybee 'AnnualSchedule' Component. Set the '_schedTypeLimits' to 'Fraction'. Connect this new schedule to the 'lightingSchedules_' input on a Honeybee 'setEPZoneSchedules' Component.
        PNNL_ElecEquip_Sched_: (Fractional) Hourly values (24). Connect these to the inputs on a new Honeybee 'AnnualSchedule' Component. Set the '_schedTypeLimits' to 'Fraction'. Connect this new schedule to the 'equipmentSchedules_' input on a Honeybee 'setEPZoneSchedules' Component.
"""

ghenv.Component.Name = "LBT2PH_PNLL_Resi_Loads"
ghenv.Component.NickName = "PNLL Resi Loads & Schedules"
ghenv.Component.Message = 'NOV_21_2020'
ghenv.Component.IconDisplayMode = ghenv.Component.IconDisplayMode.application
ghenv.Component.Category = "PH-Tools"
ghenv.Component.SubCategory = "01 | Model"

import scriptcontext as sc

def calcElecEquip():
    # ------------------------------------------------------------------------------
    # Get the HB Zone Floor Area values
    totalSF = 0
    for zone in HBZoneObjects:
        for srfc in zone.surfaces:
            if srfc.type in [2, 2.25, 2.5, 2.75]:
                totalSF+=srfc.getTotalArea()
    
    # ------------------------------------------------------------------------------
    # Electric Equipment Load
    load_ref, load_dw, load_cw, load_cd, load_r, load_mel, load_pl = elec_equip_defalts()
    
    wattHr_ref = [load_ref * hour for hour in sched_ref]
    wattHr_dw = [load_dw * hour for hour in sched_dw]
    wattHr_clWsh = [load_cw * hour for hour in sched_washer]
    wattHr_dryer = [load_cd * hour for hour in sched_dryer]
    wattHr_stove = [load_r * hour for hour in sched_stove]
    wattHr_mel = [load_mel * hour * totalSF for hour in sched_mels]
    wattHr_pl = [load_pl * hour * totalSF for hour in sched_plugLoads]
    
    hourlyTotalW = []
    for i in range(24):
        hourlyTotalW.append(wattHr_ref[i] + wattHr_dw[i] + wattHr_clWsh[i] + wattHr_dryer[i] + wattHr_stove[i] + wattHr_mel[i] + wattHr_pl[i])
    
    peakHourlyW = max( hourlyTotalW )
    PNNL_ElecEquip_Load = peakHourlyW / totalSF
    PNNL_ElecEquip_Sched = [hourlyWattage / peakHourlyW for hourlyWattage in hourlyTotalW]
    
    return PNNL_ElecEquip_Load, PNNL_ElecEquip_Sched

def elec_equip_defalts():
    # Default Values taken from PNNL Sample SF Residential IDF file
    # https://www.energycodes.gov/development/residential/iecc_models
    
    ref = refrigerator_ if refrigerator_ else 91.058
    dw = dishwasher_ if dishwasher_ else 65.699
    cwash = clothesWasher_ if clothesWasher_ else 28.478
    cdry = clothesDryer_ if clothesDryer_ else 213.065
    cooktop = range_ if range_ else 248.154
    mel = mel_ if mel_ else 1.713
    pl = plugLoads_ if plugLoads_ else 1.544
    return ref, dw, cwash, cdry, cooktop, mel, pl

# ------------------------------------------------------------------------------
# Fraction Schedules from PNNL Example IDF Files
# https://www.energycodes.gov/development/residential/iecc_models
sched_ref = [0.80,0.78,0.77,0.74,0.73,0.73,0.76,0.80,0.82,0.83,0.80,0.80,0.84,0.84,0.83,0.84,0.89,0.97,1.00,0.97,0.94,0.93,0.89,0.83]
sched_dw = [0.12,0.05,0.04,0.03,0.03,0.08,0.15,0.23,0.44,0.49,0.43,0.36,0.31,0.35,0.28,0.27,0.28,0.37,0.66,0.84,0.68,0.50,0.33,0.23]
sched_washer = [0.08,0.06,0.03,0.03,0.06,0.10,0.19,0.41,0.62,0.73,0.72,0.64,0.57,0.51,0.45,0.41,0.43,0.41,0.41,0.41,0.41,0.40,0.27,0.14]
sched_dryer = [0.10,0.06,0.04,0.02,0.04,0.06,0.16,0.32,0.49,0.69,0.79,0.82,0.75,0.68,0.61,0.58,0.56,0.55,0.52,0.51,0.53,0.55,0.44,0.24]
sched_stove = [0.05,0.05,0.02,0.02,0.05,0.07,0.17,0.28,0.31,0.32,0.28,0.33,0.38,0.31,0.29,0.38,0.61,1.00,0.78,0.40,0.24,0.17,0.10,0.07]
sched_mels = [0.61,0.56,0.55,0.55,0.52,0.59,0.68,0.72,0.61,0.52,0.53,0.53,0.52,0.54,0.57,0.60,0.71,0.86,0.94,0.97,1.00,0.98,0.85,0.73]
sched_plugLoads = [0.61,0.56,0.55,0.55,0.52,0.59,0.68,0.72,0.61,0.52,0.53,0.53,0.52,0.54,0.57,0.60,0.71,0.86,0.94,0.97,1.00,0.98,0.85,0.73]
PNNL_SF_Occup_Sched_=[1.00000,1.00000,1.00000,1.00000,1.00000,1.00000,1.00000,0.88310,0.40861,0.24189,0.24189,0.24189,0.24189,0.24189,0.24189,0.2418,0.29498,0.55310,0.89693,0.89693,0.89693,1.00000,1.00000,1.00000]
PNNL_SF_Lighting_Sched_ =[0.06875,0.06875,0.0687,0.06875,0.20625,0.4296875,0.48125,0.4296875,0.1890625,0.12890625,0.12890625,0.12890625,0.12890625,0.12890625,0.12890625,0.2234375,0.48125,0.6703125,0.90234375,1,1,0.75625,0.42109375,0.171875]

# ------------------------------------------------------------------------------
# Lighting Load
# 1.15 W/m2 (Hardwired)  + 0.48 W/m2 (Plugin) = 1.63 W/,2
PNNL_Lighting_Load_ = 1.15 + 0.48

# ------------------------------------------------------------------------------
# Occupancy (People / m2)
PNNL_Occup_Load_ = 0.0091 

# ------------------------------------------------------------------------------
# Electric Equipment
if _HBZones:
    hb_hive = sc.sticky["honeybee_Hive"]()
    HBZoneObjects = hb_hive.callFromHoneybeeHive(_HBZones)
    PNNL_ElecEquip_Load_, PNNL_ElecEquip_Sched_ = calcElecEquip()
    HBZones_ = _HBZones