import System
import rhinoscriptsyntax as rs
import helpers
import Grasshopper.Kernel as ghK
import Rhino
import math
import random
from collections import namedtuple

try:  # import the core honeybee dependencies
    from honeybee.boundarycondition import Surface, Outdoors, Ground, Adiabatic
    from honeybee.facetype import Wall, RoofCeiling, Floor
    import ladybug_geometry
    from ladybug_rhino.togeometry import to_face3d
except ImportError as e:
    raise ImportError('\nFailed to import honeybee:\n\t{}'.format(e))

class Temp_Surface:
    """ A temporary holder for some surface stuff. Used to be just a nametuple.. """

    def __init__(self, _geom=None, _params=None):
        self.geom = _geom
        self.params = _params

    def __iter__(self):
        return (i for i in (self.geom, self.params))

class hb_surface:
    """ Simple class to organize data for a 'surface'. Used to set up data for a HB-Face Component
    
    Args:
        _srfc: <Surface> A single 'Surface' object with .geom and .param properties
        _constructions: <Dict> A dict of all the EP Constructions
        _ghenv: The Grasshopper 'ghenv' object from the active scene
    Properties:
        * geometry
        * name
        * type
        * type_legacy
        * bc
        * const 
        * rad_mod   
    """

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
        
    def __init__(self, _srfc, _constructions):
        self.id = random.randint(1000,9999)
        self.geometry = _srfc.geom
        self.params = _srfc.params
        self.constructions = _constructions
        self.rad_mod = None
    
    def check_surface_names(self):
        """ Used to provide the user warnings if surfaces without names are found. """
        
        nm = self.params.get('Object Name', None)
        warning = None

        if nm is None or nm == 'None':
            warning = "Warning: Some Surfaces look like they are missing names? It is possible that\n"\
            "the Honeybee 'solveAdjc' component will not work correctly without names.\n"\
            "This is especially true for 'interior' surfaces up against other thermal zones.\n"\
            "If you run into trouble later, maybe try applying a unique name to all surfaces.\n"\
            "For now, I will apply a random/default name to each surface."
    
        return warning

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
    def name(self):
        default_name = 'No_Name_{}'.format(self.id)
        
        try:
            ud_value = self.params.get('Object Name', default_name)
            if str(ud_value) == 'None':
                ud_value = default_name
            
            ud_value = self._add_ext_flag_to_name(ud_value)
            return ud_value
        except:
            return default_name

    @property
    def type(self):
        ud_value = self.params.get('srfType', 'Wall')
        return self._get_srfc_type(ud_value, 'lbt1')

    @property
    def type_legacy(self):
        """Exposure type used by old 'Legacy' Honeybee """
        
        ud_value = self.params.get('srfType', 'Wall')
        return self._get_srfc_type(ud_value, 'legacy')

    @property
    def bc(self):
        return self.params.get('EPBC', 'Outdoors')
 
    @property
    def const(self):
        ud_value = self.params.get('EPConstruction', None)
        if not ud_value:
            return None
        
        ud_value = 'PHPP_CONST_' + str(ud_value).upper()
        ud_value = ud_value.replace(' ', '_')

        return self.constructions.get(ud_value, ud_value)

