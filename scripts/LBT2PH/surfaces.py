import System
import rhinoscriptsyntax as rs
import helpers
import Grasshopper.Kernel as ghK
from collections import namedtuple
import Rhino
import math

class Temp_Surface:
    ''' A temporary holder for some surface stuff. Used to be just a nametuple.. '''

    def __init__(self, _geom=None, _params=None):
        self.geom = _geom
        self.params = _params

    def __iter__(self):
        return (i for i in (self.geom, self.params))

class hb_surface:
    ''' Simple class to organize data for a 'surface'. Used to set up data for a HB-Face Component
    
    Args:
        _srfc: <Surface> A single 'Surface' object with .geom and .param properties
        _constructions: <Dict> A dict of all the EP Constructions
    Properties:
        * geometry
        * name
        * type
        * type_legacy
        * bc
        * const 
        * rad_mod   
    '''
    __slots__ = ('_geo', '_params', '_constructions', 'rad_mod')

    srfc_type_schema = {
        'Wall': {'legacy':0, 'lbt1': 'Wall'},
        'WALL': {'legacy':0, 'lbt1': 'Wall'},
        'UndergroundWall': {'legacy':0.5, 'lbt1': 'Wall'},
        'ROOF': {'legacy':1, 'lbt1': 'RoofCeiling'},
        'Roof': {'legacy':1, 'lbt1': 'RoofCeiling'},
        'UndergroundCeiling': {'legacy':1.5, 'lbt1': 'Wall'},
        'FLOOR': {'legacy':2, 'lbt1': 'Floor'},
        'Floor': {'legacy':2, 'lbt1': 'Floor'},
        'UndergroundSlab': {'legacy':2.25, 'lbt1': 'Floor'},
        'SlabOnGrade': {'legacy':2.5, 'lbt1': 'Floor'},
        'ExposedFloor': {'legacy':2.75, 'lbt1': 'Floor'},
        'RoofCeiling': {'legacy':3, 'lbt1': 'RoofCeiling'},
        'CEILING': {'legacy':3, 'lbt1': 'RoofCeiling'},
        'AIRWALL': {'legacy':4, 'lbt1': 'AirBoundary'},
        'WINDOW':  {'legacy':5, 'lbt1': 'Wall'},
        'SHADING': {'legacy': 6, 'lbt1': 'Wall'}
        }
        
    def __init__(self, _srfc, _constructions, _ghenv):
        self._geo = _srfc.geom
        self._params = _srfc.params
        self._constructions = _constructions
        self.rad_mod = None
        self._warn_no_name(_ghenv)
    
    def _warn_no_name(self, _ghenv):
        nm = self._params.get('Object Name', None)
        if nm is None or nm == 'None':
            warning = "Warning: Some Surfaces look like they are missing names? It is likely that\n"\
            "the Honeybee solveAdjc component will not work correctly without names.\n"\
            "This is especially true for 'interior' surfaces up against other thermal zones.\n"\
            "Please apply a unique name to all surfaces before proceeding. Use the\n"\
            "IDF2PH 'Set Window Names' tool to do this automatically (works on regular srfcs too)"
            _ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, warning)
    
    def _add_ext_flag_to_name(self, _ud_value):
        """ So that the EP Results can be properly sorted at the very end, add an EXT or INT flag to the srfc"""
        if self.bc is None:
            return 'EXT_' + str(_ud_value)
        elif 'Adiabatic' in self.bc:
            return 'INT_' + str(_ud_value)
        else: 
            return 'EXT_' + str(_ud_value)    

    def _get_srfc_type(self, _ud_value, _version):
        try:
            assert type(_ud_value) == str, '_ud_value input should be str'
            return self.srfc_type_schema.get(_ud_value, {_version:'Wall'}).get(_version, 'Wall')
        except: 
            return 'Wall'

    @property
    def geometry(self):
        return self._geo

    @property
    def name(self):
        try:
            ud_value = self._params.get('Object Name', 'No Name')
            ud_value = self._add_ext_flag_to_name(ud_value)
            return ud_value
        except:
            return 'No Name'

    @property
    def type(self):
        ud_value = self._params.get('srfType', 'Wall')
        return self._get_srfc_type(ud_value, 'lbt1')

    @property
    def type_legacy(self):
        ud_value = self._params.get('srfType', 'Wall')
        return self._get_srfc_type(ud_value, 'legacy')

    @property
    def bc(self):
        return self._params.get('EPBC', 'Outdoors')
 
    @property
    def const(self):
        ud_value = self._params.get('EPConstruction', None)
        if ud_value is None:
            return None
        
        ud_value = 'PHPP_CONST_' + str(ud_value).upper()
        ud_value = ud_value.replace(' ', '_')
        return self._constructions.get(ud_value, ud_value)
        
