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
Calculate the seasonal (summer | winter) radiation incident on the window surfaces. 
This component uses the LadybugTools 'IncidentRadiation' method. As stated on that component:
---
"Note that NO REFLECTIONS OF SOLAR ENERGY ARE INCLUDED IN THE ANALYSIS
PERFORMED BY THIS COMPONENT and it is important to bear in mind that vertical
surfaces typically receive 20% - 30% of their solar energy from reflection off
of the ground. Also note that this component uses the CAD environment's ray
intersection methods, which can be fast for geometries with low complexity
but does not scale well for complex geometries or many test points. For such
complex cases and situations where relfection of solar energy are important,
honeybee-radiance should be used."
---
The primary use of this component is to determine numerical 'shading factors' for use by
the LBT2PH 'Apply Win. Shading Factors' component. To calculate numerical shading factors
(0=fully shaded, 1=no shading) simply divide the unshaded radiation for each window by the
shaded radiation for that same window.
-
EM December 6, 2020
    Args:
        _winter_sky_mtx: A Sky Matrix from the "LB Cumulative Sky Matrix" component, which 
        describes the radiation coming from the various patches of the sky for the WINTER season.
        North American typically values: start month of October (10) and end month of April (4) when creating the Sky Matrix.
        _summer_sky_mtx: A Sky Matrix from the "LB Cumulative Sky Matrix" component, which 
        describes the radiation coming from the various patches of the sky for the SUMMER season.
        North American typically values: start month of May (5) and end month of Sept (9) when creating the Sky Matrix.
        grid_size_: A positive number in Rhino model units for the size of grid
            cells at which the input _geometry will be subdivided for incident
            radiation analysis. The smaller the grid size, the higher the
            resolution of the analysis and the longer the calculation will take.
            So it is recommended that one start with a large value here and
            decrease the value as needed. However, the grid size should usually
            be smaller than the dimensions of the smallest piece of the _geometry
            and context_ in order to yield meaningful results.
        _HB_rooms: The Honeybee Rooms in the model
        ------
        _window_names: A list of the names of each window. Should be in the same
            order as the '_window_surfaces' input. Connect to the 'Create Window Reveals'
            LBT2PH Component's 'window_names_' output.
        _window_surfaces: The window surfaces to analyze. Usually enter a 'surface'.
            Ensure that whatever you enter can be converted into a Mesh. Connect to the 'Create Window Reveals'
            LBT2PH Component's 'window_surfaces_' output.
        _window_surrounds: Rhino Breps and/or Rhino Meshes representing the window 'surround' geometry
            on the top / bottom / left / right. Connect to the 'Create Window Reveals'
            LBT2PH Component's 'window_surrounds_' output.
        _envelope_surfaces_punched: Rhino Breps and/or Rhino Meshes representing building envelope geometry
            that can block solar radiation to the test _geometry. Connect to the 'Create Window Reveals'
            LBT2PH Component's 'envelope_surfaces_punched_' output. Ensure that any walls or other
            surfaces are 'punched' with holes for the windows / apertures being analysed.
        additional_shading_surfaces_: Rhino Breps and/or Rhino Meshes representing context geometry
            outside the building that can block solar radiation to the test _geometry. This would
            be used for things like trees, neighbors, overhangs or other shading elements other
            than the basic building envelope surfaces themselves.
        -------
        legend_par_: Optional legend parameters from the "LB Legend Parameters"
            that will be used to customize the display of the results.
        parallel_: (bool) Set to "True" to run the study using multiple CPUs. This can
            dramatically decrease calculation time but can interfere with
            other computational processes that might be running on your
            machine. (Default: False).
        _run: (bool) Set to "True" to run the component and perform incident radiation
            analysis.
   Returns:
        HB_rooms_: The Honeybee-Rooms
        window_names_: A list of the Window names. Useful for passing along to the 
            'Apply Win. Shading Factors' component.
        winter_radiation_shaded_: The results for the WINTER period radiation (kWh) received
            for each window when shaded by the surrounding context. 
            By default, each branch on the DataTree corresponds to one window
            surface in the same order they were passed into the component.
        winter_radiation_unshaded_: The results for the WINTER period radiation (kWh) received
            for each window WITHOUT any surrounding context shading elements affecting it. 
            By default, each branch on the DataTree corresponds to one window
            surface in the same order they were passed into the component. In order to calculate
            the 'shading factor' for each window, simply divide this 'unshaded' radiation
            by the shaded radiation for the same window.
        summer_radiation_shaded_: The results for the Summer period radiation (kWh) received
            for each window when shaded by the surrounding context. 
            By default, each branch on the DataTree corresponds to one window
            surface in the same order they were passed into the component.
        summer_radiation_unshaded_: The results for the SUMMER period radiation (kWh) received
            for each window WITHOUT any surrounding context shading elements affecting it. 
            By default, each branch on the DataTree corresponds to one window
            surface in the same order they were passed into the component. In order to calculate
            the 'shading factor' for each window, simply divide this 'unshaded' radiation
            by the shaded radiation for the same window.
        -----
        winter_radiation_shaded_mesh_: A colored mesh of the test _geometry representing the cumulative
            incident radiation (kWh) received by the input _geometry over the WINTER period.
        summer_radiation_shaded_mesh_: A colored mesh of the test _geometry representing the cumulative
            incident radiation (kWh) received by the input _geometry over the SUMMER period.
        legend: A legend showing the kWh that correspond to the colors of the mesh.
        title: A text object for the study title.
