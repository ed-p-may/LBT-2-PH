from itertools import izip
import math
import Rhino

try:
    from ladybug.viewsphere import view_sphere
    from ladybug.graphic import GraphicContainer
except ImportError as e:
    raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))

try:
    from ladybug_rhino.config import conversion_to_meters
    from ladybug_rhino.togeometry import to_joined_gridded_mesh3d
    from ladybug_rhino.fromgeometry import from_mesh3d, from_point3d, from_vector3d
    from ladybug_geometry.geometry3d import Mesh3D
    from ladybug_rhino.fromobjects import legend_objects
    from ladybug_rhino.text import text_objects
    from ladybug_rhino.intersect import intersect_mesh_rays
    from ladybug_rhino.grasshopper import de_objectify_output
except ImportError as e:
    raise ImportError('\nFailed to import ladybug_rhino:\n\t{}'.format(e))


# Cacl Radiation
#-------------------------------------------------------------------------------
def create_shading_mesh(_envelope_surfaces_punched, additional_shading_surfaces_,
                        _window_surrounds, _mesh_params ):
    """Creates a single joined mesh from all the shading surfaces 
    
    Adapted from Ladybug 'IncidentRadiation' Component

    Arguments:
        _envelope_surfaces_punched: The building surfaces with holes 'punched'
            for each aperture
        additional_shading_surfaces_: Any shading surfaces other than the basic
            envelope / surround ones
        _window_surrounds: The window 'surround' surfaces (top/bottom/left/right)
        _mesh_params: (Rhino.Geometry.MeshParameters)
    Returns:
        shade_mesh: (Mesh) A 'joined' mesh of all the shading / context surfaces
            in a single mesh.
    """
    
    shade_mesh = Rhino.Geometry.Mesh()
    for srfc in _envelope_surfaces_punched or []:
        if srfc :
            shade_mesh.Append( Rhino.Geometry.Mesh.CreateFromBrep( srfc, _mesh_params ) )
    for srfc in additional_shading_surfaces_ or []:
        if srfc:
            shade_mesh.Append( Rhino.Geometry.Mesh.CreateFromBrep( srfc, _mesh_params ) )
    for branch in _window_surrounds.Branches or []:
        if branch:
            for srfc in branch:
                if srfc:
                    shade_mesh.Append( Rhino.Geometry.Mesh.CreateFromBrep( srfc, _mesh_params ) )

    return shade_mesh

def deconstruct_sky_matrix(_sky_mtx):
    """Copied from Ladybug 'IncidentRadiation' Component
    
    Arguments:
        _sky_mtx: A Ladybug Sky Matrix for the season
    Returns: (tuple)
        sky_vecs: (list: _ )
        total_sky_rad: (list: _ )
    """
    
    mtx = de_objectify_output(_sky_mtx)
    total_sky_rad = [dir_rad + dif_rad for dir_rad, dif_rad in izip(mtx[1], mtx[2])]
    lb_vecs = view_sphere.tregenza_dome_vectors if len(total_sky_rad) == 145 \
        else view_sphere.reinhart_dome_vectors
    if mtx[0][0] != 0:  # there is a north input for sky; rotate vectors
        north_angle = math.radians(mtx[0][0])
        lb_vecs = [vec.rotate_xy(north_angle) for vec in lb_vecs]
    sky_vecs = [from_vector3d(vec) for vec in lb_vecs]

    return sky_vecs, total_sky_rad

def build_window_meshes(_window_surface, _grid_size, _mesh_params ):
    """Create the Ladybug Mesh3D grided mesh for the window being analysed
    
    Arguments:
        _window_surface: (Brep) A single window Brep from the scene
        _grid_size: (float)
        _mesh_params: (Rhino.Geometry.MeshingParameters)
    Returns: (tuple)
        points: (list: Ladybug Point3D) All the analysis points on the window
        normals: (list: Ladybug Normal) All the normals for the analysis points
        window_mesh: (ladybug_geometry.geometry3d.Mesh3D) The window
        window_back_mesh: (ladybug_geometry.geometry3d.Mesh3D) A copy of the window shifted 'back'
        just a little bit (0.1 units). Used when solving the 'unshaded' situation.
    """
    
    # create the gridded mesh for the window surface
    #---------------------------------------------------------------------------
    offset_dist = 0.001
    window_mesh = to_joined_gridded_mesh3d([_window_surface], _grid_size, offset_dist)
    window_rh_mesh = from_mesh3d(window_mesh)
    points = [from_point3d(pt) for pt in window_mesh.face_centroids]
    
    # Create a 'back' for the window
    #---------------------------------------------------------------------------
    # Mostly this is done so it can be passed to the ladybug_rhino.intersect.intersect_mesh_rays()
    # solver as a surfce which is certain to *not* shade the window at all
    window_back_mesh = None
    for sr in _window_surface.Surfaces:
        window_normal = sr.NormalAt(0.5, 0.5)
        window_normal.Unitize()
        window_normal = window_normal * -1 * 0.1
    
        window_back = _window_surface.Duplicate()
        window_back.Translate(window_normal)
        window_back_mesh = Rhino.Geometry.Mesh.CreateFromBrep(window_back, _mesh_params)[0]
    
    normals = [from_vector3d(vec) for vec in window_mesh.face_normals]

    return points, normals, window_mesh, window_back_mesh, window_rh_mesh

