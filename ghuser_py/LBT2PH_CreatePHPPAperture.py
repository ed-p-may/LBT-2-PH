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
Use this component AFTER a Honeybee 'Aperture' component. This will pull data from  the Rhino scene (names, constructions, etc) where relevant.
-
EM Nov. 25, 2020
    Args:
        apertures: <list> The HB Aperture objects from a 'Aperture' component
        frames_: <list> Optional. PHPP Frame Object or Objects
        glazings_: <list> Optional. PHPP Glazing Object or Objects
        psi_installs_: <list> Optional. An optional entry for user-defined Psi-Install Values (W/m-k). Either pass in a single number which will be used for all edges, or a list of 4 numbers (left, right, bottom, top) - one for each edge.
        installs_: <list> Optional. An optional entry for user-defined Install Conditions (1|0) for each window edge (1=Apply Psi-Install, 0=Don't apply Psi-Install). Either pass in a single number which will be used for all edges, or a list of 4 numbers (left, right, bottom, top) - one for each edge.
    Return:
        apertures_: HB Aperture objects with new PHPP data. Pass along to any other HB component as usual.
"""

ghenv.Component.Name = "LBT2PH_CreatePHPPAperture"
ghenv.Component.NickName = "PHPP Aperture"
ghenv.Component.Message = 'NOV_25_2020'
ghenv.Component.IconDisplayMode = ghenv.Component.IconDisplayMode.application
ghenv.Component.Category = "PH-Tools"
ghenv.Component.SubCategory = "01 | Model"

import System
import Rhino
import rhinoscriptsyntax as rs
import json

import LBT2PH
import LBT2PH.windows

reload(LBT2PH)
reload(LBT2PH.windows)

def aperture_sources():
    ''' Find the component input source with the name "apertures" '''
    
    for input in ghenv.Component.Params.Input:
        if input.NickName == 'apertures':
            return input.Sources[0]
    
    return None

def window_rh_Guids():
    ''' Work backwards to get the Guid of the original input geom '''
    
    apertures = aperture_sources()
    if apertures is None:
        return None
    
    hb_aperture_compo = apertures.Attributes.GetTopLevel.DocObject
    
    rh_doc_window_guids = []
    for input in hb_aperture_compo.Params.Input[0].VolatileData[0]:
        guid_as_str = input.ReferenceID.ToString() 
        
        try:
            rh_doc_window_guids.append( System.Guid(guid_as_str) )
        except:
            rh_doc_window_guids.append( None )
    
    return rh_doc_window_guids

def cleanInput(_inputList, targetListLength,):
    # Used to make sure the input lists are all the same length
    # if the input param list isn't the same, use only the first item for all
    
    output = []
    if len(_inputList) == targetListLength:
        for each in _inputList:
            output.append(each)
    elif len(_inputList) >= 1:
        for i in range(targetListLength):
            output.append(_inputList[0])
    elif len(_inputList) == 0:
        for i in range(targetListLength):
            output.append(None)
    
    return output

#-------------------------------------------------------------------------------
# Clean the GH component inputs
ud_frames = cleanInput(frames_, len(apertures))
ud_glazings = cleanInput(glazings_, len(apertures))
ud_psi_installs = cleanInput(psi_installs_, len(apertures))
ud_installs = cleanInput(installs_, len(apertures))
gh_inputs = zip(ud_frames, ud_glazings, ud_psi_installs,  ud_installs)

#-------------------------------------------------------------------------------
# Get the Rhino Scene UserText (window Library)
rh_doc_window_library = LBT2PH.windows.get_rh_doc_window_library(ghdoc)

apertures_ = []
window_guids = []

if apertures:
    window_guids = window_rh_Guids()

for aperture, window_guid, gh_input in zip(apertures, window_guids, gh_inputs):
    # Get the Window data from the scene (name, params, etc)
    # If its a generic dbl pane, that means no GH user-determined input
    # so go try and find values from the Rhino scene instead
    if aperture.properties.energy.construction.display_name == 'Generic Double Pane':
        aperture_params = LBT2PH.windows.get_rh_window_obj_params(ghdoc, window_guid )
    else:
        aperture_params = {}
    
    #---------------------------------------------------------------------------
    # Apply any Grasshopper Scene user-determined values
    ud_f, ud_g, ud_psi, ud_i = gh_input
    
    if ud_f: aperture_params['FrameType'] = json.dumps(ud_f.to_dict())
    if ud_g: aperture_params['GlazingType'] = json.dumps(ud_g.to_dict())
    if ud_psi: aperture_params['FrameType'] = ud_psi
    if ud_i:
        aperture_params['InstallLeft'] = ud_i
        aperture_params['InstallRight'] = ud_i
        aperture_params['InstallBottom'] = ud_i
        aperture_params['InstallTop'] = ud_i
    
    #---------------------------------------------------------------------------
    # Create a new 'Window' Object based on the aperture, params, component library
    # Create EP Constructions for each window (based on frame / glass)
    window_obj = LBT2PH.windows.PHPP_Window(aperture, aperture_params, rh_doc_window_library)
    window_EP_material = LBT2PH.windows.create_EP_window_mat( window_obj )
    window_EP_const = LBT2PH.windows.create_EP_const( window_EP_material )
    
    
    #---------------------------------------------------------------------------
    # Create a new Aperture object and modify it's properties
    # Package up the data onto the 'Aperture' objects' user_data
    new_ap = aperture.duplicate()
    new_ap.properties.energy.construction = window_EP_const
    
    new_ap = LBT2PH.helpers.add_to_HB_model( new_ap, 'phpp', window_obj.to_dict(), ghenv, 'overwrite' )
    
    apertures_.append(new_ap)