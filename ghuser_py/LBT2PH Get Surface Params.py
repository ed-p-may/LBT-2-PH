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
Use this component BEFORE a Honeybee 'Face' component. This will pull data from  the Rhino scene (names, constructions, etc) where relevant. Simply connect the  outputs from this compone to the inputs on the 'Face' for this to run.
-
EM March 1, 2021
    Args:
        _srfcs: <list> Rhino Brep or Mesh geometry
        auto_orientation_: <bool Default='False'> Set to 'True' to have this component automatically assign surface type ('wall', 'floor', 'roof'). useful if you are testing massings / geometry and don't want to assign explicit type everytime. If you have already assigned the surface type in Rhino, leave this set to False. If 'True' this will override any values found in the Rhino scene.
    Return:
        geo_: Connect to the '_geo' Input on a Honeybee 'Face' component.
        name_: Names found on the Rhino geometry (Rhino ObjectName). Connect to the '_name' Input on a Honeybee 'Face' component.
        type_: Surface type (wall, roof, floor) Connect to the '_type' Input on a Honeybee 'Face' component. 
        bc_: Connect to the '_bc' Input on a Honeybee 'Face' component. If blank or any Null values pased, will use HB defaults as usual.
        ep_const_: Connect to the 'ep_constr_' Input on a Honeybee 'Face' component. If blank or any Null values pased, will use HB defaults as usual.
        rad_mod_: <Not implemented yet>
"""

import LBT2PH
import LBT2PH.__versions__
import LBT2PH.helpers
import LBT2PH.assemblies
import LBT2PH.surfaces
import Grasshopper.Kernel as ghK

reload(LBT2PH)
reload(LBT2PH.__versions__)
reload(LBT2PH.helpers)
reload(LBT2PH.assemblies)
reload(LBT2PH.surfaces)

ghenv.Component.Name = "LBT2PH Get Surface Params"
LBT2PH.__versions__.set_component_params(ghenv, dev=False)

#-------------------------------------------------------------------------------
# Get the Surface data from the RH Scene
input_geom = LBT2PH.surfaces.get_input_geom(_srfcs, ghenv)
input_srfcs = LBT2PH.surfaces.get_rh_srfc_params(input_geom, ghenv, ghdoc)

if auto_orientation_:
    input_srfcs = LBT2PH.surfaces.determine_surface_type_by_orientation(input_srfcs)

#-------------------------------------------------------------------------------
# Get all the Assemblies from the RH Scene
rh_doc_constructions = LBT2PH.assemblies.get_constructions_from_rh(ghdoc)
hb_constructions = LBT2PH.assemblies.generate_all_HB_constructions(rh_doc_constructions, ghenv)

#-------------------------------------------------------------------------------
# Create the Honeybee surface objects
hb_surfaces = (LBT2PH.surfaces.hb_surface(srfc, hb_constructions) for srfc in input_srfcs)

#-------------------------------------------------------------------------------
# Outputs
geo_ = []
name_ = []
type_ = []
bc_ = []
ep_const_ = []
rad_mod_ = []
warnings = {}

for hb_srfc in hb_surfaces:
    name_warning = hb_srfc.check_surface_names()
    if name_warning: warnings['name_warning'] = name_warning
    
    geo_.append(hb_srfc.geometry)
    name_.append(hb_srfc.name)
    type_.append(hb_srfc.type)
    bc_.append(hb_srfc.bc)
    ep_const_.append(hb_srfc.const)
    rad_mod_.append(hb_srfc.rad_mod)

#-------------------------------------------------------------------------------
# Give Warnings
if _srfcs:
    for warning in warnings.values():
        ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Remark, warning)
    
    if 'Floor' not in type_:
        warning = "There is no 'Floor' surface found for some reason? Later components like\n"\
        "the 'PHPP Spaces', 'Airtightness', and others will NOT work without at least one valid\n" \
        "Honeybee 'Floor' element. Please check your surface assignnements and geometry\n"\
        "before proceeding.\n"\
        "1) Try setting the 'auto-orientation_' intput to 'True'?\n"\
        "2) Check the surface-normals for the floor surface perhaps?\n"\
        "3) If you are passing in GH-generated geometry and/or a Brep solid, consider using \n"\
        "the normal Honeybee 'HB Room from Solid' instead of this component?"
        ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Error, warning)