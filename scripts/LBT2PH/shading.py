from collections import namedtuple
import math
import ghpythonlib.components as ghc
from System import Object
from ladybug_rhino.fromgeometry import from_linesegment3d


class PHPP_Shading_Dims(Object):
    """ PHPP-Style dimensions to shading objects """
    
    Horizon = namedtuple('Horizon', ['h_hori', 'd_hori', 'checkline'])
    Overhang = namedtuple('Overhang', ['d_over', 'o_over', 'checkline'])
    Reveal = namedtuple('Reveal', ['o_reveal', 'd_reveal', 'checkline1', 'checkline2'])
    
    def __init__(self):
        self._horizon = None
        self._overhang = None
        self._reveal = None

    def __bool__(self):
        if self.horizon.h_hori or self.horizon.d_hori:
            return True
        if self.overhang.d_over or self.overhang.o_over:
            return True
        if self.reveal.o_reveal or self.reveal.d_reveal:
            return True
              
        return False
        
    def __nonzero__(self):
        return self.__bool__()

    @property
    def horizon(self):
        if self._horizon:
            return self._horizon
        else:
            return self.Horizon(None, None, None)
    
    @horizon.setter
    def horizon(self, _in):
        if not _in:
            pass
        
        if len(_in) == 3:
            self._horizon = self.Horizon(*_in)
        else:
            print('Horizon input should be list/tuple of length 3?')
            pass

    @property
    def overhang(self):
        if self._overhang:
            return self._overhang
        else:
            return self.Overhang(None, None, None)

    @overhang.setter
    def overhang(self, _in):
        if not _in:
            pass
    
        if len(_in) == 3:
            self._overhang = self.Overhang(*_in)
        else:
            print('Overhang input should be list/tuple of length 3?')
            pass
    
    @property
    def reveal(self):
        if self._reveal:
            return self._reveal
        else:
            return self.Reveal(None, None, None, None)

    @reveal.setter
    def reveal(self, _in):
        if not _in:
            pass
        
        if len(_in) == 4:
            self._reveal = self.Reveal(*_in)
        else:
            print('Reveal input should be list/tuple of length 4?')
            pass

    def to_dict(self):
        d = {}
        d.update( {'_horizon':self._horizon } )
        d.update( {'_overhang':self._overhang } )
        d.update( {'_reveal':self._reveal } )
        
        return d

    @classmethod
    def from_dict(cls, _dict):
        new_obj = cls()
        
        if not _dict:
            return new_obj

        new_obj._horizon = _dict.get('_horizon')
        new_obj._overhang = _dict.get('_overhang')
        new_obj._reveal = _dict.get('_reveal')
        
        return new_obj

def calc_shading_dims_simple(_phpp_window_obj, _shading_objs, _limit=99):
    """Finds PHPP-Style dimensions to relevant shading objects"""
    
    shading_dims_obj = PHPP_Shading_Dims()
    if not _shading_objs:
        return shading_dims_obj
    
    # ----------------------------------------------------------------------
    # Find the relevant geometry in the scene and figures out the critical dimensions from the window
    h_hori, d_hori, checkline_hori = find_horizon_shading(_phpp_window_obj, _shading_objs, _limit)
    d_over, o_over, checkline_over = find_overhang_shading(_phpp_window_obj, _shading_objs, _limit)
    o_reveal, d_reveal, checkline_1, checkline_2 = find_reveal_shading(_phpp_window_obj, _shading_objs, _limit)

    # ----------------------------------------------------------------------
    # Package for output
    shading_dims_obj.horizon = (h_hori, d_hori, checkline_hori)
    shading_dims_obj.overhang = (d_over, o_over, checkline_over)
    shading_dims_obj.reveal = (o_reveal, d_reveal, checkline_1, checkline_2)

    return shading_dims_obj