def generate_intersection_data(_shade_mesh, _win_mesh_back, _points, _sky_vecs, _normals, _parallel):
    """Creates all the Intersection Matrix data for both the Shaded and the UNShaded conditions

    Note that for the 'Unshaded' case you still have to pass the solver *something*, so 
    the _win_mesh_back is used for this case. This surface should block out any radiation coming from
    'behind' and also not interfer with the front-side radition calculation.
    
    Adapted from Ladybug 'IncidentRadiation' Component
    
    Arguments:
        _shade_mesh: (Mesh) The context shading joined mesh
        _win_mesh_back: (Mesh) The window surface pushed 'back' a little.
        _points: (_)     
        _sky_vecs: (_)
        _normals: (list: Ladybug Normals)
        _parallel: (bool)
    Returns: (tuple)
        int_matrix_init_shaded: Intersection Matrix for window WITH shading
        int_matrix_init_unshaded: Intersection Matrix for window WITHOUT shading
        angles_s: Shaded
        angles_u: UN-Shaded
    """

    # intersect the rays with the mesh
    #---------------------------------------------------------------------------
    int_matrix_init_shaded, angles_s = intersect_mesh_rays(
        _shade_mesh, _points, _sky_vecs, _normals, parallel=_parallel)

    int_matrix_init_unshaded, angles_u = intersect_mesh_rays(
        _win_mesh_back, _points, _sky_vecs, _normals, parallel=_parallel)

    return int_matrix_init_shaded, int_matrix_init_unshaded, angles_s, angles_u

def calc_win_radiation(_int_matrix_init, _angles, _total_sky_rad, _window_mesh):
    """Computes total kWh per window based on the int_matrix and sky vec angles 
    
    Arguments:
        _int_matrix_init: (_)
        _angles: (_)
        _total_sky_rad: (_)
        _window_mesh: (ladybug_geometry.geometry3d.Mesh3D)
    Returns: (tuple)
        average_window_kWh: (float) The area-weighted average total kWh radiation
        for the window over the analysis period specified.
    """
    
    results_kWh = []
    window_face_areas = []
    int_matrix = []
    
    count = (k for k in range(len(_angles)*2 )) # just a super large counter
    
    for c, int_vals, angs in izip(count, _int_matrix_init, _angles):
        pt_rel = (ival * math.cos(ang) for ival, ang in izip(int_vals, angs))
        rad_result = sum(r * w for r, w in izip(pt_rel, _total_sky_rad))
        
        int_matrix.append(pt_rel)
        results_kWh.append( rad_result * _window_mesh.face_areas[c] )
        window_face_areas.append( _window_mesh.face_areas[c] )
    
    return results_kWh, window_face_areas


# Graphics / Mesh
#-------------------------------------------------------------------------------
def create_graphic_container(_season, _data, _study_mesh, _legend_par):
    """Creates the Ladybug 'Graphic' Object from the result data
    
    Copied from Ladybug 'IncidentRadiation' Component
    
    Arguments:
        _season: (str) 'Winter' or 'Summer'. Used in the title.
        _data: (list: float:) A list of the result data to use to color / style the output
        _study_mesh: (ladybug_geometry.geometry3d.Mesh3D) The joined Mesh used in the analysis
        _legend_par: Ladybug Legend Parameters
    Returns: (tuple)
        graphic: (ladybug.graphic.GraphicContainer) The Ladybug Graphic Object
        title: The text title
    """

    graphic = GraphicContainer(_data, _study_mesh.min, _study_mesh.max, _legend_par)
    graphic.legend_parameters.title = 'kWh'
    
    title = text_objects(
        '{} Incident Radiation'.format(_season), graphic.lower_title_location,
        graphic.legend_parameters.text_height * 1.5,
        graphic.legend_parameters.font)

    return graphic, title

def create_window_mesh( _lb_meshes ):
    return Mesh3D.join_meshes( _lb_meshes )

def create_rhino_mesh(_graphic, _lb_mesh ):
    """Copied from Ladybug 'IncidentRadiation' Component 
    
    Arguments:
        _graphic: (ladybug.graphic.GraphicContainer) The Laybug Graphic object
        _lb_mesh: (Ladybug Mesh) A single joined mesh of the entire scene
    Returns: (tuple)
        mesh: (_)
        legend: (_)
    """
    
    # Create all of the visual outputs
    
    _lb_mesh.colors = _graphic.value_colors
    mesh = from_mesh3d( _lb_mesh )
    legend = legend_objects(_graphic.legend)

    return mesh, legend