class PHPP_Surface:
    def __init__(self, _lbt_face, _rm_name, _rm_id, _scene_north_vec, _ghenv):
        self.lbt_srfc = _lbt_face
        self.HostZoneName = _rm_name
        self.HostZoneID = _rm_id
        self.scene_north_vector = self.calc_scene_north_vector(_scene_north_vec)
        self.ghenv = _ghenv
        self.Factor_Shading = 0.5
        self.Factor_Absorptivity = 0.6
        self.Factor_Emissivity = 0.9
    
    def calc_scene_north_vector(self, _input_vector):
        ''' 
        Arguments:
            _input_vector: Vector2d or an anlge representing the scene's North direction 
        Returns:
            north_vector:
        '''

        default_north_vector = Rhino.Geometry.Vector2d(0,1)
        
        if _input_vector is None:
            return default_north_vector
        
        if isinstance(_input_vector, ladybug_geometry.geometry2d.pointvector.Vector2D):
            return _input_vector

        if isinstance(_input_vector, Rhino.Geometry.Vector2d):
            return _input_vector
        
        # If its an angle input, create the vector from the angle
        try:
            angle = float(_input_vector)
            return angle
        except:
            return default_north_vector

    @property
    def Name(self):
        try:
            lbt_srfc_name = self.lbt_srfc.display_name
            clean_name = lbt_srfc_name.replace('EXT_', '').replace('INT_', '')
            return clean_name
        except Exception as e:
            print('Error getting name from the LBT Face?', e)
            return 'NameError'

    @property
    def AssemblyName(self):
        try:
            lbt_val = self.lbt_srfc.properties.energy.construction.display_name
            return lbt_val
        except Exception as e:
            print('Error getting the LBT Face Construction?', e)
            return None

    @property
    def Assembly_ID(self):
        try:
            lbt_val = self.lbt_srfc.properties.energy.construction.identifier
            return lbt_val
        except Exception as e:
            print('Error getting the LBT Face Construction Identifier?', e)
            return None

    @property
    def exposure(self):
        try:
            lbt_exposure = self.lbt_srfc.boundary_condition
            return lbt_exposure
        except Exception as e:
            print('Error getting the LBT BC?', e)
            return None

    @property
    def type(self):
        try:
            lbt_type = self.lbt_srfc.type
            return lbt_type
        except Exception as e:
            print('Error getting the LBT Surface Type?', e)
            return None

    @property
    def GroupNum(self):
        ''' Figure out the 'Group Number' for PHPP based on the Srfc exposure & type '''
        
        bc = self.exposure
        face_type = self.type
        
        if isinstance(bc, (Surface)):
            return None
        elif isinstance(face_type, Wall) and isinstance(bc, (Outdoors)):
            return 8
        elif isinstance(face_type, Wall) and isinstance(bc, (Ground)):
            return 9
        elif isinstance(face_type, RoofCeiling) and isinstance(bc, (Outdoors)):
            return 10
        elif isinstance(face_type, Floor) and isinstance(bc, (Ground)):
            return 11
        elif isinstance(face_type, Floor) and isinstance(bc, (Outdoors)):
            return 12
        elif isinstance(bc, (Adiabatic)):
            return 18
        else:
            groupWarning = "Couldn't figure out the Group Number for surface '{self.Name}'?\n"\
                "It appears to have an exposure of: '{self.exposure}' and a type of: '{self.type}'?\n"\
                "I will give this surface a group type of 13. You may want to overwrite that in PHPP.".format(self=self)
            self.ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, groupWarning)
            return 13

    @property
    def SurfaceArea(self):
        try:
            lbt_val = self.lbt_srfc.area
            return lbt_val
        except Exception as e:
            print('Error getting the LBT Surface Area?', e)
            return None

    @property
    def NormalVector(self):
        try:
            lbt_val = self.lbt_srfc.normal
            return lbt_val
        except Exception as e:
            print('Error getting the LBT Surface Normal?', e)
            return None

    @property
    def Srfc(self):
        try:
            lbt_val = self.lbt_srfc.geometry
            return lbt_val
        except Exception as e:
            print('Error getting the LBT Surface Geometry?', e)
            return None

    @property
    def AngleFromHoriz(self):
        up_vec = Rhino.Geometry.Vector3d(0,0,1)
        face_normal_vec = self.NormalVector
        
        angle = rs.VectorAngle(up_vec, face_normal_vec)
        return angle 

    @property
    def AngleFromNorth(self):
        ''' Uses the Surface's Normal Vector and the project's north angle
        vector and computes the clockwise orientation angle 0--360 between them
        
        http://frasergreenroyd.com/obtaining-the-angle-between-two-vectors-for-360-degrees/
        Results 0=north, 90=east, 180=south, 270=west
        Arguments:
            None
        Returns: 
            angle: the angle off North for the surface (Degrees) clockwise from 0
        '''

        # Get the input Vector's X and Y parts
        x1 = self.NormalVector.x
        y1 = self.NormalVector.y
        
        # Note: ladybug_geometry vectors use lowercase 'x', Rhino uses uppercase 'X'
        try:
            x2 = self.scene_north_vector.X
            y2 = self.scene_north_vector.Y
        except AttributeError as e:
            x2 = self.scene_north_vector.x
            y2 = self.scene_north_vector.y

        # Calc the angle between the vectors
        angle = math.atan2(y2, x2) - math.atan2(y1, x1)
        angle = angle * 360 / (2 * math.pi)
        
        if angle < 0:
            angle = angle + 360
        
        # Return Angle in Degrees
        return angle

    @property
    def Centroid(self):
        try:
            lbt_val = self.lbt_srfc.geometry.centroid
            return lbt_val
        except Exception as e:
            print('Error getting the LBT Surface Centroid?', e)
            return None

    def __unicode__(self):
        return u'A PHPP-Style Surface Object: < {} >'.format(self.Name)
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
       return "{}(_lbt_face={!r})".format(
            self.__class__.__name__, self.lbt_srfc)