def find_horizon_shading(_phpp_window_obj, _shadingGeom, _extents=99):
    """
    Arguments:
        _phpp_winddow_obj: The PHPP_Window object to calcualte the values for
        _shadingGeom: (list) A list of possible shading objects to test against
        _extents: (float) A number (m) to limit the shading search to. Default = 99m
    Returns:
        h_hori: Distance (m) out from the glazing surface of any horizontal shading objects found
        d_hori: Distance (m) up from the base of the window to the top of any horizontal shading objects found
    """
    surface_normal = _phpp_window_obj.surface_normal

    #-----------------------------------------------------------------------
    # Find Starting Point
    glazingEdges = _phpp_window_obj._get_edges_in_order( _phpp_window_obj.glazing_surface )
    glazingBottomEdge = glazingEdges.Bottom
    ShadingOrigin = ghc.CurveMiddle( from_linesegment3d(glazingBottomEdge) )
    UpVector = ghc.VectorXYZ(0,0,1).vector
    
    #-----------------------------------------------------------------------
    # Find if there are any shading objects and if so put them in a list
    HorizonShading = []
    
    HorizontalLine = ghc.LineSDL(ShadingOrigin, surface_normal, _extents)
    VerticalLine = ghc.LineSDL(ShadingOrigin, UpVector, _extents)
    for shadingObj in _shadingGeom:
        if ghc.BrepXCurve(shadingObj, HorizontalLine).points != None:
            HorizonShading.append( shadingObj )
    
    #-----------------------------------------------------------------------
    # Find any intersection Curves with the shading objects
    IntersectionSurface = ghc.SumSurface(HorizontalLine, VerticalLine)
    IntersectionCurve = []
    IntersectionPoints = []
    
    for shadingObj in HorizonShading:
        if ghc.BrepXBrep(shadingObj, IntersectionSurface).curves != None:
            IntersectionCurve.append(ghc.BrepXBrep(shadingObj, IntersectionSurface))
    for pnt in IntersectionCurve:
        IntersectionPoints.append(ghc.ControlPoints(pnt).points)
    
    #-----------------------------------------------------------------------
    # Run the "Top-Corner-Finder" if there are any intersecting objects...
    if len(IntersectionPoints) != 0:
        # Find the top/closets point for each of the objects that could possibly shade
        KeyPoints = []
        for pnt in IntersectionPoints:
            Rays = []
            Angles = []
            if pnt:
                for k in range(len(pnt)):
                    Rays.append(ghc.Vector2Pt(ShadingOrigin,pnt[k], False).vector)
                    Angles.append(ghc.Angle(surface_normal , Rays[k]).angle)
                KeyPoints.append(pnt[Angles.index(max(Angles))])
    
        # Find the relevant highest / closest point
        Rays = []
        Angles = []
        for i in range(len(KeyPoints)):
            Rays.append(ghc.Vector2Pt(surface_normal, KeyPoints[i], False).vector)
            Angles.append(ghc.Angle(surface_normal, Rays[i]).angle)
        KeyPoint = KeyPoints[Angles.index(max(Angles))]
    
        # Use the point it finds to deliver the Height and Distance for the PHPP Shading Calculator
        h_hori = KeyPoint.Z - ShadingOrigin.Z #Vertical distance
        Hypot = ghc.Length(ghc.Line(ShadingOrigin, KeyPoint))
        d_hori = math.sqrt(Hypot**2 - h_hori**2)
        CheckLine = ghc.Line(ShadingOrigin, KeyPoint)
    else:
        h_hori = None
        d_hori = None
        CheckLine = HorizontalLine
    
    return h_hori, d_hori, CheckLine

