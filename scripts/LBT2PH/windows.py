import rhinoscriptsyntax as rs
import Rhino
import ghpythonlib.components as ghc
import json
import math
from System import Object

import LBT2PH.helpers
import LBT2PH.shading
from ladybug_rhino.fromgeometry import from_face3d 
from honeybee.aperture import Aperture

reload( LBT2PH.shading )

from collections import namedtuple

class PHPP_Window(Object):
    '''  Class to organize data for a 'window'.
    Args:
        _aperture: A LadybugTools 'aperture' object
        _params: <dict> A dict with a 'phpp' key and parameter values
        _rh_doc_library: The Rhino document window library from the document UserText
    Properties:
        * quantity
        * _tolerance
        * aperture
        * params
        * rh_library
        * _shading_dimensions
        * _shading_factor_winter
        * _shading_factor_summer
    '''
    
    def __init__(self, _aperture=None, _params=None, _rh_doc_library=None):
        self.quantity = 1
        self._tolerance = 0.01
        self.aperture = _aperture
        self.params = _params
        self.rh_library = _rh_doc_library
        self._shading_dimensions = None
        self._shading_factor_winter = None
        self._shading_factor_summer = None
        self.shading_dimensions = None
    
    @property
    def name(self):
        nm = self.params.get('Object Name', None)
        if nm is None:
            nm = self.aperture.display_name 
        return nm

    @property
    def frame(self):      
        # 1) Try and create glazing from user_data params
        # 2) Try and create glazing from UserText params
        # 3) If all fails, return a default Frame object
        
        frame_val = (self.params.get('FrameType', None))
        try:
            d = json.loads( frame_val )
            nm = d['_nm']
            uValues = d['_uValues']
            frameWidths = d['_frameWidths']
            psiGlazings = d['_psiGlazings']
            psiInstalls = d['_psiInstalls']
            chiGlassCarrier = d['_chiGlassCarrier']

            frame_object = PHPP_Frame(nm, uValues, frameWidths, psiGlazings, psiInstalls, chiGlassCarrier)
            return frame_object
        except:
            frame_object = self.rh_library['lib_FrameTypes'].get(frame_val, None )
            
            if frame_object:
                return frame_object
            else:
                # Since no PHPP params, use the EP/HB Construction values
                nm = self.aperture.properties.energy.construction.display_name
                uVal = self.aperture.properties.energy.construction.u_factor

            if nm and uVal:
                frame =  PHPP_Frame(_nm=nm, _uValues=[uVal]*4, _frameWidths=[0.1]*4,
                                    _psiGlazings=[0]*4, _psiInstalls=[0]*4)
                return frame
            else:
                return PHPP_Frame()

    @property
    def glazing(self):
        # 1) Try and create glazing from user_data params
        # 2) Try and create glazing from UserText params
        # 3) If all fails, return a default Glazing object

        glazing_val = (self.params.get('GlazingType', None))
        try:
            d = json.loads( glazing_val )
            nm = d['_nm']
            gVal = d['_gValue']
            uVal = d['_uValue']
            
            glazing_object = PHPP_Glazing(nm, gVal, uVal)
            return glazing_object
        except:
            glazing_object = self.rh_library['lib_GlazingTypes'].get(glazing_val, None )
            
            if glazing_object:
                return glazing_object
            else:
                # Since no PHPP params, use the EP/HB Construction values
                nm = self.aperture.properties.energy.construction.display_name
                uVal = self.aperture.properties.energy.construction.u_factor

                if nm and uVal:
                    return PHPP_Glazing(_nm=nm, _gValue=0.4, _uValue=uVal)        
                else:
                    return PHPP_Glazing()
  
    @property
    def window_edges(self):
        window_left, window_right = self.aperture.geometry.get_left_right_vertical_edges(self._tolerance)
        window_top, window_bottom = self.aperture.geometry.get_top_bottom_horizontal_edges(self._tolerance)
        
        Output = namedtuple('Output', ['Left', 'Right', 'Bottom', 'Top'])
        return Output(window_left, window_right, window_bottom, window_top)

    @property
    def glazing_edge_lengths(self):
        glazing_Left = self.window_edges.Left.length - self.frame.fTop - self.frame.fBottom
        glazing_Right = self.window_edges.Right.length - self.frame.fTop - self.frame.fBottom
        glazing_Bottom = self.window_edges.Bottom.length - self.frame.fLeft - self.frame.fRight
        glazing_Top = self.window_edges.Top.length - self.frame.fLeft - self.frame.fRight
        
        Output = namedtuple('Output', ['Left', 'Right', 'Bottom', 'Top'])
        return Output(glazing_Left, glazing_Right, glazing_Bottom, glazing_Top)

    @property
    def glazing_surface(self):
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
        
        return ghc.BoundarySurfaces(InsetCurve)

    @property
    def installs(self):
        def _str_to_bool(_):
            try:
                return int(_)
            except:
                if 'FALSE' == str(_).upper():
                    return 0
                return 1

        left = _str_to_bool(self.params.get('InstallLeft', 1))
        right = _str_to_bool(self.params.get('InstallRight', 1))
        bottom = _str_to_bool(self.params.get('InstallBottom', 1))
        top = _str_to_bool(self.params.get('InstallTop', 1))
        
        Output = namedtuple('Output', ['Left', 'Right', 'Bottom', 'Top'])
        return Output(left, right, bottom, top)

    @property
    def install_depth(self):
        try:
            inst_depth = self.params.get('InstallDepth', None)
            return float(inst_depth)
        except:
            return 0.1

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
        frame_areas = [(e.length*w)-(0.5*ca) for e, w, ca in zip(window_edges, frame.frameWidths, corner_areas)]

        # Calc the heat-loss values for all the elements
        hl_glazing = glazing_area * self.glazing.uValue
        hl_frames = sum([a*u for a, u in zip(frame_areas, frame.uValues)])
        hl_glazing_edge = sum([e_len*psi_g for e_len, psi_g in zip(glazing_edge_lens, frame.PsiGVals)])
        hl_install_edge = sum([e.length*psi_i*i for e, psi_i, i in zip(window_edges, frame.PsiInstalls, self.installs)])
        
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

    def _get_edges_in_order(self, _surface):
        """Sort the surface edges using the Degree about center as the Key"""

        srfcPlane = self._get_plane_aligned_to_surface( _surface )
        vectorList = self._get_vector_from_center_to_edge( _surface, srfcPlane)
        edgeAngleDegrees = self._calc_edge_angle_about_center(vectorList)
        srfcEdges_Unordered = ghc.DeconstructBrep(_surface).edges
        srfcEdges_Ordered = ghc.SortList( edgeAngleDegrees, srfcEdges_Unordered).values_a
        
        Edges = namedtuple('Edges', ['bottom', 'left', 'top', 'right'])
        output = Edges(*srfcEdges_Ordered)
        return output

    @staticmethod
    def _extrude_reveal_edge(_geom, _direction, _extrudeDepth, _install):
        """Extrudes edge in some direction, guards against 0 extrude """
        
        if _install == 0 or _extrudeDepth == 0:
            return None
        else:
            return ghc.Extrude( _geom, ghc.Amplitude(_direction, _extrudeDepth) )

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
        inst_depth = self.install_depth
        normal = self.surface_normal * orientation

        # ----------------------------------------------------------------------
        # Create the reveal geom
        bottom = self._extrude_reveal_edge(edges.bottom, normal, inst_depth, self.installs.Bottom)
        left = self._extrude_reveal_edge(edges.left, normal, inst_depth, self.installs.Left)
        top = self._extrude_reveal_edge(edges.top, normal, inst_depth, self.installs.Top)
        right = self._extrude_reveal_edge(edges.right, normal, inst_depth, self.installs.Right)
        
        # ----------------------------------------------------------------------
        # Output
        RevealGeom = namedtuple('RevealGeom', ['left', 'right', 'bottom', 'top'])
        output = RevealGeom( left, right, bottom, top )
        
        return output

    @property
    def inset_window_surface(self):
        """Moves the window geometry based on the InstallDepth param """
        orientation = -1 # don't remember why this is...
        
        transform_vector = ghc.Amplitude(self.surface_normal, self.install_depth*-1)
        transformed_surface = ghc.Move(self.rh_surface, transform_vector).geometry
        
        return transformed_surface

    def rh_lib_to_dict(self):
        
        a = {}
        for key, val in self.rh_library.items():
            b = { }
            if val:
                for k, v in val.items():
                   b.update( {k:v.to_dict()} )

            a.update( {key:b} )
        
        return a

    @staticmethod
    def rh_lib_from_dict(_dict):
        a = {}
        for k, v in _dict.items():
            b = {}
            if 'GLAZING' in k.upper():
                for glazing in v.values():
                    obj = PHPP_Glazing.from_dict( glazing)
                    b.update( {obj.name:obj} )
            elif 'FRAME' in k.upper():
                for frame in v.values():
                    obj = PHPP_Frame.from_dict( frame )
                    b.update( {obj.name:obj} )
            elif 'INSTALL' in k.upper():
                obj = PHPP_Installs.from_dict( v )
                b.update( {obj.name:obj} )
            
            a.update( {k:b} )

        return a

    def to_dict(self):
        d = {}
        d.update( {'quantity':self.quantity} )
        d.update( {'_tolerance':self._tolerance} )
        d.update( {'aperture':self.aperture.to_dict()} )
        d.update( {'params':self.params} )
        d.update( {'rh_library':self.rh_lib_to_dict() } )
        d.update( {'_shading_factor_winter':self._shading_factor_winter } )
        d.update( {'_shading_factor_summer':self._shading_factor_summer} )

        if self.shading_dimensions:
            d.update( {'shading_dimensions':self.shading_dimensions.to_dict() } )

        return d

    @classmethod
    def from_dict(cls, _dict):
        
        new_obj = cls()
        new_obj.quantity = _dict.get('quantity')
        new_obj._tolerance = _dict.get('_tolerance')
        new_obj.aperture = Aperture.from_dict( _dict.get('aperture') )
        new_obj.params = _dict.get('params')
        new_obj.rh_library = cls.rh_lib_from_dict( _dict.get('rh_library') )
        new_obj._shading_factor_winter =_dict.get('_shading_factor_winter')
        new_obj._shading_factor_summer =_dict.get('_shading_factor_summer')
        shading_dims = LBT2PH.shading.PHPP_Shading_Dims.from_dict( _dict.get('shading_dimensions') )        
        new_obj.shading_dimensions = shading_dims
        return new_obj

    def __unicode__(self):
        return u'A PHPP-Style Window Object: < {} >'.format(self.name)
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
       return "{}( _aperture={!r}, _params={!r}, _rh_doc_library={!r})".format(
            self.__class__.__name__,
            self.aperture,
            self.params,
            self.rh_library)

