import rhinoscriptsyntax as rs
import Rhino
import ghpythonlib.components as ghc
import json
import math
from collections import namedtuple
from itertools import izip
from System import Object

import LBT2PH
import LBT2PH.helpers
import LBT2PH.shading

reload(LBT2PH.helpers)
reload( LBT2PH.shading )

try:  # import the core honeybee dependencies
    from ladybug_geometry.geometry3d.line import LineSegment3D
    from ladybug_geometry.geometry3d.face import Face3D
    from ladybug_rhino.fromgeometry import from_face3d
    from ladybug_rhino.togeometry import to_face3d, to_linesegment3d, to_point3d    
    from honeybee.aperture import Aperture
    from honeybee.typing import clean_and_id_ep_string
    from honeybee_energy.material.glazing import EnergyWindowMaterialSimpleGlazSys
except ImportError as e:
    raise ImportError('\nFailed to import honeybee:\n\t{}'.format(e))

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
class PHPP_Window(Object):
    '''A PHPP Style 'Window'.

    Args:
        _aperture: A LadybugTools 'aperture' object
    Properties:
        *'quantity'
        * 'aperture',
        * '_tolerance'
        * '_glazing_edge_lengths'
        * '_window_edges'
        * '_glazing_surface'
        * '_shading_factor_winter'
        * '_shading_factor_summer'
        * 'shading_dimensions'
        * 'name'
        * 'frame'
        * 'glazing'
        * 'installs'
        * 'install_depth' 
    '''
    __slots__ = ('quantity', 'aperture',
        '_tolerance', '_glazing_edge_lengths', '_window_edges', '_glazing_surface',
        '_shading_factor_winter', '_shading_factor_summer', 'shading_dimensions',
        'name', 'frame', 'glazing', 'installs', 'install_depth', 'UD_glass_Name',
        'UD_frame_Name' )
    
    Output = namedtuple('Output', ['Left', 'Right', 'Bottom', 'Top'])

    def __init__(self, _aperture=None):
        self.quantity = 1
        self.aperture = _aperture
        self._tolerance = 0.01        
        self._glazing_edge_lengths = None
        self._window_edges = None
        self._glazing_surface = None
        self.UD_glass_Name = None
        self.UD_frame_Name = None
        
        self._shading_factor_winter = None
        self._shading_factor_summer = None
        self.shading_dimensions = None
        
        self.frame = None
        self.glazing = None
        self.installs = None
        self.install_depth = None

    @property
    def name(self):
        return self.aperture.display_name

    @property
    def window_edges(self):
        
        if self._window_edges:
            return self._window_edges
        else:
            # First, try and use the simple Ladubug Veritcal / Horizontal methods
            # If that doesn't work for any reason, those methods return 'None'
            # If any are None, use the slower 'edges in order' method
            result_verticals = self.aperture.geometry.get_left_right_vertical_edges(self._tolerance)
            result_horizontals = self.aperture.geometry.get_top_bottom_horizontal_edges(self._tolerance)
            
            if result_verticals and result_horizontals:
                window_left, window_right = result_verticals
                window_top, window_bottom = result_horizontals
                edges = self.Output(window_left, window_right, window_bottom, window_top)    
            else:
                edges = self._get_edges_in_order()

            self._window_edges = edges
            return edges

    @property
    def glazing_edge_lengths(self):
        if self._glazing_edge_lengths:
            return self._glazing_edge_lengths
        else:
            edges = self.window_edges
            frame = self.frame

            glazing_Left = edges.Left.length - frame.fTop - frame.fBottom
            glazing_Right = edges.Right.length - frame.fTop - frame.fBottom
            glazing_Bottom = edges.Bottom.length - frame.fLeft - frame.fRight
            glazing_Top = edges.Top.length - frame.fLeft - frame.fRight

            edge_lens = self.Output(glazing_Left, glazing_Right, glazing_Bottom, glazing_Top)
            self._glazing_edge_lengths = edge_lens
            return edge_lens

    @property
    def glazing_surface(self):
        if self._glazing_surface:
            return self._glazing_surface
        else:
            geom = self.inset_window_surface

            # Create the frame and instet surfaces
            WinCenter = ghc.Area(geom).centroid
            WinNormalVector = self.surface_normal
            
            #Create the Inset Perimeter Curve
            WinEdges = ghc.DeconstructBrep(geom).edges
            WinPerimeter = ghc.JoinCurves(WinEdges, False)
            FrameWidth = self.frame.fLeft

            InsetCurve = rs.OffsetCurve(WinPerimeter, WinCenter, FrameWidth, WinNormalVector, 0)
            
            # In case the curve goes 'out' and the offset fails
            # Or is too small and results in multiple offset Curves
            if len(InsetCurve)>1:
                warning = 'Error. The window named: "{}" is too small. The frame offset of {} m can not be done. Check the frame sizes?'.format(self.Name, FrameWidth)
                print(warning)
                
                InsetCurve = rs.OffsetCurve(WinPerimeter, WinCenter, 0.05, WinNormalVector, 0)
                InsetCurve = rs.coercecurve( InsetCurve[0] )
            else:
                InsetCurve = rs.coercecurve( InsetCurve[0] )
            
            srfc = ghc.BoundarySurfaces(InsetCurve)
            self._glazing_surface = srfc
            return srfc

    @property
    def u_w_installed(self):
        
        frame = self.frame
        glazing_edge_lens = self.glazing_edge_lengths
        window_edges = self.window_edges
        window_area = self.aperture.area
        glazing_area = glazing_edge_lens.Left * glazing_edge_lens.Bottom
        
        # Correct for the corner overlap
        corner_areas = []
        corner_areas.append(frame.fLeft * frame.fTop + frame.fLeft * frame.fBottom)
        corner_areas.append(frame.fRight* frame.fTop + frame.fRight * frame.fBottom)
        corner_areas.append(frame.fLeft * frame.fBottom + frame.fRight * frame.fBottom)
        corner_areas.append(frame.fLeft* frame.fTop + frame.fRight * frame.fTop)
        frame_areas = ((e.length*w)-(0.5*ca) for e, w, ca in izip(window_edges, frame.frameWidths, corner_areas))

        # Calc the heat-loss values for all the elements
        hl_glazing = glazing_area * self.glazing.uValue
        hl_frames = sum(a*u for a, u in izip(frame_areas, frame.uValues))
        hl_glazing_edge = sum(e_len*psi_g for e_len, psi_g in izip(glazing_edge_lens, frame.PsiGVals))
        hl_install_edge = sum(e.length*psi_i*i for e, psi_i, i in izip(window_edges, frame.PsiInstalls, self.installs))

        u_w_installed = (hl_glazing + hl_frames + hl_glazing_edge + hl_install_edge) / window_area

        return u_w_installed
    
    @property
    def host_surface(self):
        return self.aperture.parent.display_name.replace('EXT_', '')

    @property
    def height(self):
        left, right = self.aperture.geometry.get_left_right_vertical_edges(self._tolerance)
        return left.length

    @property
    def width(self):
        top, bottom = self.aperture.geometry.get_top_bottom_horizontal_edges(self._tolerance)
        return top.length

    @property
    def shading_factor_winter(self):
        try:
            return float(self._shading_factor_winter)
        except Exception as e:
            return 0.75

    @shading_factor_winter.setter
    def shading_factor_winter(self, _in):
        try:
            self._shading_factor_winter = float(_in)
        except ValueError as e:
            print(e)
            print('Shading Factor must be a number.')

    @property
    def shading_factor_summer(self):
        try:
            return float(self._shading_factor_summer)
        except Exception as e:
            return 0.75
    
    @shading_factor_summer.setter
    def shading_factor_summer(self, _in):
        try:
            self._shading_factor_summer= float(_in)
        except ValueError as e:
            print(e)
            print('Shading Factor must be a number.')

    @property
    def rh_surface(self):
        """Get the LBT Aperture 'Face3d' as a Rhino surface"""
        
        if self.aperture:
            lbt_face3d = self.aperture.geometry
            rh_surface = from_face3d( lbt_face3d )
            return rh_surface
        else:
            return None

    @property
    def surface_normal(self):
        """ Convert the LBT normal to a real Rhino normal """
        
        lbt_norm = self.aperture.normal
        x = lbt_norm.x
        y = lbt_norm.y
        z = lbt_norm.z

        return Rhino.Geometry.Vector3d(x, y, z)

    @property
    def reveal_geometry(self):
        """Create reveal (side) geometry for the window edges"""
        
        orientation = -1 # don't rememeber why this is.....
        window_surface = self.rh_surface
        if not window_surface:
            return None

        # ----------------------------------------------------------------------
        # Get the inputs
        edges = self._get_edges_in_order( window_surface )
        inst_depth = float(self.install_depth)
        normal = self.surface_normal * orientation

        # ----------------------------------------------------------------------
        # Create the reveal geom
        bottom = self._extrude_reveal_edge(edges.bottom, normal, inst_depth, self.installs.install_B)
        left = self._extrude_reveal_edge(edges.left, normal, inst_depth, self.installs.install_L)
        top = self._extrude_reveal_edge(edges.top, normal, inst_depth, self.installs.install_T)
        right = self._extrude_reveal_edge(edges.right, normal, inst_depth, self.installs.install_R)
        
        # ----------------------------------------------------------------------
        # Output
        RevealGeom = namedtuple('RevealGeom', ['left', 'right', 'bottom', 'top'])
        output = RevealGeom( left, right, bottom, top )
        
        return output

    @property
    def inset_window_surface(self):
        """Moves the window geometry based on the InstallDepth param """
        orientation = -1 # don't remember why this is...

        transform_vector = ghc.Amplitude(self.surface_normal, float(self.install_depth) * orientation)
        transformed_surface = ghc.Move(self.rh_surface, transform_vector).geometry
        return transformed_surface

    @staticmethod
    def _get_vector_from_center_to_edge(_surface, _surface_plane):
        """ Find a Vector from center of surface to mid-point on each edge.
        
        Arguments:
            _surface: The Rhino surface to analyze.
            _surface_plane: A Plane aligned to the surface.
        Returns:
            edgeVectors: (List) Vector3D for mid-point on each edge
        """
        
        worldOrigin = Rhino.Geometry.Point3d(0,0,0)
        worldXYPlane = ghc.XYPlane(worldOrigin)
        geomAtWorldZero = ghc.Orient(_surface, _surface_plane, worldXYPlane).geometry
        edges = ghc.DeconstructBrep(geomAtWorldZero).edges
        
        # Find the mid-point for each edge and create a vector to that midpoint
        crvMidPoints = [ ghc.CurveMiddle(edge) for edge in edges ]
        edgeVectors = [ ghc.Vector2Pt(midPt, worldOrigin, False).vector for midPt in crvMidPoints ]
        
        return edgeVectors

    @staticmethod
    def _calc_edge_angle_about_center(_vectorList):
        """Take in a list of vectors. Calculate the Vector angle about the center
        
        Note: The 'center' is (0,0,0). Will calculate around 360 degrees (clockwise)
        and return values in degrees not radians.
        
        Arguments:
            _vectorList: (list) Vectors to the surface's edges
        Returns:
            vectorAngles: (List) Float values of Degrees for each Vector input
        """
        
        vectorAngles = []
        
        refAngle = ghc.UnitY(1)
        x2 = refAngle.X
        y2 = refAngle.Y
        
        for vector in _vectorList:
            x1 = vector.X
            y1 = vector.Y
            
            # Calc the angle between
            angle = math.atan2(y2, x2) - math.atan2(y1, x1)
            angle = angle * 360 / (2 * math.pi)
            
            if angle < 0:
                angle = angle + 360
            
            angle = round(angle, 0)
            
            if angle >359.9 or angle < 0.001:
                angle = 0
            
            vectorAngles.append(angle)
        
        return vectorAngles
    
    @staticmethod
    def _get_plane_aligned_to_surface(_surface):
        """Finds an Aligned Plane for Surface input
        
        Note, will try and correct to make sure the aligned plane's Y-Axis aligns 
        to the surface and goes 'up' (world Z) if it can.
        
        Arguments:
            _surface: The Rhino surface to align with
        Returns:
            srfcPlane: A single Plane object, aligned to the surface
        """
        
        # Get the UV info for the surface
        srfcPlane = rs.SurfaceFrame(_surface, [0.5, 0.5])
        centroid = ghc.Area(_surface).centroid
        uVector = srfcPlane.XAxis
        vVector = srfcPlane.YAxis
        
        # Create a Plane aligned to the UV of the srfc
        lineU = ghc.LineSDL(centroid, uVector, 1)
        lineV = ghc.LineSDL(centroid, vVector, 1)
        srfcPlane = ghc.Line_Line(lineU, lineV)
        
        # Try and make sure its pointing the right directions
        if abs(round(srfcPlane.XAxis.Z, 2)) != 0:
            srfcPlane =  ghc.RotatePlane(srfcPlane, ghc.Radians(90))
        if round(srfcPlane.YAxis.Z, 2) < 0:
            srfcPlane =  ghc.RotatePlane(srfcPlane, ghc.Radians(180))
        
        return srfcPlane

    def _get_edges_in_order(self):
        """Sort the surface edges using the Degree about center as the Key
        
        Ordering yields edges in the order Bottom / Left / Top / Right
        repackege them unto L/R/B/T for output
        """

        analysis_surface = self.rh_surface

        srfcPlane = self._get_plane_aligned_to_surface( analysis_surface )
        vectorList = self._get_vector_from_center_to_edge( analysis_surface, srfcPlane)
        edgeAngleDegrees = self._calc_edge_angle_about_center(vectorList)
        srfcEdges_Unordered = ghc.DeconstructBrep(analysis_surface).edges
        srfcEdges_Ordered = ghc.SortList( edgeAngleDegrees, srfcEdges_Unordered).values_a
        
        # Convert all the Rhino lines to Ladybug LineSegments before output
        _bottom, _left, _top, _right = srfcEdges_Ordered

        _left = self._my_lb_line_constructor(_left)
        _right = self._my_lb_line_constructor(_right)
        _bottom = self._my_lb_line_constructor(_bottom)
        _top = self._my_lb_line_constructor(_top)

        output = self.Output(_left, _right, _bottom, _top)
        return output

    @staticmethod
    def _my_lb_line_constructor(_line):
        """Cus' the 'to_line_segment' method has an error (thinks second pt is a vector) """

        p1 = to_point3d(_line.PointAtStart)
        p2 = to_point3d(_line.PointAtEnd) 
        line = LineSegment3D.from_end_points(p1, p2)

        return line

    @staticmethod
    def _extrude_reveal_edge(_geom, _direction, _extrudeDepth, _install):
        """Extrudes edge in some direction, guards against 0 extrude """
        
        if _install == 0 or _extrudeDepth == 0:
            return None
        else:
            return ghc.Extrude( _geom, ghc.Amplitude(_direction, _extrudeDepth) )

    def to_dict(self):
        d = {}

        d.update( {'quantity':self.quantity} )
        d.update( {'_tolerance':self._tolerance} )
        d.update( {'aperture':self.aperture.to_dict()} )
        d.update( {'_shading_factor_winter':self._shading_factor_winter } )
        d.update( {'_shading_factor_summer':self._shading_factor_summer} )
        d.update( {'install_depth':self.install_depth} )

        _edges = {}
        for k, v in self.window_edges._asdict().iteritems():
            _edges.update( {k:v.to_dict()} )
        d.update( {'_window_edges':_edges} )
        d.update( {'_glazing_edge_lengths':self.glazing_edge_lengths})
        
        _glazing_srfc = to_face3d(self.glazing_surface)
        if _glazing_srfc:
            d.update( {'_glazing_surface':_glazing_srfc[0].to_dict()} )
        
        if self.frame:
            d.update( {'_frame':self.frame.to_dict()} )

        if self.glazing:
            d.update( {'_glazing':self.glazing.to_dict()} )
        
        if self.installs:
            d.update( {'_installs':self.installs.to_dict()} )

        if self.shading_dimensions:
            d.update( {'shading_dimensions':self.shading_dimensions.to_dict() } )

        return d

    @classmethod
    def from_dict(cls, _dict):
        
        new_obj = cls()
        new_obj.quantity = _dict.get('quantity')
        new_obj._tolerance = _dict.get('_tolerance')
        new_obj.aperture = Aperture.from_dict( _dict.get('aperture') )
        new_obj._shading_factor_winter =_dict.get('_shading_factor_winter')
        new_obj._shading_factor_summer =_dict.get('_shading_factor_summer')
        new_obj._glazing_edge_lengths = _dict.get('_glazing_edge_lengths')

        #----
        _edges = _dict.get('_window_edges', {})
        _left = _edges.get('Left')
        _left = LineSegment3D.from_dict( _left )

        _right = _edges.get('Right')
        _right = LineSegment3D.from_dict( _right )

        _bottom = _edges.get('Bottom')
        _bottom = LineSegment3D.from_dict( _bottom )

        _top = _edges.get('Top')
        _top = LineSegment3D.from_dict( _top )      
        
        new_obj._window_edges = cls.Output(_left, _right, _bottom, _top)
        #----
        
        _glazing_surface = _dict.get('_glazing_surface')
        _glazing_surface = Face3D.from_dict(_glazing_surface)
        _glazing_surface = from_face3d(_glazing_surface)
        new_obj._glazing_surface = _glazing_surface

        new_obj.install_depth = _dict.get('install_depth')

        new_obj.frame = LBT2PH.windows.PHPP_Frame.from_dict( _dict.get('_frame') )
        new_obj.glazing = LBT2PH.windows.PHPP_Glazing.from_dict( _dict.get('_glazing') )
        new_obj.installs = LBT2PH.windows.PHPP_Installs.from_dict( _dict.get('_installs') )
        new_obj.shading_dimensions = LBT2PH.shading.PHPP_Shading_Dims.from_dict( _dict.get('shading_dimensions') )        

        return new_obj
    
    def __unicode__(self):
        return u'A PHPP-Style Window Object: < {} >'.format(self.name)
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
       return "{}( _aperture={!r})".format(
            self.__class__.__name__, self.aperture)
    def ToString(self):
        return str(self)