def get_input_geom( _input_list, _ghenv ):
    """Gets geom and guid from whatever objects are input as the '_srfcs' """

    _input_num = 0
    output = []
    Geom = namedtuple('Geom', ['geom', 'guid'])

    for i, input_obj in enumerate(_input_list):
        if not input_obj:
            continue
        
        # Get the GUID of the item being input into the component's 0-pos input
        input_guid = _ghenv.Component.Params.Input[_input_num].VolatileData[0][i].ReferenceID
        rh_obj = Rhino.RhinoDoc.ActiveDoc.Objects.Find( input_guid )

        if rh_obj:            
            # Must be some Rhino Geometry being input
            # Try and explode any multi-surface Breps
            # If that fails, must be a Mesh, just pass along without exploding.
            geom = rs.coercegeometry(rh_obj)
            
            # Try and convert whatever it is into a Brep (for Extrusions, etc.)
            try:
                geom = geom.ToBrep()
            except AttributeError as e:
                pass

            try:
                for srfc in geom.Faces:
                    output.append( Geom(srfc, input_guid) )
            except AttributeError as e:
                output.append( Geom(geom, input_guid) )
        else:
            
            # Must be some Grasshopper Geometry being input
            try:
                for srfc in input_obj.Faces:
                    output.append( Geom(srfc, None) )
            except AttributeError as e:
                output.append( Geom(input_obj, None) )
    
    return output

def get_rh_srfc_params(_input_geom, _ghenv, _ghdoc):
    """ Pulls geom and UserText params from the Rhino scene.

    Args:
        _srfc_GUIDs: <list: Guid:> A list of the surface GUID numbers.
        _ghenv: The <ghenv> object from the Grasshopper component calling this function
        _ghdoc: The <ghDoc> object from the Grasshopper component calling this function
    Returns:
        surfaces: A List of surface objects. Each object has a .geom and a .param property
    """
    
    surfaces = []
    
    for item in _input_geom:
        # --- Get UserText params
        srfc_user_text = _get_surface_rh_userText(item.guid, _ghenv, _ghdoc)
        
        new_srfc_obj = Temp_Surface(item.geom, srfc_user_text)
        surfaces.append(new_srfc_obj)

    return surfaces

