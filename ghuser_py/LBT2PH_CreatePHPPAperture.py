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
EM December 23, 2020
    Args:
        apertures: <list> The HB Aperture objects from a 'Aperture' component
        frames_: <list> Optional. PHPP Frame Object or Objects
        glazings_: <list> Optional. PHPP Glazing Object or Objects
        installs_: <list> Optional. An optional entry for user-defined Install Conditions (1|0) for each window edge (1=Apply Psi-Install, 0=Don't apply Psi-Install). Either pass in a single number which will be used for all edges, or a list of 4 numbers (left, right, bottom, top) - one for each edge.
    Return:
        apertures_: HB Aperture objects with new PHPP data. Pass along to any other HB component as usual.
"""

ghenv.Component.Name = "LBT2PH_CreatePHPPAperture"
ghenv.Component.NickName = "PHPP Aperture"
ghenv.Component.Message = 'DEC_23_2020'
ghenv.Component.IconDisplayMode = ghenv.Component.IconDisplayMode.application
ghenv.Component.Category = "PH-Tools"
ghenv.Component.SubCategory = "01 | Model"

from itertools import izip

import System
import LBT2PH
import LBT2PH.windows
import LBT2PH.helpers

reload(LBT2PH)
reload(LBT2PH.windows)
reload(LBT2PH.helpers)

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


# Clean the GH component inputs
#-------------------------------------------------------------------------------
ud_frames = cleanInput(frames_, len(apertures))
ud_glazings = cleanInput(glazings_, len(apertures))
ud_installs = cleanInput(installs_, len(apertures))
gh_inputs = izip(ud_frames, ud_glazings,  ud_installs)


# Get the Rhino Scene UserText (window Library)
# Build Glazing, Frame and Install objects for everything that is found there
#-------------------------------------------------------------------------------
rh_doc_frame_and_glass_objs = LBT2PH.windows.build_frame_and_glass_objs_from_RH_doc(ghdoc)


# Build the new Aperture and PHPP Window Objects
#-------------------------------------------------------------------------------
apertures_ = []
window_guids = []

if apertures:
    window_guids = window_rh_Guids()

for aperture, window_guid, gh_input in izip(apertures, window_guids, gh_inputs):
    # Get the Aperture from the Grasshopper scene
    # If its a generic dbl pane construction, that means no GH/HB user-determined input
    # so go try and find values from the Rhino scene instead
    if aperture.properties.energy.construction.display_name == 'Generic Double Pane':
        aperture_params = LBT2PH.helpers.get_rh_obj_UserText_dict(ghdoc, window_guid )
    else:
        aperture_params = {}
    
    #---------------------------------------------------------------------------
    # Override params with any Grasshopper Component user-determined values
    ud_f, ud_g, ud_i = gh_input
    
    if ud_f: aperture_params['FrameType'] = ud_f
    if ud_g: aperture_params['GlazingType'] = ud_g
    if ud_i:
        aperture_params['InstallLeft'] = ud_i
        aperture_params['InstallRight'] = ud_i
        aperture_params['InstallBottom'] = ud_i
        aperture_params['InstallTop'] = ud_i
    
    
    
    # build the right glazing
    # 1) First build a glazing from the HB Mat / Construction
    # 2) if any UD (Rhino or GH) side Objects, overide the obj with those instead
    
    glazing = LBT2PH.windows.PHPP_Glazing.from_HB_Const( aperture.properties.energy.construction )
    ud_glazing = rh_doc_frame_and_glass_objs.get('lib_GlazingTypes', {}).get(aperture_params.get('GlazingType'))
    if ud_glazing: glazing = ud_glazing
    
    frame = LBT2PH.windows.PHPP_Frame.from_HB_Const( aperture.properties.energy.construction )
    ud_frame = rh_doc_frame_and_glass_objs.get('lib_FrameTypes', {}).get(aperture_params.get('FrameType'))
    if ud_frame: frame = ud_frame
    
    install = LBT2PH.windows.PHPP_Installs()
    install.install_L = aperture_params.get('InstallLeft', 1)
    install.install_R = aperture_params.get('InstallRight', 1)
    install.install_B = aperture_params.get('InstallBottom', 1)
    install.install_T = aperture_params.get('InstallTop', 1)
    
    #---------------------------------------------------------------------------
    # Create a new 'Window' Object based on the aperture, Frame, Glass, Installs
    # Create EP Constructions for each window (based on frame / glass)
    
    window_obj = LBT2PH.windows.PHPP_Window()
    
    window_obj.aperture = aperture
    window_obj.frame = frame
    window_obj.glazing = glazing
    window_obj.installs = install
    window_obj.install_depth = aperture_params.get('InstallDepth', 0.1)
    window_obj.variant_type = aperture_params.get('VariantType','a')
    
    window_EP_material = LBT2PH.windows.create_EP_window_mat( window_obj )
    window_EP_const = LBT2PH.windows.create_EP_const( window_EP_material )
    
    
    #---------------------------------------------------------------------------
    # Create a new Aperture object and modify it's properties
    # Package up the data onto the 'Aperture' objects' user_data
    
    new_ap = aperture.duplicate()
    
    new_ap.properties.energy.construction = window_EP_const
    new_name = aperture_params.get('Object Name', None)
    if new_name:
        new_ap.display_name = new_name
    
    new_ap = LBT2PH.helpers.add_to_HB_model( new_ap, 'phpp', window_obj.to_dict(), ghenv, 'overwrite' )
    
    apertures_.append(new_ap)