#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
class PHPP_Frame(Object):
    ''' For Storing PHPP Style Frame Parameters       
     Args:
        _nm (str): The name of the Frame Type
        _uValues (list): A list of the 4 U-Values (W/m2k) for the frame sides (Left, Right, Bottom, Top)
        _frameWidths (list): A list of the 4 U-Values (W/m2k) for the frame sides (Left, Right, Bottom, Top)
        _psiGlazings (list): A list of the 4 Psi-Values (W/mk) for the glazing spacers (Left, Right, Bottom, Top)
        _psiInstalls (list): A list of the 4 Psi-Values (W/mk) for the frame Installations (Left, Right, Bottom, Top)
        _chiGlassCarrier (list): A value for the Chi-Value (W/k) of the glass carrier for curtain walls
    Properties:
        * name
        * _uValues
        * frameWidths
        * PsiGVals
        * PsiInstalls
        * chiGlassCarrier
        * uValues
        * display_name
    '''

    attr_names_u = ['uLeft', 'uRight', 'uBottom', 'uTop']
    attr_names_f = ['fLeft', 'fRight', 'fBottom', 'fTop']
    attr_names_psi_g = ['psigLeft', 'psigRight', 'psigBottom', 'psigTop']
    attr_names_psi_inst = ['psiInstLeft', 'psiInstRight', 'psiInstBottom', 'psiInstTop']
    
    def __init__(self, 
                _nm='Default Frame',
                _uValues=[1.0]*4,
                _frameWidths=[0.1]*4,
                _psiGlazings=[0.04]*4,
                _psiInstalls=[0.04]*4,
                _chiGlassCarrier=None):

        self._name = _nm
        self._uValues = _uValues
        self._frameWidths = _frameWidths
        self._PsiGVals = _psiGlazings
        self._PsiInstalls = _psiInstalls
        self.chiGlassCarrier = _chiGlassCarrier
        
        self._setup_attributes(self.attr_names_u, self._uValues)
        self._setup_attributes(self.attr_names_f, self._frameWidths)
        self._setup_attributes(self.attr_names_psi_g, self._PsiGVals)
        self._setup_attributes(self.attr_names_psi_inst, self._PsiInstalls)
    
    @property
    def name(self):
        nm = self._name
        nm = nm.replace('PHPP_CONST_', '')
        nm = nm.replace('PHPP_MAT_', '')
        return nm

    @name.setter
    def name(self, _in):
        if _in:
            self._name = _in

    @property
    def uValues(self):
        d = []
        for attr in self.attr_names_u:
            d.append( getattr(self, attr) )
        
        return d

    @uValues.setter
    def uValues(self, _in):
        clean_input = self._clean_list( _in )
        
        if clean_input:
            self._uValues = clean_input
            self._setup_attributes(self.attr_names_u, clean_input)

    @property
    def frameWidths(self):
        d = []
        for attr in self.attr_names_f:
            d.append( getattr(self, attr) )

        return d

    @frameWidths.setter
    def frameWidths(self, _in):
        clean_input = self._clean_list( _in )
        
        if clean_input:
            self._frameWidths = clean_input
            self._setup_attributes(self.attr_names_f, clean_input) 

    @property
    def PsiGVals(self):
        d = []
        for attr in self.attr_names_psi_g:
            d.append( getattr(self, attr) )

        return d

    @PsiGVals.setter
    def PsiGVals(self, _in):
        clean_input = self._clean_list( _in )
        
        if clean_input:
            self._PsiGVals = clean_input
            self._setup_attributes(self.attr_names_psi_g, clean_input) 

    @property
    def PsiInstalls(self):
        d = []
        for attr in self.attr_names_psi_inst:
            d.append( getattr(self, attr) )

        return d

    @PsiInstalls.setter
    def PsiInstalls(self, _in):
        clean_input = self._clean_list( _in )
        
        if clean_input:
            self._PsiInstalls = clean_input
            self._setup_attributes(self.attr_names_psi_inst, clean_input) 

    @staticmethod
    def _clean_list( _in ):
        try:
            output = float(_in)
            return [output]*4
        except AttributeError:
            if None in _in:
                return None
                
            if len(_in) == 4:
                return _in
            else:
                return [_in[0]]*4
        except SystemError:
            pass
        except ValueError:
            pass

    def _setup_attributes(self, _attr_name_list, _value_list):
        """Used to set multiple attributes from a 4-element list """
        
        for i, attr_name in enumerate(_attr_name_list):
            val = float(_value_list[i])
            setattr(self, attr_name, val)
    
    def to_dict(self):
        d = {}

        d.update( {'name':self.name} )
        d.update( {'uValues':self.uValues} )
        d.update( {'frameWidths':self.frameWidths} )
        d.update( {'PsiGVals':self.PsiGVals} )
        d.update( {'PsiInstalls':self.PsiInstalls} )
        d.update( {'chiGlassCarrier':self.chiGlassCarrier} )
        
        return d
    
    @classmethod
    def from_dict(cls, _dict):
        new_obj = cls()

        new_obj._name = _dict.get('name')
        new_obj.uValues = _dict.get('uValues')
        new_obj.frameWidths = _dict.get('frameWidths')
        new_obj.PsiGVals = _dict.get('PsiGVals')
        new_obj.PsiInstalls = _dict.get('PsiInstalls')
        new_obj.chiGlassCarrier = _dict.get('chiGlassCarrier')

        return new_obj
    
    @classmethod
    def from_HB_Const( cls, _aperture_construction ):
        new_obj = cls()
        
        new_obj.name = _aperture_construction.display_name
        new_obj.uValues = _aperture_construction.u_factor

        return new_obj

    def __unicode__(self):
        return u'A PHPP Style Frame Object: < {self.name} >'.format(self=self)
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
       return "{}( _nm={!r}, _uValues={!r}, _frameWidths={!r}, _psiGlazings={!r}, "\
              "_psiInstalls={!r}, _chiGlassCarrier={!r} )".format(
               self.__class__.__name__,
               self.name,
               self.uValues,
               self.frameWidths,
               self.PsiGVals,
               self.PsiInstalls,
               self.chiGlassCarrier )



