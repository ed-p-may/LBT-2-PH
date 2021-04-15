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
Collects and organizes data for a DHW System. Hook up inputs from DHW components 
and this will organize for the excel writer.
Connect the output to the 'dhw_' input on the 'Create Excel Obj - Setup' component to use.
-
EM April 15, 2021
    Args:
        _system_name: (str) The name / idenfitier for the System.
        
        usage_: (Optional) The Usage Profile object decribing DHW litres/person/day of HW at 
            the Design Forward temp (unmixed). Input the result from a 'DHW Usage' component.
        design_frwrd_T_: (Deg C) Design Forward Temperature. Default is 60 deg C. Unmixed HW temp.
        ['DHW+Distribution', Cell J146]
        
        tap_points_: (Optional) The Tap Points (faucets, etc). Used to calculate the number
            tap points in the building. If none are input here, will use the number
            of branch pipes input as the number of tap points.
        recirc_pipes_: (Optional) The Recirculation Piping (not including branches).
            This is only used if there is a recirculation loop in the project. Connect a 
            'Pipping | Recirc' component here or Curve/Polyline Geometry
            ['DHW+Distribution', Cells J149:N163]
        branch_pipes_: (Optional) All the branch (non-recirc) piping. Connect the 'Piping | Banches' 
            result here or Curve/Polyline Geometry
            ['DHW+Distribution', Cells J167:N175]
        
        tank1_: (Optional) The main DHW tank (if any) used. Input the results of a 'DHW Tank' component.
            ['DHW+Distribution', Cells J186:J204]
            Note - Optionally, pass in the string 'default' in order to assign a 
            default tank with a heat loss rate of 4 W/k.
        tank2_: (Optional) The secondary DHW tank (if any) used. Input the results of a 'DHW Tank' component.
            ['DHW+Distribution', Cells M186:M204]
            Note - Optionally, pass in the string 'default' in order to assign a 
            default tank with a heat loss rate of 4 W/k.
        buffer_tank_: (Optional) The DHW buffer tank (if any) used. Heating Only. Input the 
            results of a 'DHW Tank' component.
            ['DHW+Distribution', Cells P186:P204]
        solar_: (Optional) A Solar-Thermal hot-water system. Connect to a 
            "DHW | Solar Thermal" component.
        
        _HB_rooms: The Honeybee-Rooms you would like to apply the DHW System to.
    
    Returns:
        HB_rooms_: The Honeybee Rooms with the new DHW systems added.
"""

import Grasshopper.Kernel as ghK

from LBT2PH.helpers import add_to_HB_model, preview_obj, context_rh_doc, convert_value_to_metric
import LBT2PH
import LBT2PH.dhw
import LBT2PH.dhw_IO

reload( LBT2PH )
reload( LBT2PH.dhw )
reload( LBT2PH.dhw_IO )

ghenv.Component.Name = "LBT2PH DHW System"
LBT2PH.__versions__.set_component_params(ghenv, dev='APR_15_2021')

#----- Get / Create Recirc Piping
#-------------------------------------------------------------------------------
try:
    recirc_piping = []
    for _input in recirc_pipes_:
        #---- Try making a new Segment based on an existing one
        #-----------------------------------------------------------------------
        recirc_piping.append( LBT2PH.dhw.PHPP_DHW_Pipe_Segment.from_existing(_input) )
except AttributeError:
    #----- Build the standardized inputs
    #---------------------------------------------------------------------------
    piping_inputs = LBT2PH.dhw_IO.piping_input_values(_input_node=5, _user_input=recirc_pipes_,
                                    _user_attr_dicts=[{}], _ghenv=ghenv, _ghdoc=ghdoc)
    
    #----- Build the actual piping segements
    #---------------------------------------------------------------------------
    recirc_piping = []
    for segment in piping_inputs:
        new_segment = LBT2PH.dhw.PHPP_DHW_Pipe_Segment()
        
        new_segment.length = segment.get('length')
        if segment.get('pipe_diameter'):            new_segment.diameter = segment.get('pipe_diameter')
        if segment.get('insulation_thickness'):     new_segment.insulation_thickness = segment.get('insulation_thickness')
        if segment.get('insulation_conductivity'):  new_segment.insulation_conductivity = segment.get('insulation_conductivity')
        if segment.get('insulation_reflective'):    new_segment.insulation_reflective = segment.get('insulation_reflective')
        if segment.get('insul_quality'):            new_segment.insul_quality = segment.get('insul_quality')
        if segment.get('daily_period'):             new_segment.daily_period = segment.get('daily_period')
        
        recirc_piping.append( new_segment )


#----- Get / Create Branch Piping
#-------------------------------------------------------------------------------
branch_piping = []
try:
    for _input in branch_pipes_:
        #---- Try making a new Segment based on an existing one
        #-----------------------------------------------------------------------
        branch_piping.append( LBT2PH.dhw.PHPP_DHW_Pipe_Segment.from_existing(_input) )
except AttributeError:
    #----- Build the standardized inputs
    #---------------------------------------------------------------------------
    piping_inputs = LBT2PH.dhw_IO.piping_input_values(_input_node=6, _user_input=branch_pipes_, 
                                    _user_attr_dicts=[{}], _ghenv=ghenv, _ghdoc=ghdoc)
    
    #----- Build the actual piping segements
    #---------------------------------------------------------------------------
    for segment in piping_inputs:
        new_segment = LBT2PH.dhw.PHPP_DHW_Pipe_Segment()
        
        new_segment.length = segment.get('length')
        if segment.get('pipe_diameter'):    new_segment.diameter = segment.get('pipe_diameter')
        
        branch_piping.append(new_segment)


#----- Get / Create the Tap Points
#-------------------------------------------------------------------------------
tap_pts = []
for tap_pt in tap_points_:
    new_tap_pt = LBT2PH.dhw.PHPP_DHW_Tap_Point()
    tap_pts.append( new_tap_pt )


#---- Create the System
#-------------------------------------------------------------------------------
dhw_system_obj = LBT2PH.dhw.PHPP_DHW_System()

if _system_name: dhw_system_obj.system_name = _system_name
if usage_: dhw_system_obj.usage = usage_
if design_frwrd_T_: dhw_system_obj.forwardTemp = convert_value_to_metric(design_frwrd_T_, 'C')

dhw_system_obj.tap_points = tap_pts
dhw_system_obj.circulation_piping = recirc_piping
dhw_system_obj.branch_piping = branch_piping
dhw_system_obj.rooms_assigned_to = [ hb_room.display_name for hb_room in _HB_rooms ]

if tank1_: dhw_system_obj.tank1 = tank1_
if tank2_: dhw_system_obj.tank2 = tank2_
if buffer_tank_: dhw_system_obj.tank_buffer = buffer_tank_
if solar_:
    dhw_system_obj.solar = solar_
    msg = dhw_system_obj.check_tanks_for_solar_connection()
    if msg:
        ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, msg)

#-------------------------------------------------------------------------------
preview_obj(dhw_system_obj)

#-------------------------------------------------------------------------------
# Add the new System onto the HB-Rooms
HB_rooms_ = []
for hb_room in _HB_rooms:
    new_hb_room = hb_room.duplicate()
    new_hb_room = add_to_HB_model(new_hb_room, 'dhw_systems', {dhw_system_obj.id:dhw_system_obj.to_dict()}, ghenv )
    HB_rooms_.append( new_hb_room )