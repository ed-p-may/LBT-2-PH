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
Create a ground contact 'Floor Element' for use in writing to the 'Ground' worksheet. By Default, this will just create a single floor element. You can input up to 3 of these (as a flattened list) into the 'grndFloorElements_' input on the 'Create Excel Obj - Geom' component. 
However, if you also pass in the Honeybee Zones (into _HBZones) this will try and sort out the right ground element from the HB Geometry and parameters for each zone input. This info will be automatcally passed through to the Excel writer. If you have a simple situation, you can pass all of the Honeybee zones in at once, but if you need to set detailed parameters for multiple different floor types, first explode the Honeybee Zone object and then apply one of these components to each zone one at a time. Merge the zones back together before passing along.
-
EM November 27, 2020
    Args:
        _HBZones: (list) <Optional> The Honeybee Zone Objects. 
        _type: (string): Input a floor element 'type'. Choose either:
            > 01_SlabOnGrade
            > 02_HeatedBasement
            > 03_UnheatedBasement
            > 04_SuspendedFloorOverCrawlspace
        _floorSurfaces: (List) Rhino Surface objects which describe the ground-contact surface. If the surfaces have a U-Value assigned that will be read to create the object. Use the 'Set Surface Params' tool in Rhino to set parameters for the surface before inputing.
        _exposedPerimCrvs: (List) Rhino Curve object(s) [or Surfaces] which describe the 'Exposed' perimeter of the ground contact surface(s). If these curves have a Psi-Value assigned that will be read and used to create the object. Use the 'Linear Thermal Bridge' tool in Rhino to assign Psi-Values to curves before inputing. If a surface is passed in, will use the total perimeter length of the surface as 'exposed' and apply a default Psi-Value of 0.5 W/mk for all edges.
    Returns:
        floorElement_: A single 'Floor Element' object. Input this into the 'grndFloorElements_' input on the 'Create Excel Obj - Geom' component to write to PHPP.
        HBZones_: The Honeybee zone Breps to pass along to the next component