#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
class PHPP_Glazing(Object):
    """ For storing PHPP Style Glazing Parameters """
    
    def __init__(self, _nm='Default Glazing', _gValue=0.4, _uValue=1.0):
        """
        Args:
            _nm (str): The name of the glass type
            _gValue (float): The g-Value (SHGC) value of the glass only as per EN 410 (%)
            _uValue (float): The Thermal Trasmittance value of the center of glass (W/m2k) as per EN 673
        """

        self.name = _nm
        self._gValue = _gValue
        self._uValue = _uValue
    
    @property
    def gValue(self):
        return float(self._gValue)

    @property
    def uValue(self):
        return float(self._uValue)

    @uValue.setter
    def uValue(self, _in):
        if _in:
            self._uValue = _in

    @property
    def display_name(self):
        nm = self.name
        nm = nm.replace('PHPP_CONST_', '')
        nm = nm.replace('PHPP_MAT_', '')
        
        return nm

    def to_dict(self):
        d = {}

        d.update( {'name':self.display_name} )
        d.update( {'gValue':self.gValue} )
        d.update( {'uValue':self.uValue} )
        
        return d

    @classmethod
    def from_dict(cls, _dict):
        new_obj = cls()

        new_obj.name = _dict.get('name')
        new_obj._gValue = _dict.get('gValue')
        new_obj._uValue = _dict.get('uValue')

        return new_obj

    @classmethod
    def from_HB_Const( cls, _aperture_construction ):
        new_obj = cls()
        new_obj.name = _aperture_construction.display_name
        new_obj.uValue = _aperture_construction.u_factor

        return new_obj

    def __unicode__(self):
        return u'A PHPP Style Glazing Object: < {} >'.format(self.display_name)
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
       return "{}( _nm={!r}, _gValue={!r}, _uValue={!r} )".format(
               self.__class__.__name__,
               self.display_name,
               self.gValue,
               self.uValue)
    def ToString(self):
        return str(self)