class PHPP_Frame:
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
    
    def __init__(self, 
                _nm='Default Frame',
                _uValues=[1.0]*4,
                _frameWidths=[0.1]*4,
                _psiGlazings=[0.04]*4,
                _psiInstalls=[0.04]*4,
                _chiGlassCarrier=None):

        self.name = _nm
        self._uValues = _uValues
        self.frameWidths = _frameWidths
        self.PsiGVals = _psiGlazings
        self.PsiInstalls = _psiInstalls
        self.chiGlassCarrier = _chiGlassCarrier
        
        self.cleanAttrSet(['uLeft', 'uRight', 'uBottom', 'uTop'], self.uValues)
        self.cleanAttrSet(['fLeft', 'fRight', 'fBottom', 'fTop'], self.frameWidths)
        self.cleanAttrSet(['psigLeft', 'psigRight', 'psigBottom', 'psigTop'], self.PsiGVals)
        self.cleanAttrSet(['psiInstLeft', 'psiInstRight', 'psiInstBottom', 'psiInstTop'], self.PsiInstalls)
    
    @property
    def uValues(self):
        if self._uValues is None:
            return [0.1]*4
        
        if len(self._uValues) == 4:
            return self._uValues
        else:
            return [self._uValues]*4

    @property
    def display_name(self):
        nm = self.name
        nm = nm.replace('PHPP_CONST_', '')
        nm = nm.replace('PHPP_MAT_', '')
        return nm

    def cleanAttrSet(self, _inList, _attrList):
        # In case the input len != 4 and convert to float values
        if len(_attrList) != 4:
            try:
                val = float(_attrList[0])
            except:
                val = _attrList[0]
            
            for each in _inList:
                setattr(self, each, val)
        else:
            for i, each in enumerate(_inList):
                try:
                    val = float(_attrList[i])
                except:
                    val = _attrList[i]
                
                setattr(self, _inList[i], val)
    
    def to_dict(self):
        d = {}

        d.update( {'name':self.display_name} )
        d.update( {'uValues':self.uValues} )
        d.update( {'frameWidths':self.frameWidths} )
        d.update( {'PsiGVals':self.PsiGVals} )
        d.update( {'PsiInstalls':self.PsiInstalls} )
        d.update( {'chiGlassCarrier':self.chiGlassCarrier} )
        
        return d
    
    @classmethod
    def from_dict(cls, _dict):
        new_obj = cls()

        new_obj.name = _dict.get('name')
        new_obj._uValues = _dict.get('uValues')
        new_obj.frameWidths = _dict.get('frameWidths')
        new_obj.PsiGVals = _dict.get('PsiGVals')
        new_obj.PsiInstalls = _dict.get('PsiInstalls')
        new_obj.chiGlassCarrier = _dict.get('chiGlassCarrier')

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

