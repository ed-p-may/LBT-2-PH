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
Collects and organizes data for simple heating / cooling equipment. Outputs a 
'Heating_Cooling' and 'PER' class object with all the data organized and keyed.
-
EM March 1, 2021
    Args:
        primaryHeatGeneration_: <Optional, Default='5-Direct electricity'> The 
            type of heating equipment to use for the 'Primary' heating. Input either:
            >  1-HP compact unit
            >  2-Heat pump(s)
            >  3-District heating, CGS
            >  4-Heating boiler
            >  5-Direct electricity
            >  6-Other
        secondaryHeatGeneration_: <Optional, Default='-'> The type of heating 
            equipment to use for the 'Secondary' heating. Input either:
            >  1-HP compact unit
            >  2-Heat pump(s)
            >  3-District heating, CGS
            >  4-Heating boiler
            >  5-Direct electricity
            >  6-Other
            -
            Leave blank if no secondary heat generation equipment is used.
        heatingFracPrimary_: <Optional, Default=100%> A number from 0-1. The percentage 
            of Heating energy that comes from the 'Primary' heater. The rest will 
            come from the 'Secondary' heater.
        dhwFracPrimary_: <Optional, Default=100%> A number from 0-1. The percentage 
            of DHW Energy that comes from the 'Primary' heater. The rest will come 
            from the 'Secondary' heater.
        mech_cooling_: (bool) Default=False. This turns mechanical cooling (ac) 'on'. 
            Leave blank or set False to have mechanical cooling 'off' in the PHPP model. 
            Set TRUE in order to turn active cooling 'on'.
        
        boiler_: <Optional, Default=None> A typical hot water Boiler system parameters. 
            Connect to the 'Heating:Boiler' Component.
        hp_heating_: <Optional, Default=None> Heat Pump unit for space heating
        hp_DHW_: <Optional, Default=None> Heat Pump unit for Domestic Hot Water (DHW)
        hpGround_: <Optional, Default=None> Not implemented yet....
        compact_: <Optional, Default=None> Not implemented yet....
        distictHeating_: <Optional, Default=None> Not implemented yet....
        supplyAirCooling_: <Optional, Default=None> A 'Supply Air' cooling system. 
            Providing cooling through the ventilation (HRV) air flow.
        recircAirCooling_: <Optional, Default=None> A normal AC system parameters. 
            Connect to the 'Cooling:Recirc' Component.
        addnlDehumid_: <Optional, Default=None> An Additional Dehumidification element. 
        panelCooling_: <Optional, Default=None> Not implemented yet....
    Returns:
        HB_rooms_: DataTree. Branch 1 is all the 'PER' related information 
            (heating fractions). Branch 2 is all the Heating / Cooling Equipment
            related data. Connect to the 'Heating_Cooling_' input on the '2PHPP | Setup' Component.
"""

import Grasshopper.Kernel as ghK

import LBT2PH
import LBT2PH.__versions__
import LBT2PH.helpers
import LBT2PH.heating_cooling

reload( LBT2PH )
reload(LBT2PH.__versions__)
reload( LBT2PH.helpers )
reload( LBT2PH.heating_cooling )

ghenv.Component.Name = "LBT2PH Heating Systems"
LBT2PH.__versions__.set_component_params(ghenv, dev=False)

#-------------------------------------------------------------------------------
# Build PER Object
per_obj = LBT2PH.heating_cooling.PHPP_PER()
if primary_heat_generation_: per_obj.primary_heat = primary_heat_generation_
if secondary_heat_generation_: per_obj.secondary_heat = secondary_heat_generation_
if heating_frac_primary_: per_obj.primary_heat_frac = heating_frac_primary_
if dhw_frac_primary_: per_obj.dhw_frac = dhw_frac_primary_
if mech_cooling_: per_obj.mech_cooling = mech_cooling_

hc = {}
hc.update( {'use_mech_cooling':mech_cooling_} )

# Heat Pump bits
if hp_heating_: hc.update( {'hp_heating'   :hp_heating_.to_dict()} )
if hp_DHW_:     hc.update( {'hp_DHW_'      :hp_DHW_.to_dict()} )
if hp_ground_:  hc.update( {'hp_ground_'   :hp_ground_.to_dict()} )
if hp_options_: hc.update( {'hp_options_'  :hp_options_.to_dict()} )

# Other Crap
if boiler_: hc.update( { 'boiler':boiler_.to_dict()} )
if compact_:     hc.update( { 'compact':compact_.to_dict()} )
if distict_heating_:  hc.update( {'distict_heating':distict_heating_.to_dict()} )
if supply_air_cooling_: hc.update( {'supply_air_cooling':supply_air_cooling_.to_dict()} )
if recirc_air_cooling_: hc.update( {'recirc_air_cooling':recirc_air_cooling_.to_dict()} )
if addnl_dehumid_:     hc.update( {'addnl_dehumid':addnl_dehumid_.to_dict()} )
if panel_cooling_:  hc.update( {'panel_cooling':panel_cooling_.to_dict()} )


#-------------------------------------------------------------------------------
# Add the new objects onto the Honeybee Rooms
HB_rooms_ = []
per_dict = { per_obj.id:per_obj.to_dict() }
for hb_room in _HB_rooms:
    new_room = hb_room.duplicate()
    new_room = LBT2PH.helpers.add_to_HB_model(hb_room, 'PER', per_dict, ghenv, 'overwrite' )
    new_room = LBT2PH.helpers.add_to_HB_model(hb_room, 'heating_cooling', hc, ghenv, 'overwrite' )
    
    HB_rooms_.append( new_room )


#Give warnings
#-------------------------------------------------------------------------------
if not mech_cooling_:
    if supply_air_cooling_ or recirc_air_cooling_ or addnl_dehumid_ or panel_cooling_:
        msg = 'It looks like you have cooling equipment hoooked up but you do not\n'\
        'have mechanical cooling enabled? If you want to use this equipment to provide\n'\
        'cooling (AC) be sure to set "mech_cooling" to TRUE.'
        ghenv.Component.AddRuntimeMessage( ghK.GH_RuntimeMessageLevel.Warning, msg )
else:
    if not supply_air_cooling_ and not recirc_air_cooling_ and not addnl_dehumid_ and not panel_cooling_:
        msg = 'It looks like you do not have cooling equipment hoooked up but you do \n'\
        'have mechanical cooling enabled? If you want to provide active cooling, be sure to\n'\
        'to hook up at least one piece of active cooling equipment.'
        ghenv.Component.AddRuntimeMessage( ghK.GH_RuntimeMessageLevel.Warning, msg )