#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
class PHPP_Installs(Object):
    """ For storing the install conditions (0|1) of each edge in a window component """
    
    def __init__(self, _install_L=1, _install_R=1, _install_B=1, _install_T=1 ):
        """
        Args:
            _install_L (int: str: bool:): 1 | 0, 'True' | 'False' or True | False
            _install_R (int: str: bool:): 1 | 0, 'True' | 'False' or True | False
            _install_B (int: str: bool:): 1 | 0, 'True' | 'False' or True | False
            _install_T (int: str: bool:): 1 | 0, 'True' | 'False' or True | False
        """
        self._install_L = _install_L
        self._install_R = _install_R
        self._install_T = _install_T
        self._install_B = _install_B

    @property
    def install_L(self):
        return self._install_L
    
    @install_L.setter
    def install_L(self, _in):
        try:
            self._install_L = int(_in)
        except ValueError:
            if str(_in).upper() == 'FALSE':
                self._install_L = 0
            else:
                self._install_L = 1

    @property
    def install_R(self):
        return self._install_R
    
    @install_R.setter
    def install_R(self, _in):
        try:
            self._install_R = int(_in)
        except ValueError:
            if str(_in).upper() == 'FALSE':
                self._install_R = 0
            else:
                self._install_R = 1

    @property
    def install_B(self):
        return self._install_B
    
    @install_B.setter
    def install_B(self, _in):
        try:
            self._install_B = int(_in)
        except ValueError:
            if str(_in).upper() == 'FALSE':
                self._install_B = 0
            else:
                self._install_B = 1

    @property
    def install_T(self):
        return self._install_T
    
    @install_T.setter
    def install_T(self, _in):
        try:
            self._install_T = int(_in)
        except ValueError:
            if str(_in).upper() == 'FALSE':
                self._install_T = 0
            else:
                self._install_T = 1

    @property
    def values_as_list(self):
        return [self.install_L, self.install_R, self.install_B, self.install_T]
    
    @property
    def named_values(self):
        Output = namedtuple('Output', ['Left', 'Right', 'Bottom', 'Top'])
        return Output(self.install_L, self.install_R, self.install_B, self.install_T)

    def __iter__(self):
        return self.values_as_list

    def __len__(self):
        return len(self.values_as_list)

    def to_dict(self):
        d = {}

        d.update( {'_install_L':self.install_L} )
        d.update( {'_install_R':self.install_R} )
        d.update( {'_install_T':self.install_T} )
        d.update( {'_install_B':self.install_B} )

        return d

    @classmethod
    def from_dict(cls, _dict):
        new_obj = cls()

        new_obj._install_L = _dict.get('_install_L')
        new_obj._install_R = _dict.get('_install_R')
        new_obj._install_T = _dict.get('_install_T')
        new_obj._install_B = _dict.get('_install_B')

        return new_obj

    def __unicode__(self):
        return u'A PHPP Style Window Install Object: < L={self.install_L} | R={self.install_R} | T={self.install_T} | B={self.install_B} >'.format(self=self)
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
       return "{}( _install_L={!r} )".format(
               self.__class__.__name__, self._install_L)
    def ToString(self):
        return str(self)


