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
EM November 29, 2020
    Args:
        north_: <Optional :float :vector> A number between -360 and 360 for the counterclockwise or a vector pointing 'north'
            difference between the North and the positive Y-axis in degrees.
            90 is West and 270 is East. Note that this is different than the
            convention used in EnergyPlus, which uses clockwise difference
            instead of counterclockwise difference. This can also be Vector
            for the direction to North. (Default: 0)
        epw_file_: The EPW file path
        _model: The Honeybee Model
        rooms_included_: <Optional :str> Input the Room/Zone Name or a list of Room/Zone Names to output to a PHPP document. If no input, all zones found in the HB Model will be output to a single PHPP Excel document. 
        rooms_excluded_: <Optional :str> Pass in a list of string values to filter out certain zones by name. If the zone name includes the string anywhere in its name, it will be removed from the set to output.
        ud_row_starts_: <Optional :str> Input a list of string values for any non-standard starting positions (rows) in your PHPP. This might be neccessary if you have modified your PHPP from the normal one you got originally. For instance, if you added new rows to the PHPP in  order to add more rooms (Additional Ventilation) or surfaces (Areas) or that sort of thing. To set the correct values here, input strings in the format " Worksheet Name, Start Key: New Start Row " - so use commas to separate the levels of the dict, then a semicolon before the value you want to input. Will accept multiline strings for multiple value resets.
        Enter any of the following valid Start Rows:
            -  Additional Ventilation, Rooms: ## (Default=56)
            -  Additional Ventilation, Vent Unit Selection: ## (Default=97)
            -  Additional Ventilation, Vent Ducts: ## (Default=127)
            -  Components, Ventilator: ## (Default=15)
            -  Areas, TB: ## (Default=145)
            -  Areas, Surfaces: ## (Default=41)
            -  Electricity non-res, Lighting: ## (Default= 19)
            -  Electricity non-res, Office Equip: ## (Default=62)
            -  Electricity non-res, Kitchen: ## (Default=77)
    Returns:
        footprint_: Preview of the 'footprint' found based on the input geometry. This is used for PER evaluation in the PHPP.
        excel_objects_: Excel obejcts which are ready to wrtite out to the PHPP file. Connect these tothe 'Wrtie XL Workbook' component.