def determine_surface_type_by_orientation(_surfaces):
    """ Determines the 'type' of surface automatically, based on its surface normal.

    Args:
        _surfaces: <List: Surface:> A List of Surface objects with a .geom and a .params attribute.
    Returns:
        surface_type: A new list of Surface objs with their Surface Type modified as appropriate
    """
    
    surfaces = []
    warnings = {}
    for srfc_geom, srfc_params in _surfaces:
        # Code here adapted from Honeybee Legacy 'decomposeZone' method
        # Checks the surface normal and depending on the direction, 
        # assigns it as a 'wall', 'floor' or 'roof'
        
        def find_srfc_normal(_f):           
            centroid = Rhino.Geometry.AreaMassProperties.Compute(_f).Centroid
            b, u, v = _f.ClosestPoint(centroid)
            face_normal = _f.NormalAt(u, v)

            return face_normal

        maximumRoofAngle = 30
        try:
            #---- Find the surface normal of the srfc
            normal = find_srfc_normal(srfc_geom)

            #---- Find the surface type based on the normal
            angle2Z = math.degrees(Rhino.Geometry.Vector3d.VectorAngle(normal, Rhino.Geometry.Vector3d.ZAxis))
            
            if  angle2Z < maximumRoofAngle or angle2Z > 360 - maximumRoofAngle:
                srfc_type = 'RoofCeiling'
                bc = 'Outdoors'
            elif  160 < angle2Z <200:
                srfc_type = 'Floor'
                bc = 'Ground'

                #---- Warn the user if it should have been a floor, 
                # but wasn't tagged as one.
                msg = "I found a surface which looks like it should be a 'Floor' but is\n"\
                    "not tagged as a floor? To correct this, either:\n"\
                    "    1) Check your Rhino-scene surface assignnements and geometry\n"\
                    "    2) Try setting this component's 'auto-orientation_' intput to 'True'?"\

                ud_srfc_type = srfc_params.get('srfType')
                if ud_srfc_type != 'FLOOR':
                    warnings['Floor'] = {'level':'Warning', 'msg':msg}

            else: 
                srfc_type = 'Wall'
                bc = 'Outdoors'
        except:
            print('Failed to find surface normal. Are you sure it is Brep geometry?')
            srfc_type = 'Wall'
            bc = 'Outdoors'
        
        #--- Build the new surface with the modified params
        nm = srfc_params.get('Object Name')
        new_srfc_params = {
            'Object Name': nm,
            'srfType': srfc_type,
            'EPBC': bc,
            }
        new_srfc_obj = Temp_Surface(srfc_geom, new_srfc_params)
        surfaces.append(new_srfc_obj)

    return surfaces, warnings

def _get_surface_rh_userText(_srfc_GUID, _ghdoc, _ghenv):
    """ Takes in an objects GUID and returns the full dictionary of
    Attribute UserText Key and Value pairs. Cleans up a bit as well.
    
    Args:
        _GUID: <Guid> the Rhino GUID of the surface object to try and read from
        _ghdoc: The Grasshopper Component 'ghdoc' object
        _ghenv: The Grasshopper Component 'ghenv' object
    Returns:
        output_dict: a dictionary object with all the keys / values found in the Object's UserText
    """
    output_dict = {}
    
    if not _srfc_GUID:
        return output_dict

    if _srfc_GUID.GetType() != System.Guid:
        remark = "Unable to get parameter data for the surface? If trying to pull data\n"\
        "from Rhino, be sure the '_srfc' input Type Hint is set to 'Guid'\n"\
        "For now, using default values for all surface parameter values."
        _ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Remark, remark)
        return output_dict
    
    with helpers.context_rh_doc(_ghdoc):
        output_dict['Object Name'] = rs.ObjectName(_srfc_GUID)
        
        for eachKey in rs.GetUserText(_srfc_GUID):
            if 'Object Name' not in eachKey:
                val =  rs.GetUserText(_srfc_GUID, eachKey)
                if val != 'None':
                    output_dict[eachKey] = val
                else:
                    output_dict[eachKey] = None
    
    return output_dict