#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def create_EP_window_mat(_win_obj):
    """ Creates an E+ style material for the window based on the PHPP U-W-Installed

    Args:
        _win_obj (): The PHPP-Style window object
    Returns:
        mat: The window E+ Material
    
    """

    # Material properties
    name = 'PHPP_MAT_{}'.format(_win_obj.name)
    u_factor = _win_obj.u_w_installed
    shgc = _win_obj.glazing.gValue
    t_vis = 0.6

    # Create the material
    mat = EnergyWindowMaterialSimpleGlazSys(
        clean_and_id_ep_string(name), u_factor, shgc, t_vis)
    mat.display_name = name

    return mat


#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def create_EP_const(_win_EP_material):
    """ Creates an 'E+' style construction for the window

    Args:
        _win_EP_material (): The E+ Material for the window
    Returns:
        constr (): The new E+ Construction for the window
    """

    try:  # import the core honeybee dependencies
        from honeybee.typing import clean_and_id_ep_string
    except ImportError as e:
        raise ImportError('\nFailed to import honeybee:\n\t{}'.format(e))

    try:  # import the honeybee-energy dependencies
        from honeybee_energy.construction.window import WindowConstruction
        from honeybee_energy.lib.materials import window_material_by_identifier
    except ImportError as e:
        raise ImportError('\nFailed to import honeybee_energy:\n\t{}'.format(e))
    
    material_objs = []
    for material in [_win_EP_material]:
        if isinstance(material, str):
            material = window_material_by_identifier(material)
        material_objs.append(material)
    
    name = 'PHPP_CONST_{}'.format(_win_EP_material.display_name)

    constr = WindowConstruction(clean_and_id_ep_string(name), material_objs)
    constr.display_name = name

    return constr