"""

ghenv.Component.Name = "LBT2PH_GroundContactElement"
ghenv.Component.NickName = "Create Floor Element"
ghenv.Component.Message = 'NOV_27_2020'
ghenv.Component.IconDisplayMode = ghenv.Component.IconDisplayMode.application
ghenv.Component.Category = "PH-Tools"
ghenv.Component.SubCategory = "01 | Model"

import Grasshopper.Kernel as ghK
from ladybug_rhino.fromgeometry import from_face3d 

import LBT2PH
import LBT2PH.ground
import LBT2PH.helpers
from LBT2PH.helpers import convert_value_to_metric
from LBT2PH.helpers import preview_obj
from LBT2PH.helpers import add_to_HB_model

reload( LBT2PH )
reload( LBT2PH.ground )
reload( LBT2PH.helpers )

#-------------------------------------------------------------------------------
# Classes and Defs

def cleanInputs(_in, _nm, _default, _units='-'):
    # Apply defaults if the inputs are Nones
    out = _in if _in != None else _default
    out = convert_value_to_metric(str(out), _units)
    
    # Check that output can be float
    try:
        # Check units
        if _nm == "thickness":
            if float(out.ToString()) > 1:
                unitWarning = "Check thickness units? Should be in METERS not MM." 
                ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, unitWarning)
            return float(out.ToString())
        elif _nm == 'orientation':
            return out
        elif _nm == 'psi':
            return str(out)
        else:
            return float(out.ToString())
    except:
        ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Error, '"{}" input should be a number'.format(_nm))
        return out

def setup_component_input(_type):
    """ Dynamic setup of the Component inputs based on the 'type' selector """
    direction = 'Please input a valid Floor Type into "_type". Input either:\n'\
    '    1: Slab on Grade\n'\
    '    2: Heated Basement\n'\
    '    3: UnHeated Basement\n'\
    '    4: Suspeneded Floor over Crawspace'
    
    # Setup Inputs based on type
    inputs_slabOnGrade = {
        4:{'name':'_exposedPerimPsiValue', 'desc':'(float) Psi-Value of the perimeter slab-edge thermal bridge (w/mk). Default is None (0)'},
        5:{'name':'_perimInsulWidthOrDepth', 'desc':'(float) The width or depth (m) beyond the face of the building enclosure which the perimeter insualtion extends. For vertical, measure this length from the underside of the floor slab insulation. Default is 1 m.'},
        6:{'name':'_perimInsulThickness', 'desc':'(float) Perimeter Insualtion Thickness (m). Default is 0.101 m'},
        7:{'name':'_perimInsulConductivity', 'desc':'(float) Perimeter Insulation Thermal Conductivity (W/mk). Default is 0.04 W/m2k'},
        8:{'name':'_perimInsulOrientation', 'desc':'(string) Perimeter Insulation Orientation. Input either "Vertical" or "Horizontal". Default is "Vertical".'}
        }
    
    inputs_heatedBasement = {
        4:{'name':'_exposedPerimPsiValue', 'desc':'(float) Psi-Value of the perimeter slab-edge thermal bridge (w/mk). Default is None (0)'},
        7:{'name':'_wallBelowGrade_height', 'desc':'(float) Average height (m) from grade down to base of basement wall.'},
        8:{'name':'_wallBelowGrade_Uvalue', 'desc':'(float) U-Value (W/m2k) of wall below grade.'},
        }
    
    inputs_unheatedBasement =  {  
        4:{'name':'_exposedPerimPsiValue', 'desc':'(float) Psi-Value of the perimeter slab-edge thermal bridge (w/mk). Default is None (0)'},
        5:{'name':'_wallAboveGrade_height', 'desc':'(float) Average height (m) from grade up to top of  basement wall.'},
        6:{'name':'_wallAboveGrade_Uvalue', 'desc':'(float) U-Value (W/m2k) of wall above grade.'},
        7:{'name':'_wallBelowGrade_height', 'desc':'(float) Average height (m) from grade down to base of basement wall.'},
        8:{'name':'_wallBelowGrade_Uvalue', 'desc':'(float) U-Value (W/m2k) of wall below grade.'},
        9:{'name':'_basementFloor_Uvalue', 'desc':'(float) U-Value (W/m2k) of the basement floor slab.'},
        10:{'name':'_basementAirChange', 'desc':'(float) Air exchange rate (ACH) in the unheated basement. A Typical value is 0.2ACH'},
        11:{'name':'_basementVolume', 'desc':'(float) Air Volume (m3) of the unheated basement. The basement ventilation heat losses are calculated based on this volume and the air exchange.'}
        }
        
    inputs_suspendedFloor =  {  
        4:{'name':'_exposedPerimPsiValue', 'desc':'(float) Psi-Value of the perimeter slab-edge thermal bridge (w/mk). Default is None (0)'},
        5:{'name':'_wallCrawlSpace_height', 'desc':'(float) Average height (m) of the crawl space walls.'},
        6:{'name':'_wallCrawlSpace_Uvalue', 'desc':'(float) U-Value (W/m2k) of the crawl space walls.'},
        7:{'name':'_crawlSpace_UValue', 'desc':'(float) U-Value of the floor under the crawl space. If the ground is not insulated, the heat transfer coefficient of 5.9 W/m2k must be used.'},
        8:{'name':'_ventilationOpeningArea', 'desc':'(float) Total area (m2) of the ventilation openings of the crawl space.'},
        9:{'name':'_windVelocityAt10m', 'desc':'(float) Average wind velocity (m/s) at 10m height in the selected location. Default is 4 m/s.'},
        10:{'name':'_windShieldFactor', 'desc':'(float) Wind Shield Factor. Default is 0.05. Typical Values:\n-Protected Site (city center): 0.02\n-Average Site (suburb): 0.05\n-Exposed Site (rural):0.10'}
        }
    
    if _type == None:
        inputs = {}
        ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, direction)
    else:
        if '1' in str(_type):
            inputs = inputs_slabOnGrade
        elif '2' in str(_type):
            inputs = inputs_heatedBasement
        elif '3' in str(_type):
            inputs = inputs_unheatedBasement
        elif '4' in str(_type):
            inputs = inputs_suspendedFloor
        else:
            inputs = {}
            ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, direction)
            
    for inputNum in range(4, 12):
        item = inputs.get(inputNum, {'name':'-', 'desc':'-'})
        
        ghenv.Component.Params.Input[inputNum].NickName = item.get('name')
        ghenv.Component.Params.Input[inputNum].Name = item.get('name')
        ghenv.Component.Params.Input[inputNum].Description = item.get('desc')
        
    return None

def handle_input_curve( _input_curve ):
    # Sort out Perim Curve Inputs
    perim_curves_ = []
    for i, item in enumerate(_input_curve):
        try:
            perim_curves_.append( float(item) )
        except:
            try:
                rhinoGuid = ghenv.Component.Params.Input[3].VolatileData[0][i].ReferenceID.ToString()
                perim_curves_.append( rhinoGuid )
            except:
                warning = 'Please input only curves, surfaces or numbers (list) for _exposedPerimCrvs'
                ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, warning)
    
    return perim_curves_

def handle_input_surface( _inputs ):
    output = []
    
    for i, item in enumerate( _inputs ):
        try:
            output.append( float(item) )
        except:
            try:
                rhino_guid = ghenv.Component.Params.Input[2].VolatileData[0][i].ReferenceID.ToString()
                output.append( rhino_guid )
            except Exception as e:
                print(e)
                warning = 'Please input only curves, surfaces or numbers (list) for _floor_surfaces'
                ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, warning)
    
    return output

def does_not_have_exposed_floor( _hb_room ):
    """ Check is the HB-Room has at least one 'exposed' floor surfac in it """
    
    for face in _hb_room.faces:
        if face.type=='Floor' and face.boundary_condition=='Outdoors':
            return True
    
    return False

def get_input_values():
    """ Dynamic Component Input 'get' - pulls all the input names/values into a dictionary """
    
    inputs = {}
    
    for input in ghenv.Component.Params.Input:
        try:
            vals = list(input.VolatileData[0])
            try:
                val = float( str(vals[0]) )
            except:
                val = str(vals[0])
            inputs[input.Name] = val
        
        except Exception as e:
            inputs[input.Name] = None
    
    return inputs

def build_slab_on_grade( _floor_elements, _inputs ):
    # Custom Inputs
    perimPsi = cleanInputs(_inputs.get('_exposedPerimPsiValue'), 'psi', None, 'W/MK')
    depth = cleanInputs(_inputs.get('_perimInsulWidthOrDepth'), "depth", 1.0, 'M')
    thickness = cleanInputs(_inputs.get('_perimInsulThickness'), "thickness", 0.101, 'M')
    conductivity = cleanInputs(_inputs.get('_perimInsulConductivity'), "lambda", 0.04, 'W/MK')
    orientation = cleanInputs(_inputs.get('_perimInsulOrientation'), "orientation", 'Vertical')
    
    # Build the ground element
    params = (_floor_elements, perimPsi, depth, thickness, conductivity, orientation)
    ground_element_ = LBT2PH.ground.PHPP_Ground_Slab_on_Grade( *params )
    
    return ground_element_

def build_heated_basement( _floor_elements, _inputs ):
    # Custom Inputs
    perimPsi = cleanInputs(_inputs.get('_exposedPerimPsiValue'), 'psi', None, 'W/MK')
    wallHeight_BG = cleanInputs(_inputs.get('_wallBelowGrade_height'), "height_bg", 1.0, 'M')
    wallU_BG = cleanInputs(_inputs.get('_wallBelowGrade_Uvalue'), "Uvalue_bg", 1.0, 'W/M2K')
    
    # Build the ground element
    params = (_floor_elements, perimPsi, wallHeight_BG, wallU_BG )
    ground_element_ = LBT2PH.ground.PHPP_Ground_Heated_Basement( *params )
    
    return ground_element_

def build_unheated_basement( _floor_elements, _inputs ):
    # Custom Inputs
    perimPsi = cleanInputs(_inputs.get('_exposedPerimPsiValue'), 'psi', None, 'W/MK')
    wallHeight_AG = cleanInputs(_inputs.get('_wallAboveGrade_height'), "height_ag", 1.0, 'M')
    wallU_AG = cleanInputs(_inputs.get('_wallAboveGrade_Uvalue'), "Uvalue_ag", 1.0, 'W/M2K')
    wallHeight_BG = cleanInputs(_inputs.get('_wallBelowGrade_height'), "height_bg", 1.0, 'M')
    wallU_BG = cleanInputs(_inputs.get('_wallBelowGrade_Uvalue'), "Uvalue_bg", 1.0, 'W/M2K')
    floorU = cleanInputs(_inputs.get('_basementFloor_Uvalue'), "Uvalue", 1.0, 'W/M2K')
    ach = cleanInputs(_inputs.get('_basementAirChange'), "ACH", 0.2)
    vol = cleanInputs(_inputs.get('_basementVolume'), "Volume", 1.0, 'M3')
    
    # Build the ground element
    params = (_floor_elements, perimPsi, wallHeight_AG, wallU_AG, wallHeight_BG, wallU_BG, floorU, ach, vol )
    ground_element_ = LBT2PH.ground.PHPP_Ground_Unheated_Basement( *params )
    
    return ground_element_

def build_crawl_space( _floor_elements, _inputs ):
    # Custom Inputs
    perimPsi = cleanInputs(_inputs.get('_exposedPerimPsiValue'), 'psi', None, 'W/MK')
    wallHeight = cleanInputs(_inputs.get('_wallCrawlSpace_height'), "height", 1.0, 'M')
    wallU = cleanInputs(_inputs.get('_wallCrawlSpace_Uvalue'), "Uvalue", 1.0, 'W/M2K')
    crawlspaceU = cleanInputs(_inputs.get('_crawlSpace_UValue'), "Ucrawl", 5.9, 'W/M2K')
    ventOpening = cleanInputs(_inputs.get('_ventilationOpeningArea'), "ventOpening", 1.0, 'M2')
    windVelocity = cleanInputs(_inputs.get('_windVelocityAt10m'), "velocity", 4.0)
    windFactor = cleanInputs(_inputs.get('_windShieldFactor'), "windFactor", 0.05)
    
    # Build the ground element
    params = (_floor_elements, perimPsi, wallHeight, wallU, crawlspaceU, ventOpening, windVelocity, windFactor)
    ground_element_ = LBT2PH.ground.PHPP_Ground_Crawl_Space( *params )
    
    return ground_element_

#-------------------------------------------------------------------------------
# Set all the component input values / names / hints
setup_component_input(_type)
ghenv.Component.Attributes.Owner.OnPingDocument()

# Sort out what input geometry to use
# If both a floor surface and a perim_curve are input, use them both
#-------------------------------------------------------------------------------
ground_elements_ = []
HB_rooms_ = []
if _type:
    # Basic Inputs
    with LBT2PH.helpers.context_rh_doc(ghdoc):
        floor_surfaces = handle_input_surface( _floor_surfaces )
        perim_curves = handle_input_curve( _exposedPerimCrvs)
        
        for hb_room in _HB_rooms:
            if does_not_have_exposed_floor(hb_room):
                HB_rooms_.append( hb_room )
                print('Room "{}" does not have any exposed floor surfaces. Skipping this room'.format(hb_room.display_name))
                continue
            
            floor_element = LBT2PH.ground.PHPP_Ground_Floor_Element( ghenv )
            floor_element.hb_host_room_name = hb_room.display_name
            
            if floor_surfaces and perim_curves:
                floor_element.set_surface_values( floor_surfaces )
                floor_element.set_perim_edge_values( perim_curves, _exposedPerimPsiValue )
            elif floor_surfaces and not perim_curves:
                floor_element.set_surface_values( floor_surfaces )
                floor_element.set_perim_edge_values( floor_surfaces, _exposedPerimPsiValue )
            else:
                floor_element.set_values_by_hb_room( hb_room )
            
            #-------------------------------------------------------------------
            # Build the Ground Element
            if '1' in str(_type):
                inputs = get_input_values()
                ground_element = build_slab_on_grade( floor_element, inputs )
                ground_elements_.append( ground_element )
            #-------------------------------------------------------------------
            if '2' in str(_type):
                inputs = get_input_values()
                ground_element = build_heated_basement( floor_element, inputs )
                ground_elements_.append( ground_element )
            #-------------------------------------------------------------------
            if '3' in str(_type):
                inputs = get_input_values()
                ground_element = build_unheated_basement( floor_element, inputs )
                ground_elements_.append( ground_element )
            #-------------------------------------------------------------------
            if '4' in str(_type):
                inputs = get_input_values()
                ground_element = build_crawl_space( floor_element, inputs )
                ground_elements_.append( ground_element )
            
            #-------------------------------------------------------------------
            # Add the ground element onto the HB-Room
            new_room = hb_room.duplicate()
            add_to_HB_model(new_room, 'ground', ground_element.to_dict(), ghenv)
            HB_rooms_.append( new_room )
            
            #-------------------------------------------------------------------
            preview_obj( ground_element )