class PHPP_Glazing:
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
        try:
            return float(self._gValue)
        except:
            return None
    
    @property
    def uValue(self):
        try:
            return float(self._uValue)
        except:
            return None
    
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

class PHPP_Installs:
    """ For storing the install conditions (0|1) of each edge in a window component """
    
    def __init__(self, _installs=[1]*4):
        """
        Args:
            _installs (list): A list of four 'install' types (Left, Right, Bottom, Top)
        """
        self.Installs = _installs
        self.name = 'Installs_Obj'
        self.setInstalls()
        
    def setInstalls(self):
        # In case the number of installs passed != 4, use the first one for all of them
        if len(self.Installs) != 4:
            self.Inst_L = float(self.Installs[0]) if self.Installs[0] != None else 'Auto'
            self.Inst_R = float(self.Installs[0]) if self.Installs[0] != None else 'Auto'
            self.Inst_B = float(self.Installs[0]) if self.Installs[0] != None else 'Auto'
            self.Inst_T = float(self.Installs[0]) if self.Installs[0] != None else 'Auto'
        else:
            self.Inst_L = float(self.Installs[0]) if self.Installs[0] != None else 'Auto'
            self.Inst_R = float(self.Installs[1]) if self.Installs[1] != None else 'Auto'
            self.Inst_B = float(self.Installs[2]) if self.Installs[2] != None else 'Auto'
            self.Inst_T = float(self.Installs[3]) if self.Installs[3] != None else 'Auto'
    
    @property
    def values_as_list(self):
        return [int(self.Inst_L), int(self.Inst_R), int(self.Inst_B), int(self.Inst_T)]
    
    @property
    def values(self):
        Output = namedtuple('Output', ['Left', 'Right', 'Bottom', 'Top'])
        return Output(self.Inst_L, self.Inst_R, self.Inst_B, self.Inst_T)

    def to_dict(self):
        d = {}

        d.update( {'Installs':self.Installs} )
        d.update( {'name':self.name} )

        return d

    @classmethod
    def from_dict(cls, _dict):
        new_obj = cls()

        new_obj.Installs = _dict.get('Installs')
        new_obj.name = _dict.get('name')

        return new_obj

    def __unicode__(self):
        return u'A PHPP Style Window Install Object: < L={self.Inst_L} | R={self.Inst_R} | T={self.Inst_T} | B={self.Inst_B} >'.format(self=self)
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
       return "{}( _installs={!r} )".format(
               self.__class__.__name__, self.Installs)

