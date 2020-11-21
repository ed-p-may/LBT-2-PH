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
Will calculate the PHPP Envelope Airtightness using the PHPP Rooms as the reference volume. Connect the ouputs from this component to a Honeybee 'setEPZoneLoads' and then set the Infiltration Schedule to 'CONSTANT'. Use a Honeybee 'Constant Schedule' with a value of 1 and a _schedTypeLimit of 'FRACTIONAL', then connect that to an HB 'setEPZoneSchdeules' component.
-
Note: The results shown here will be a fair bit different than the Honeybee 'ACH2m3/s-m2 Calculator' standard component because for PH Cert we are supposed to use the Net Internal Volume (v50) NOT the gross volume. E+ / HB use the gross volume and so given the same ACH, they will arrive at different infiltration flow rates (flow = ACH * Volume). For PH work, use this component.
-
EM Nov. 21, 2020

    Args:
        _HBZones: Honeybee Zones to apply this leakage rate to. Note, this should be the set of all the zones which were tested together as part of a Blower Door test. IE: if the blower door test included Zones A, B, and C then all three zones should be passed in here together. Use 'Merge' to combine zones if need be.
        _n50: (ACH) The target ACH leakage rate
        _q50: (m3/hr-m2-surface) The target leakage rate per m2 of exposed surface area
        _blowerPressure: (Pascal) Blower Door pressure for the airtightness measurement. Default is 50Pa
    Returns:
        _HBZones: Connect to the '_HBZones' input on the Honeybee 'setEPZoneLoads' Component
        infiltrationRatePerFloorArea_: (m3/hr-m2-floor)
        infiltrationRatePerFacadeArea_: (m3/hr-m2-facade) Connect to the 'infilRatePerArea_Facade_' input on the Honeybee 'setEPZoneLoads' Component
"""

ghenv.Component.Name = "LBT2PH_Airtightness"
ghenv.Component.NickName = "Airtightness"
ghenv.Component.Message = 'NOV_21_2020'
ghenv.Component.IconDisplayMode = ghenv.Component.IconDisplayMode.application
ghenv.Component.Category = "PH-Tools"
ghenv.Component.SubCategory = "01 | Model"

try:
    from honeybee_energy.load.infiltration import Infiltration
except ImportError as e:
    raise ImportError('\nFailed to import honeybee_energy:\n\t{}'.format(e))

import Grasshopper.Kernel as ghK

import LBT2PH.helpers
import LBT2PH.spaces
import LBT2PH.ventilation
import LBT2PH.airtightness

reload(LBT2PH)
reload(LBT2PH.helpers)
reload(LBT2PH.spaces)
reload(LBT2PH.ventilation)
reload(LBT2PH.airtightness)

# ------------------------------------------------------------------------------
# These defs are from Honeybee 'ApplyLoadVals' component
def dup_load(hb_obj, object_name, object_class):
    """Duplicate a load object assigned to a Room or ProgramType."""
    # try to get the load object assgined to the Room or ProgramType
    try:  # assume it's a Room
        load_obj = hb_obj.properties
        for attribute in ('energy', object_name):
            load_obj = getattr(load_obj, attribute)
    except AttributeError:  # it's a ProgramType
        load_obj = getattr(hb_obj, object_name)

    load_id = '{}_{}'.format(hb_obj.identifier, object_name)
    try:  # duplicate the load object
        dup_load = load_obj.duplicate()
        dup_load.identifier = load_id
        return dup_load
    except AttributeError:  # create a new object
        try:  # assume it's People, Lighting, Equipment or Infiltration
            return object_class(load_id, 0, always_on)
        except:  # it's a Ventilation object
            return object_class(load_id)

def assign_load(hb_obj, load_obj, object_name):
    """Assign a load object to a Room or a ProgramType."""
    try:  # assume it's a Room
        setattr(hb_obj.properties.energy, object_name, load_obj)
    except AttributeError:  # it's a ProgramType
        setattr(hb_obj, object_name, load_obj)

# Clean up inputs
n50 = _n50 if _n50 else None # ACH
q50 = _q50 if _q50 else None # m3/m2-facade
blower_pressure = _blower_pressure if _blower_pressure else 50.0 # Pa

# ------------------------------------------------------------------------------
HB_rooms_ = []
for room in _HB_rooms:
    try:
        room_phpp_dict = room.user_data['phpp'].copy()
    except:
        msg = "No PHHP-Spaces found on the HB Room? Be sure that you\n"\
        "use this component AFTER the 'PHPP Spaces' component\n"\
        "and that you have valid 'rooms' in the model in order to "\
        "determine the volume correctly.".format(room.display_name)
        ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, msg)
        continue
    
    # --------------------------------------------------------------------------
    (room_infil_airflow,
        phpp_spaces_vn50) = LBT2PH.airtightness.get_room_infiltration_rate(_n50, _q50, blower_pressure, room, room_phpp_dict)
    standard_flow_rate = LBT2PH.airtightness.calc_standard_flow_rate(room_infil_airflow, blower_pressure)
    
    # --------------------------------------------------------------------------
    # Calc the Zone's Infiltration Rate in m3/hr-2 of floor area (zone gross)
    zoneinfilRatePerFloorArea = standard_flow_rate /  room.floor_area  #m3/s---> m3/hr-m2
    infilt_per_exterior_ = standard_flow_rate /  room.exposed_area  #m3/s---> m3/hr-m2
    
    # --------------------------------------------------------------------------
    # Set the Load and Schedule for the HB-Room
    new_hb_room = room.duplicate()
    
    infilt_load = dup_load(new_hb_room, 'infiltration', Infiltration)
    infilt_load.flow_per_exterior_area = infilt_per_exterior_
    assign_load(new_hb_room, infilt_load, 'infiltration')
    
    infiltration_sch_ = LBT2PH.helpers.create_hb_constant_schedule( 'Infilt_Const_Sched' )
    infilt_sched = dup_load(new_hb_room, 'infiltration', 'infiltration_sch_')
    infilt_sched.schedule = infiltration_sch_
    assign_load(new_hb_room, infilt_sched, 'infiltration')
    
    HB_rooms_.append(new_hb_room)
    
    # --------------------------------------------------------------------------
    print('- '*30)
    print 'RESULTS:'
    print '  >HB-Room Infiltration Flow Per Unit of Floor Area: '\
            '{:.4f} m3/hr-m2 ({:.6f} m3/s-m2) @ 4 Pa'.format(zoneinfilRatePerFloorArea*60*60, zoneinfilRatePerFloorArea)
    print '  >HB-Room Infiltration Flow Per Unit of Facade Area: '\
    '{:.4f} m3/hr-m2 ({:.6f} m3/s-m2) @ 4 Pa'.format(infilt_per_exterior_*60*60, infilt_per_exterior_)
    print '  >HB-Room Infiltration ACH: {:.4f} @ 4 Pa'.format(standard_flow_rate*60*60 / phpp_spaces_vn50)