def get_rh_srfc_params(_srfc_GUIDs, _ghenv, _ghdoc):
    ''' Pulls geom and UserText params from the Rhino scene.

    Args:
        _srfc_GUIDs: <list: Guid:> A list of the surface GUID numbers.
        _ghenv: The <ghenv> object from the Grasshopper component calling this function
        _ghdoc: The <ghDoc> object from the Grasshopper component calling this function
    Returns:
        surfaces: A List of surface objects. Each object has a .geom and a .param property
    '''
    
    surfaces = []
    
    for srfc_GUID in _srfc_GUIDs:
        # --- Get UserText params
        srfc_user_text = _get_surface_rh_userText(srfc_GUID, _ghenv, _ghdoc)
        
        # --- Get Geometry
        with helpers.context_rh_doc(_ghdoc):
            surface_geom = rs.coercebrep(srfc_GUID)
        
        new_srfc_obj = Temp_Surface(surface_geom, srfc_user_text)
        surfaces.append(new_srfc_obj)

    return surfaces

def determine_surface_type_by_orientation(_surfaces):
    ''' Determines the 'type' of surface automatically, based on its surface normal.

    Args:
        _surfaces: <List: Surface:> A List of Surface objects with a .geom and a .params attribute.
    Returns:
        surface_type: A new list of Surface objs with their Surface Type modified as appropriate
    '''
    
    assert type(_surfaces) == list, "'_surfaces' input should be a list"
    
    surfaces = []
    for srfc_geom, srfc_params in _surfaces:
        # Code here adapted from Honeybee Legacy 'decomposeZone' method
        # Checks the surface normal and depending on the direction, 
        # assigns it as a 'wall', 'floor' or 'roof'
        
        def find_srfc_normal(_f):
            centroid = Rhino.Geometry.AreaMassProperties.Compute(_f).Centroid
            b, u, v = _f.ClosestPoint(centroid)
            face_normal = _f.NormalAt(u, v)
            return face_normal
        
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
        
        maximumRoofAngle = 30
        try:
            # Find the average surface normal of the srfc
            normals = [find_srfc_normal(face) for face in srfc_geom.Faces]           
            normal = avg_normal_vectors(normals)
        
            # --- Find the surface type based on the normal
            angle2Z = math.degrees(Rhino.Geometry.Vector3d.VectorAngle(normal, Rhino.Geometry.Vector3d.ZAxis))

            if  angle2Z < maximumRoofAngle or angle2Z > 360 - maximumRoofAngle:
                srfc_type = 'RoofCeiling'
                bc = 'Outdoors'
            elif  160 < angle2Z <200:
                srfc_type = 'Floor'
                bc = 'Ground'
            else: 
                srfc_type = 'Wall'
                bc = 'Outdoors'
        except:
            print('Failed to find surface normal. Are you sure it is a surface?')
            srfc_type = 'Wall'
            bc = 'Outdoors'
        
        srfc_params['srfType'] = srfc_type
        srfc_params['EPBC'] = bc
        new_srfc_obj = Temp_Surface(srfc_geom, srfc_params)
        surfaces.append(new_srfc_obj)

    return surfaces

def _get_surface_rh_userText(_srfc_GUID, _ghdoc, _ghenv):
    ''' Takes in an objects GUID and returns the full dictionary of
    Attribute UserText Key and Value pairs. Cleans up a bit as well.
    
    Args:
        _GUID: <Guid> the Rhino GUID of the surface object to try and read from
    Returns:
        output_dict: a dictionary object with all the keys / values found in the Object's UserText
    '''
    output_dict = {}
    
    if _srfc_GUID.GetType() != System.Guid:
        remark = "Unable to get parameter data for the surface? If trying to pull data\n"\
        "from Rhino, be sure the '_srfc' input Type Hint is set to 'Guid'\n"\
        "For now, using default values for all surface parameter values."
        _ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Remark, remark)
        return output_dict
    
    with helpers.context_rh_doc(_ghdoc):
        output_dict['Object Name'] = rs.ObjectName(_srfc_GUID) # Always get the name
        
        for eachKey in rs.GetUserText(_srfc_GUID):
            if 'Object Name' not in eachKey:
                val =  rs.GetUserText(_srfc_GUID, eachKey)
                if val != 'None':
                    output_dict[eachKey] = val
                else:
                    output_dict[eachKey] = None
    
    return output_dict