def find_overhang_shading(_phpp_window_obj, _shadingGeom, _extents=99):
    # Figure out the glass surface (inset a bit) and then
    # find the origin point for all the subsequent shading calcs (top, middle)
    glzgCenter = ghc.Area(_phpp_window_obj.glazing_surface).centroid
    glazingEdges = _phpp_window_obj._get_edges_in_order( _phpp_window_obj.glazing_surface )
    glazingTopEdge = from_linesegment3d(glazingEdges.Top)
    ShadingOrigin = ghc.CurveMiddle(glazingTopEdge)
    
    # In order to also work for windows which are not vertical, find the 
    # 'direction' from the glazing origin and the top/middle ege point
    UpVector = ghc.Vector2Pt(glzgCenter, ShadingOrigin, True).vector
    
    #-----------------------------------------------------------------------
    # First, need to filter the scene to find the objects that are 'above'
    # the window. Create a 'test plane' that is _extents (99m) tall and 0.5m past the wall surface, test if
    # any objects intersect that plane. If so, add them to the set of things
    # test in the next step
    depth = float(_phpp_window_obj.install_depth) + 0.5
    edge1 = ghc.LineSDL(ShadingOrigin, UpVector, _extents)
    edge2 = ghc.LineSDL(ShadingOrigin, _phpp_window_obj.surface_normal, depth)
    intersectionTestPlane = ghc.SumSurface(edge1, edge2)
    
    OverhangShadingObjs = (x for x in _shadingGeom 
                    if ghc.BrepXBrep(intersectionTestPlane, x).curves != None)
    
    #-----------------------------------------------------------------------
    # Using the filtered set of shading objects, find the 'edges' of shading 
    # geom and then decide where the maximums shading point is
    # Create a new 'test' plane coming off the origin (99m in both directions this time).
    # Test to find any intersection shading objs and all their crvs/points with this plane
    HorizontalLine = ghc.LineSDL(ShadingOrigin, _phpp_window_obj.surface_normal, _extents)
    VerticalLine = ghc.LineSDL(ShadingOrigin, UpVector, _extents)
    
    IntersectionSurface = ghc.SumSurface(HorizontalLine, VerticalLine)
    IntersectionCurves = (ghc.BrepXBrep(obj, IntersectionSurface).curves 
                            for obj in OverhangShadingObjs
                            if ghc.BrepXBrep(obj, IntersectionSurface).curves != None)
    IntersectionPointsList = (ghc.ControlPoints(crv).points for crv in IntersectionCurves)
    IntersectionPoints = (pt for list_of_pts in IntersectionPointsList for pt in list_of_pts)
    
    #-----------------------------------------------------------------------
    # If there are any intersection Points found, choose the right one to use to calc shading....
    # Find the top/closets point for each of the objects that could possibly shade
    smallest_angle_found = 2 * math.pi
    key_point = None
    
    for pt in IntersectionPoints:
        if pt == None:
            continue
        
        # Protect against Zero-Length error
        ray = ghc.Vector2Pt(ShadingOrigin, pt, False).vector
        if ray.Length < 0.001:
            continue
        
        this_ray_angle = ghc.Angle(_phpp_window_obj.surface_normal , ray).angle
        if this_ray_angle < 0.001:
            continue
        
        if this_ray_angle <= smallest_angle_found:
            smallest_angle_found = this_ray_angle
            key_point = pt
    
    #-----------------------------------------------------------------------
    # Use the 'key point' found to deliver the Height and Distance for the PHPP Shading Calculator
    if key_point is not None:
        d_over = key_point.Z - ShadingOrigin.Z                              # Vertical distance
        Hypot = ghc.Length(ghc.Line(ShadingOrigin, key_point))              # Hypot
        o_over = math.sqrt(Hypot**2 - d_over**2)                            # Horizontal distance
        CheckLine = ghc.Line(ShadingOrigin, key_point)
    else:
        d_over = None
        o_over = None
        CheckLine = VerticalLine
    
    return d_over, o_over, CheckLine

def find_reveal_shading(_phpp_window_obj, _shadingGeom, _extents=99):
    
    WinCenter = ghc.Area(_phpp_window_obj.glazing_surface).centroid
    edges = _phpp_window_obj._get_edges_in_order( _phpp_window_obj.glazing_surface )
    surface_normal = _phpp_window_obj.surface_normal

    #Create the Intersection Surface for each side
    Side1_OriginPt = ghc.CurveMiddle( from_linesegment3d(edges.Left) )
    Side1_NormalLine = ghc.LineSDL(Side1_OriginPt, surface_normal, _extents)
    Side1_Direction = ghc.Vector2Pt(WinCenter, Side1_OriginPt, False).vector
    Side1_HorizLine = ghc.LineSDL(Side1_OriginPt, Side1_Direction, _extents)
    Side1_IntersectionSurface = ghc.SumSurface(Side1_NormalLine, Side1_HorizLine)
    
    #Side2_OriginPt = SideMidPoints[1] #ghc.CurveMiddle(self.Edge_Left)
    Side2_OriginPt = ghc.CurveMiddle( from_linesegment3d(edges.Right) )
    Side2_NormalLine = ghc.LineSDL(Side2_OriginPt, surface_normal, _extents)
    Side2_Direction = ghc.Vector2Pt(WinCenter, Side2_OriginPt, False).vector
    Side2_HorizLine = ghc.LineSDL(Side2_OriginPt, Side2_Direction, _extents)
    Side2_IntersectionSurface = ghc.SumSurface(Side2_NormalLine, Side2_HorizLine)
    
    #Find any Shader Objects and put them all into a list
    Side1_RevealShaderObjs = []
    testStartPt = ghc.Move(WinCenter, ghc.Amplitude(surface_normal, 0.1)).geometry #Offsets the test line just a bit
    Side1_TesterLine = ghc.LineSDL(testStartPt, Side1_Direction, _extents) #extend a line off to side 1
    for i in range(len(_shadingGeom)):
        if ghc.BrepXCurve(_shadingGeom[i],Side1_TesterLine).points != None:
            Side1_RevealShaderObjs.append(_shadingGeom[i])
    
    Side2_RevealShaderObjs = []
    Side2_TesterLine = ghc.LineSDL(testStartPt, Side2_Direction, _extents) #extend a line off to side 2
    for i in range(len(_shadingGeom)):
        if ghc.BrepXCurve(_shadingGeom[i],Side2_TesterLine).points != None:
            Side2_RevealShaderObjs.append(_shadingGeom[i])
    
    NumShadedSides = 0
    if len(Side1_RevealShaderObjs) != 0:
        Side1_o_reveal = CalcRevealDims(_phpp_window_obj, Side1_RevealShaderObjs, Side1_IntersectionSurface, Side1_OriginPt, Side1_Direction)[0]
        Side1_d_reveal = CalcRevealDims(_phpp_window_obj, Side1_RevealShaderObjs, Side1_IntersectionSurface, Side1_OriginPt, Side1_Direction)[1]
        Side1_CheckLine = CalcRevealDims(_phpp_window_obj, Side1_RevealShaderObjs, Side1_IntersectionSurface, Side1_OriginPt, Side1_Direction)[2]
        NumShadedSides = NumShadedSides + 1
    else:
        Side1_o_reveal =  None
        Side1_d_reveal = None
        Side1_CheckLine = Side1_HorizLine
    
    if len(Side2_RevealShaderObjs) != 0:
        Side2_o_reveal = CalcRevealDims(_phpp_window_obj, Side2_RevealShaderObjs, Side2_IntersectionSurface, Side2_OriginPt, Side2_Direction)[0]
        Side2_d_reveal = CalcRevealDims(_phpp_window_obj, Side2_RevealShaderObjs, Side2_IntersectionSurface, Side2_OriginPt, Side2_Direction)[1]
        Side2_CheckLine = CalcRevealDims(_phpp_window_obj, Side2_RevealShaderObjs, Side2_IntersectionSurface, Side2_OriginPt, Side2_Direction)[2]
        NumShadedSides = NumShadedSides + 1
    else:
        Side2_o_reveal =  None
        Side2_d_reveal = None
        Side2_CheckLine = Side2_HorizLine
    
    o_reveal = None#(Side1_o_reveal + Side2_o_reveal )/ max(1,NumShadedSides)
    d_reveal = None#(Side1_d_reveal + Side2_d_reveal )/ max(1,NumShadedSides)
    
    return o_reveal, d_reveal, Side1_CheckLine, Side2_CheckLine

