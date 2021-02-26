import ghpythonlib.components as ghc
import rhinoscriptsyntax as rs
import Rhino

from ladybug_rhino.fromgeometry import from_face3d
from ladybug_rhino.togeometry import to_face3d 

def avg_normal_vectors(_vectors):
    x, y, z = 0, 0, 0
    for v in _vectors:
        x += v.X
        y += v.Y
        z += v.Z

    x = x/len(_vectors)
    y = y/len(_vectors)
    z = z/len(_vectors)
    
    return Rhino.Geometry.Vector3d(x, y, z)

def get_srfc_normal_vector(_surface):
    """ Returns the surface normal vector of a single Rhino Surface 
    
    Args:
        _surface: Rhino.Geometry.NurbsSurface: A Single surface
    Returns:
        surface_normal: The vector of the surface normal
    
    Note: This only works on a SINGLE surface. If you want to get the normal for a
    'Brep' object, be sure to use this on the Brep.Surfaces entities one at a time. 
    Breps have list of multiple surfaces (potentialy) and this function only works
    on a single surface at a time.
    """
    
    try:
        is_surface =  hasattr(_surface, 'NormalAt')
        if not is_surface:
            raise AttributeError
    except AttributeError:
        print('Input should be a single surface. If using on a Brep, pass in each of the "Brep.Surfaces" elements one at a time')

    centroid = Rhino.Geometry.AreaMassProperties.Compute(_surface).Centroid
    b, u, v = _surface.ClosestPoint(centroid)
    surface_normal = _surface.NormalAt(u, v)

    return surface_normal

def brep_avg_surface_normal(_brep):
    brep_surface_normals = []
    
    for srfc in _brep.Surfaces:
        brep_surface_normals.append( get_srfc_normal_vector(srfc) )

    return avg_normal_vectors(brep_surface_normals)

def inset_rhino_surface(_srfc, _inset_dist=0.001, _srfc_name=""):
    """ Insets/shrinks a Rhino Brep some dimension 
    Arg:
        _srfc: A Rhino Brep
        _inset_dist: float: Default=0.001m
        _srfc_name: str: The name of the surface, used for error messages
    Returns:
        new_srfc: A new Rhino surface, shrunk/inset by the specified amount
    """

    #-----------------------------------------------------------------------
    # Get all the surface params needed
    srfc_Center = ghc.Area(_srfc).centroid
    srfc_normal_vector = brep_avg_surface_normal(_srfc)
    srfc_edges = ghc.DeconstructBrep(_srfc).edges
    srfc_perimeter = ghc.JoinCurves(srfc_edges, False)

    #-----------------------------------------------------------------------
    # Try to inset the perimeter Curve
    inset_curve = rs.OffsetCurve(srfc_perimeter, srfc_Center, _inset_dist, srfc_normal_vector, 0)

    #-----------------------------------------------------------------------
    # In case the new curve goes 'out' and the offset fails
    # Or is too small and results in multiple offset Curves
    if len(inset_curve)>1:
        warning = 'Error. The surface: "{}" is too small. The offset of {} m"\
            "can not be done. Check the offset size?'.format(_srfc_name, _inset_dist)
        print(warning)
        
        inset_curve = rs.OffsetCurve(srfc_perimeter, srfc_Center, 0.001, srfc_normal_vector, 0)
        inset_curve = rs.coercecurve( inset_curve[0] )
    else:
        inset_curve = rs.coercecurve( inset_curve[0] )

    new_srfc = ghc.BoundarySurfaces(inset_curve)

    return new_srfc

def inset_LBT_Face3d(_face3d, _inset_dist=0.001):
    rhino_geom = from_face3d(_face3d)
    rhino_geom_inset = inset_rhino_surface(rhino_geom, _inset_dist)
    lbt_face3d = to_face3d(rhino_geom_inset)

    if lbt_face3d:
        return lbt_face3d[0]
    else:
        return None