#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def build_frame_and_glass_objs_from_RH_doc(_ghdoc):
    """ Loads window-type entries from DocumentUseText library of the Active Rhino doc.

        Note, it determines if its a 'window-type' entry by looking for the 
        string "PHPP_lib_Glazing", "PHPP_lib_Frame" or "_PsiInstall_" in the key
         
    Args:
        _ghdoc (ghdoc): The 'ghdoc' object from the Grasshopper document.
    Returns:
        PHPPLibrary_ (dict): A dictionary of all the window-type entries
            found with their parameters.
    """
    
    PHPPLibrary_ = {'lib_GlazingTypes':{}, 'lib_FrameTypes':{}, 'lib_PsiInstalls':{}}
    lib_GlazingTypes = {}
    lib_FrameTypes = {}
    lib_PsiInstalls = {}

    with LBT2PH.helpers.context_rh_doc(_ghdoc):
        # First, try and pull in the Rhino Document's PHPP Library
        # And make new Frame and Glass Objects. Add all of em' to new dictionaries
        if not rs.IsDocumentUserText():
            return PHPPLibrary_
        
        for eachKey in rs.GetDocumentUserText():
            if 'PHPP_lib_Glazing' in eachKey:
                tempDict = json.loads(rs.GetDocumentUserText(eachKey))
                newGlazingObject = PHPP_Glazing(
                                tempDict['Name'],
                                tempDict['gValue'],
                                tempDict['uValue']
                                )
                lib_GlazingTypes[tempDict['Name']] = newGlazingObject
            elif '_PsiInstall_' in eachKey:
                tempDict = json.loads(rs.GetDocumentUserText(eachKey))
                newPsiInstallObject = PHPP_Installs(
                                [
                                tempDict['Left'],
                                tempDict['Right'],
                                tempDict['Bottom'],
                                tempDict['Top']
                                ]
                                )
                lib_PsiInstalls[tempDict['Typename']] = newPsiInstallObject
            elif 'PHPP_lib_Frame' in eachKey:
                tempDict = json.loads(rs.GetDocumentUserText(eachKey))
                newFrameObject = PHPP_Frame()
                newFrameObject.name = tempDict.get('Name', 'Unnamed Frame')
                newFrameObject.uValues = [
                                tempDict.get('uFrame_L', 1.0), tempDict.get('uFrame_R', 1.0),
                                tempDict.get('uFrame_B', 1.0), tempDict.get('uFrame_T', 1.0) ]
                newFrameObject.frameWidths =[
                                tempDict.get('wFrame_L', 0.12), tempDict.get('wFrame_R', 0.12),
                                tempDict.get('wFrame_B', 0.12), tempDict.get('wFrame_T', 0.12) ]
                newFrameObject.PsiGVals = [
                                tempDict.get('psiG_L', 0.04), tempDict.get('psiG_R', 0.04),
                                tempDict.get('psiG_B', 0.04), tempDict.get('psiG_T', 0.04) ]
                newFrameObject.Installs = [
                                tempDict.get('psiInst_L', 0.04), tempDict.get('psiInst_R', 0.04),
                                tempDict.get('psiInst_B', 0.04), tempDict.get('psiInst_T', 0.04) ]
                   
                lib_FrameTypes[ newFrameObject.name ] = newFrameObject
        
        PHPPLibrary_['lib_GlazingTypes'] = lib_GlazingTypes
        PHPPLibrary_['lib_FrameTypes'] = lib_FrameTypes
        PHPPLibrary_['lib_PsiInstalls'] = lib_PsiInstalls
    
    return PHPPLibrary_