def create_EP_window_mat(_win_obj):
    """ Creates an E+ style material for the window based on the PHPP U-W-Installed

    Args:
        _win_obj (): The PHPP-Style window object
    Returns:
        mat: The window E+ Material
    
    """
    try:  # import the core honeybee dependencies
        from honeybee.typing import clean_and_id_ep_string
    except ImportError as e:
        raise ImportError('\nFailed to import honeybee:\n\t{}'.format(e))

    try:  # import the honeybee-energy dependencies
        from honeybee_energy.material.glazing import EnergyWindowMaterialSimpleGlazSys
    except ImportError as e:
        raise ImportError('\nFailed to import honeybee_energy:\n\t{}'.format(e))

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

def get_rh_doc_window_library(_ghdoc):
    """ Loads window-type entries from DocumentUseText library of the Active Rhino doc.

        Note, it determines if its a 'window-type' entry by looking for the 
        string "PHPP_lib_Glazing", "PHPP_lib_Frame" or "_PsiInstall_" in the key
         
    Args:
        _ghdoc (ghdoc): The 'ghdoc' object from the Grasshopper document.
    Returns:
        PHPPLibrary_ (dict): A dictionary of all the window-type entries
            found with their parameters.
    """
    
    PHPPLibrary_ = {}
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
                newFrameObject = PHPP_Frame(
                                tempDict['Name'],
                                [
                                tempDict['uFrame_L'],
                                tempDict['uFrame_R'],
                                tempDict['uFrame_B'],
                                tempDict['uFrame_T']
                                ],
                                [
                                tempDict['wFrame_L'],
                                tempDict['wFrame_R'],
                                tempDict['wFrame_B'],
                                tempDict['wFrame_T']
                                ],
                                [
                                tempDict['psiG_L'],
                                tempDict['psiG_R'],
                                tempDict['psiG_B'],
                                tempDict['psiG_T']
                                ],
                                [
                                tempDict['psiInst_L'],
                                tempDict['psiInst_R'],
                                tempDict['psiInst_B'],
                                tempDict['psiInst_T']
                                ]
                                )
                lib_FrameTypes[tempDict['Name']] = newFrameObject
        
        PHPPLibrary_['lib_GlazingTypes'] = lib_GlazingTypes
        PHPPLibrary_['lib_FrameTypes'] = lib_FrameTypes
        PHPPLibrary_['lib_PsiInstalls'] = lib_PsiInstalls
    
    return PHPPLibrary_