"""

ghenv.Component.Name = "LBT2PH_ConvertLBT2PHPPObjs"
ghenv.Component.NickName = "LBT-->PHPP"
ghenv.Component.Message = 'NOV_29_2020'
ghenv.Component.IconDisplayMode = ghenv.Component.IconDisplayMode.application
ghenv.Component.Category = "PH-Tools"
ghenv.Component.SubCategory = "02 | LBT2PHPP"

from System import Object
from Grasshopper import DataTree
from Grasshopper.Kernel.Data import GH_Path

import LBT2PH
import LBT2PH.lbt_to_phpp
import LBT2PH.to_excel

reload(LBT2PH)
reload(LBT2PH.lbt_to_phpp)
reload( LBT2PH.to_excel )

excel_objects_ = DataTree[Object]() 

#-------------------------------------------------------------------------------
# Get all the info from the LBT Model
if _model:
    materials_opaque        = LBT2PH.lbt_to_phpp.get_opaque_materials_from_model(_model, ghenv)
    constructions_opaque    = LBT2PH.lbt_to_phpp.get_opaque_constructions_from_model(_model, ghenv)
    surfaces_opaque         = LBT2PH.lbt_to_phpp.get_exposed_surfaces_from_model(_model, LBT2PH.lbt_to_phpp._find_north(north_), ghenv)
    
    materials_windows       = LBT2PH.lbt_to_phpp.get_aperture_materials_from_model(_model)
    constructions_windows   = LBT2PH.lbt_to_phpp.get_aperture_constructions_from_model(_model)
    surfaces_windows        = LBT2PH.lbt_to_phpp.get_aperture_surfaces_from_model(_model, ghdoc)
    
    hb_rooms                = LBT2PH.lbt_to_phpp.get_zones_from_model(_model)
    phpp_spaces             = LBT2PH.lbt_to_phpp.get_spaces_from_model(_model, ghdoc)
    ventilation_system      = LBT2PH.lbt_to_phpp.get_ventilation_systems_from_model(_model, ghenv)
    ground_objs             = LBT2PH.lbt_to_phpp.get_ground_from_model(_model, ghenv)
    thermal_bridges         = LBT2PH.lbt_to_phpp.get_thermal_bridges(_model, ghenv)
    
    dhw_systems             = LBT2PH.lbt_to_phpp.get_dhw_systems(_model)
    appliances              = LBT2PH.lbt_to_phpp.get_appliances(_model)
    lighting                = LBT2PH.lbt_to_phpp.get_lighting(_model)
    climate                 = LBT2PH.lbt_to_phpp.get_climate(_model, epw_file_)
    footprint               = LBT2PH.lbt_to_phpp.get_footprint(surfaces_opaque)
    footprint_              = footprint.Footprint_surface
    
    phpp_settings           = LBT2PH.lbt_to_phpp.get_settings( _model )
    summer_vent             = LBT2PH.lbt_to_phpp.get_summ_vent( _model )
    heating_cooling         = LBT2PH.lbt_to_phpp.get_heating_cooling( _model )
    per                     = LBT2PH.lbt_to_phpp.get_PER( _model )
    occupancy               = LBT2PH.lbt_to_phpp.get_occupancy( _model )
    
    #---------------------------------------------------------------------------
    # Sort out the inputs
    hb_room_names = LBT2PH.to_excel.include_rooms( hb_rooms, rooms_included_, rooms_excluded_, ghenv)
    start_row_dict = LBT2PH.to_excel.start_rows( ud_row_starts_, ghenv )
    
    #---------------------------------------------------------------------------
    # Create Xl Objects
    uValuesList, uValueUID_Names     = LBT2PH.to_excel.build_u_values( constructions_opaque, materials_opaque )
    winComponentsList                = LBT2PH.to_excel.build_components( surfaces_windows )
    areasList, surfacesIncluded      = LBT2PH.to_excel.build_areas( surfaces_opaque, hb_room_names, uValueUID_Names )
    tb_List                          = LBT2PH.to_excel.build_thermal_bridges( thermal_bridges, start_row_dict)
    winSurfacesList                  = LBT2PH.to_excel.build_windows( surfaces_windows, surfacesIncluded, surfaces_opaque )   
    shadingList                      = LBT2PH.to_excel.build_shading( surfaces_windows, surfacesIncluded )
    tfa                              = LBT2PH.to_excel.build_TFA (phpp_spaces, hb_room_names)
    addnlVentRooms, ventUnitsUsed    = LBT2PH.to_excel.build_addnl_vent_rooms( phpp_spaces, ventilation_system, hb_room_names, start_row_dict )
    vent                             = LBT2PH.to_excel.build_addnl_vent_systems( ventilation_system, ventUnitsUsed, start_row_dict )
    airtightness                     = LBT2PH.to_excel.build_infiltration( hb_rooms, hb_room_names)
    ground                           = LBT2PH.to_excel.build_ground( ground_objs, hb_room_names, ghenv )
    dhw                              = LBT2PH.to_excel.build_DHW_system( dhw_systems, hb_room_names, ghenv )
    nonRes_Elec                      = LBT2PH.to_excel.build_non_res_space_info( phpp_spaces, hb_room_names, start_row_dict )
    location                         = LBT2PH.to_excel.build_location( climate )
    elec_equip_appliance             = LBT2PH.to_excel.build_appliances( appliances, hb_room_names, ghenv )
    lighting                         = LBT2PH.to_excel.build_lighting( lighting, hb_room_names )
    footprint                        = LBT2PH.to_excel.build_footprint( footprint )
    settings                         = LBT2PH.to_excel.build_settings( phpp_settings )
    summer_vent                      = LBT2PH.to_excel.build_summ_vent( summer_vent )
    heating_cooling                  = LBT2PH.to_excel.build_heating_cooling( heating_cooling, hb_room_names )
    per                              = LBT2PH.to_excel.build_PER( per, hb_room_names, ghenv )
    occupancy                        = LBT2PH.to_excel.build_occupancy( occupancy )
    
    #---------------------------------------------------------------------------
    # Add all the Excel-Ready Objects to a master Tree for outputting / passing
    excel_objects_.AddRange(uValuesList, GH_Path(0))
    excel_objects_.AddRange(winComponentsList, GH_Path(1))
    excel_objects_.AddRange(areasList, GH_Path(2))
    excel_objects_.AddRange(winSurfacesList, GH_Path(3))
    excel_objects_.AddRange(shadingList, GH_Path(4))
    excel_objects_.AddRange(tfa, GH_Path(5))
    excel_objects_.AddRange(tb_List, GH_Path(6))
    excel_objects_.AddRange(addnlVentRooms, GH_Path(7))
    excel_objects_.AddRange(vent, GH_Path(8))
    excel_objects_.AddRange(airtightness, GH_Path(9))
    excel_objects_.AddRange(ground, GH_Path(10))
    excel_objects_.AddRange(dhw, GH_Path(11))
    excel_objects_.AddRange(nonRes_Elec, GH_Path(12))
    excel_objects_.AddRange(location, GH_Path(13))
    excel_objects_.AddRange(elec_equip_appliance, GH_Path(14))
    excel_objects_.AddRange(lighting, GH_Path(15))
    excel_objects_.AddRange(footprint, GH_Path(16))
    excel_objects_.AddRange(settings, GH_Path(17))
    excel_objects_.AddRange(summer_vent, GH_Path(18))
    excel_objects_.AddRange(heating_cooling, GH_Path(19))
    excel_objects_.AddRange(per, GH_Path(20))
    excel_objects_.AddRange(occupancy, GH_Path(21))
    
    #---------------------------------------------------------------------------
    # Give Warnings
    if len(excel_objects_.Branch(GH_Path(2)))/10 > 100:
        AreasWarning = 'Warning: It looks like you have {:.0f} surfaces in the model. By Default\n'\
        'the PHPP can only hold 100 surfaces. Before writing out to the PHPP be sure to\n '\
        'add more lines to the "Areas" worksheet of your excel file.\n'\
        'After adding lines to the PHPP, be sure to input the correct Start Rows into\n'\
        'the "udRowStarts_" of this component.'.format(len(excel_objects_.Branch(2))/10)
        ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, AreasWarning)
    
    if len(excel_objects_.Branch(GH_Path(7)))/17 > 30:
        VentWarning = 'Warning: It looks like you have {:.0f} rooms in the model. By Default\n'\
        'the PHPP can only hold 30 different rooms in the Additional Ventilation worksheet.\n'\
        'Before writing out to the PHPP be sure to add more lines to the\n'\
        '"Additional Ventilation" worksheet in the "Dimensionsing of Air Quantities" section.\n'\
        'After adding lines to the PHPP, be sure to input the correct Start Rows into\n'\
        'the "udRowStarts_" of this component.'.format(len(excel_objects_.Branch(7))/17)
        ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, VentWarning)
    
    if len(excel_objects_.Branch(GH_Path(12)))/8 > 22:
        NonResWarning = 'Warning: It looks like you have {:.0f} Non-Residential Rooms in the model. By Default\n'\
        'the PHPP can only hold 22 different rooms in the "Electricity non-res" worksheet.\n'\
        'Before writing out to the PHPP be sure to add more lines to the \n '\
        '"Electricity non-res" worksheet in the "Lighting/non-residential" section.'.format(len(excel_objects_.Branch(12))/8)
        ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, NonResWarning)