"""

ghenv.Component.Name = "LBT2PH_GenLBTSeasonalRadiation"
ghenv.Component.NickName = "Seasonal Radiation from LBT"
ghenv.Component.Message = 'DEC_06_2020'
ghenv.Component.IconDisplayMode = ghenv.Component.IconDisplayMode.application
ghenv.Component.Category = "PH-Tools"
ghenv.Component.SubCategory = "01 | Model"

from System import Object
from Grasshopper import DataTree
from Grasshopper.Kernel.Data import GH_Path
import Rhino

import LBT2PH
import LBT2PH.shading_lbt

reload( LBT2PH )
reload( LBT2PH.shading_lbt )

#-------------------------------------------------------------------------------
grid_size = 0.5
if grid_size_: grid_size = grid_size_
mesh_params = Rhino.Geometry.MeshingParameters.Default

if _run:
    # Create the context shading Mesh geometry
    #---------------------------------------------------------------------------
    shade_mesh = LBT2PH.shading_lbt.create_shading_mesh(_envelope_surfaces_punched,
                        additional_shading_surfaces_, _window_surrounds, mesh_params)
    
    
    # deconstruct the sky-matrix and get the sky dome vectors. Winter (w) and Summer (s)
    #---------------------------------------------------------------------------
    w_sky_vecs, w_total_sky_rad = LBT2PH.shading_lbt.deconstruct_sky_matrix(_winter_sky_mtx)
    s_sky_vecs, s_total_sky_rad = LBT2PH.shading_lbt.deconstruct_sky_matrix(_summer_sky_mtx)
    
    
    # Calc window surface shaded and unshaded radiation
    #---------------------------------------------------------------------------
    winter_radiation_shaded_ = DataTree[Object]()
    winter_radiation_shaded_detailed_ = DataTree[Object]()
    winter_radiation_unshaded_ = DataTree[Object]()
    summer_radiation_shaded_ = DataTree[Object]()
    summer_radiation_shaded_detailed_ = DataTree[Object]()
    summer_radiation_unshaded_ = DataTree[Object]()
    mesh_by_window = DataTree[Object]()
    lb_window_meshes = []
    
    for i, window_surface in enumerate(_window_surfaces):
        pts, nrmls, win_msh, win_msh_bck, rh_msh  = LBT2PH.shading_lbt.build_window_meshes(window_surface, grid_size, mesh_params)
        lb_window_meshes.append(win_msh)
        
        # Solve Winter
        # ----------------------------------------------------------------------
        args_winter = (shade_mesh, win_msh_bck, pts, w_sky_vecs, nrmls, parallel_)
        
        int_matrix_s, int_matrix_u, angles_s, angles_u = LBT2PH.shading_lbt.generate_intersection_data(*args_winter)
        w_rads_shaded, face_areas = LBT2PH.shading_lbt.calc_win_radiation(int_matrix_s, angles_s, w_total_sky_rad, win_msh)
        w_rads_unshaded, face_areas = LBT2PH.shading_lbt.calc_win_radiation(int_matrix_u, angles_u, w_total_sky_rad, win_msh)
        
        winter_radiation_shaded_detailed_.AddRange(w_rads_shaded, GH_Path(i))
        winter_radiation_shaded_.Add(sum(w_rads_shaded)/sum(face_areas), GH_Path(i))
        winter_radiation_unshaded_.Add(sum(w_rads_unshaded)/sum(face_areas), GH_Path(i))
        
        
        #  Solve Summer
        # ----------------------------------------------------------------------
        args_summer = (shade_mesh, win_msh_bck, pts, s_sky_vecs, nrmls, parallel_)
        
        int_matrix_s, int_matrix_u, angles_s, angles_u = LBT2PH.shading_lbt.generate_intersection_data(*args_summer)
        s_rads_shaded, face_areas = LBT2PH.shading_lbt.calc_win_radiation(int_matrix_s, angles_s, s_total_sky_rad, win_msh)
        s_rads_unshaded, face_areas = LBT2PH.shading_lbt.calc_win_radiation(int_matrix_u, angles_u, s_total_sky_rad, win_msh)
        
        summer_radiation_shaded_detailed_.AddRange(s_rads_shaded, GH_Path(i))
        summer_radiation_shaded_.Add(sum(s_rads_shaded)/sum(face_areas), GH_Path(i))
        summer_radiation_unshaded_.Add(sum(s_rads_unshaded)/sum(face_areas), GH_Path(i))
        
        
        mesh_by_window.Add(rh_msh, GH_Path(i) )
    
    
    # Create the mesh and legend outputs
    # --------------------------------------------------------------------------
    # Flatten the radiation data trees
    winter_rad_vals = [item for branch in winter_radiation_shaded_detailed_.Branches for item in branch]
    summer_rad_vals = [item for branch in summer_radiation_shaded_detailed_.Branches for item in branch]
    
    # Create the single window Mesh
    joined_window_mesh = LBT2PH.shading_lbt.create_window_mesh( lb_window_meshes )
    
    winter_graphic, title = LBT2PH.shading_lbt.create_graphic_container('Winter', winter_rad_vals, joined_window_mesh, legend_par_)
    winter_radiation_shaded_mesh_, legend = LBT2PH.shading_lbt.create_rhino_mesh(winter_graphic, joined_window_mesh)
    
    summer_graphic, title = LBT2PH.shading_lbt.create_graphic_container('Summer', summer_rad_vals, joined_window_mesh, legend_par_)
    summer_radiation_shaded_mesh_, legend = LBT2PH.shading_lbt.create_rhino_mesh(summer_graphic, joined_window_mesh)

# Pass through....
window_names_ = _window_names
HB_rooms_ = _HB_rooms