def get_rh_obj_usertext(_guid):
    """ Get the UserText dictionary for a Rhino Object 
    
    Args:
        _guid (Guid): The Rhino Guid of the object
    Returns:
        user_text_dict (dict): A dictionary of all the key:value pairs found
            in the UserText dictionary
    """
    
    if _guid is None: return {}

    rh_obj = Rhino.RhinoDoc.ActiveDoc.Objects.Find( _guid )
    user_text_dict = {k:rs.GetUserText(rh_obj, k) for k in rs.GetUserText(rh_obj)}
    
    return user_text_dict

def get_rh_window_obj_params(_ghdoc, _window_guid):
    """ Get any Rhino-side parameter data for the Window

    Note: this only works in Rhino v6.0+ I believe...
    
    Args:
        _ghdoc (ghdoc): The 'ghdoc' object from the Grasshopper document.
        _window_guid (Rhino Guid): The Rhino Guid of the window.
    Returns:
        window_rh_params_dict (dict): A dictionary of all the data found
            in the Rhino object's UserText library.
    """
    
    with LBT2PH.helpers.context_rh_doc(_ghdoc):
        window_rh_params_dict = get_rh_obj_usertext(_window_guid)
        
        # Fix the name
        window_name = rs.ObjectName(_window_guid)
        window_rh_params_dict['Object Name'] = window_name

    return window_rh_params_dict