def CalcRevealDims(_phpp_window_obj, RevealShaderObjs_input, SideIntersectionSurface, Side_OriginPt, Side_Direction):
    #Test shading objects for their edge points
    Side_IntersectionCurve = []
    Side_IntersectionPoints = []
    for i in range(len(RevealShaderObjs_input)): #This is the list of shading objects to filter
        if ghc.BrepXBrep(RevealShaderObjs_input[i], SideIntersectionSurface).curves != None:
            Side_IntersectionCurve.append(ghc.BrepXBrep(RevealShaderObjs_input[i], SideIntersectionSurface).curves)
    for i in range(len(Side_IntersectionCurve)):
        for k in range(len(ghc.ControlPoints(Side_IntersectionCurve[i]).points)):
            Side_IntersectionPoints.append(ghc.ControlPoints(Side_IntersectionCurve[i]).points[k])
    
    #Find the top/closets point for each of the objects that could possibly shade
    Side_KeyPoints = []
    Side_Rays = []
    Side_Angles = []
    for i in range(len(Side_IntersectionPoints)):
        if Side_OriginPt != Side_IntersectionPoints[i]:
            Ray = ghc.Vector2Pt(Side_OriginPt, Side_IntersectionPoints[i], False).vector
            Angle = math.degrees(ghc.Angle(_phpp_window_obj.surface_normal, Ray).angle)
            if  Angle < 89.9:
                Side_Rays.append(Ray)
                Side_Angles.append(float(Angle))
                Side_KeyPoints.append(Side_IntersectionPoints[i])
    Side_KeyPoint = Side_KeyPoints[Side_Angles.index(min(Side_Angles))]
    Side_KeyRay = Side_Rays[Side_Angles.index(min(Side_Angles))]
    
    #use the Key point found to calculte the Distances for the PHPP Shading Calculator
    Side_Hypot = ghc.Length(ghc.Line(Side_OriginPt, Side_KeyPoint))
    Deg = (ghc.Angle(Side_Direction, Side_KeyRay).angle) #note this is in Radians
    Side_o_reveal =  math.sin(Deg) * Side_Hypot
    Side_d_reveal = math.sqrt(Side_Hypot**2 - Side_o_reveal**2)
    Side_CheckLine = ghc.Line(Side_OriginPt, Side_KeyPoint)
    
    return [Side_o_reveal, Side_d_reveal, Side_CheckLine]
