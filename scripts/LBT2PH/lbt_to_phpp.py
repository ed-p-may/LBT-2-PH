import Grasshopper.Kernel as ghK
import Rhino.Geometry.Vector2d
import rhinoscriptsyntax as rs
import math
import json
from collections import OrderedDict

import LBT2PH.materials
import LBT2PH.assemblies
import LBT2PH.windows
import LBT2PH.spaces

reload(LBT2PH.materials)
reload(LBT2PH.assemblies)
reload(LBT2PH.windows)
reload(LBT2PH.spaces)

try:  # import the core honeybee dependencies
    from honeybee.model import Model
    from honeybee.boundarycondition import Surface, Outdoors, Ground, Adiabatic
    from honeybee.facetype import Wall, RoofCeiling, Floor
except ImportError as e:
    raise ImportError('\nFailed to import honeybee:\n\t{}'.format(e))

class PHPP_Zone:
    def __init__(self, _room):
        self.hb_room = _room
        self.phpp_spaces = self._create_phpp_spaces()
        self.ScheduleName = 'Schedule Name'
        self.DesignFlowRate = 'Design Flow Rate'
        self.FlowRatePerFloorArea = 'Flow per Zone Floor Area'
        self.FlowRatePerSurfaceArea =  'Flow per Exterior Surface Area'
        self.ACH = 'Air Changes per Hour'
    
    @property
    def Name(self):
        return self.hb_room.display_name

    @property
    def ZoneName(self):
        return self.hb_room.display_name

    @property
    def floor_area_gross(self):
        return self.hb_room.floor_area

    @property
    def n50(self):
        # Get the basic parameters needed
        blower_pressure = 50.0 #Pa
        normal_avg_pressure = 4.0 #Pa
        q50 = self.hb_room.properties.energy.infiltration.flow_per_exterior_area

        # Determine the ACH from the q50 value
        infil_flow_rate_at_normal_pressure = q50 * self.hb_room.exposed_area
        factor =  math.pow((blower_pressure/normal_avg_pressure), 0.63)
        infil_flow_rate_at_50PA = factor * infil_flow_rate_at_normal_pressure   # m3/s
        infil_flow_rate_at_50PA = infil_flow_rate_at_50PA * 3600                # m3/hr
        n50 = infil_flow_rate_at_50PA / self.vn50

        return n50

    @property
    def vn50(self):
        vn50_total = sum([space.space_vn50 for space in self.phpp_spaces])
        return vn50_total

    def _create_phpp_spaces(self):
        spaces = []
        try:
            for space_dict in self.hb_room.user_data['phpp']['spaces'].values():
                new_space = LBT2PH.spaces.Space.from_dict(space_dict)
                spaces.append( new_space )
        except KeyError as e:
            print(e)

        return spaces

    def __unicode__(self):
        return u'A PHPP-Style Zone/HB-Room Object: < {self.Name} >'.format(self=self)
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
       return "{}(_room={!r})".format(
            self.__class__.__name__, self.hb_room)

class PHPP_Surface:
    def __init__(self, _lbt_face, _rm_name, _rm_id, _scene_north_vec, _ghenv):
        self.lbt_srfc = _lbt_face
        self.HostZoneName = _rm_name
        self.HostZoneID = _rm_id
        self.scene_north_vector = self.calc_scene_north_vector()
        self.ghenv = _ghenv
        self.Factor_Shading = 0.5
        self.Factor_Absorptivity = 0.6
        self.Factor_Emissivity = 0.9
    
    def calc_scene_north_vector(_input_vector):
        ''' 
        Arguments:
            _input_vector: Vector2d or an anlge representing the scene's North direction 
        Returns:
            north_vector:
        '''
        
        default_north_vector = north_vec = Rhino.Geometry.Vector2d(0,1)
        
        if _input_vector is None:
            return default_north_vector
        
        if isinstance(_input_vector, Rhino.Geometry.Vector2d):
            return _input_vector
        
        try:
            angle = float(_input_vector)
            return default_north_vector
        except:
            return default_north_vector

    @property
    def Name(self):
        try:
            lbt_srfc_name = self.lbt_srfc.display_name
            clean_name = lbt_srfc_name.replace('EXT_', '')
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
        
        x2 = self.scene_north_vector.X
        y2 = self.scene_north_vector.Y
        
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
        return u'A PHPP-Style Surface Object: < {self.Name} >'.format(self=self)
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
       return "{}(_lbt_face={!r})".format(
            self.__class__.__name__, self.lbt_srfc)

def get_zones_from_model(_model):
    zones = []
    
    for room in _model.rooms:
        new_room = PHPP_Zone(room)
        zones.append(new_room)
    
    return zones

def get_exposed_surfaces_from_model(_model, _north, _ghenv):
    exposed_surfaces = []

    for room in _model.rooms: 
        room_name = room.display_name
        room_id = room.identifier
        
        for face in room:       
            bc = face.boundary_condition

            if bc != 'Surface':
                phpp_srfc = PHPP_Surface(face, room_name, room_id, _north, _ghenv )
                exposed_surfaces.append(phpp_srfc)
    
    return exposed_surfaces

def get_opaque_materials_from_model(_model, _ghenv):
    ep_materials = {}
    for face in _model.faces:
        for mat in face.properties.energy.construction.materials:
            ep_materials[mat.identifier] = mat

    phpp_materials = []
    for k, v in ep_materials.items():
        new_material = LBT2PH.materials.PHPP_Material_Opaque(v)
        phpp_materials.append(new_material)

    return phpp_materials

def get_opaque_constructions_from_model(_model, _ghenv):
    ep_constructions = {}
    for face in _model.faces:
        construction = face.properties.energy.construction
        ep_constructions[construction.identifier] = construction
    
    phpp_constructions = []
    for k, v in ep_constructions.items():
        new_construction = LBT2PH.assemblies.PHPP_Construction(v)
        phpp_constructions.append(new_construction)
    
    return phpp_constructions

def get_aperture_materials_from_model(_model):
    ep_mats = OrderedDict()
    for aperture in _model.apertures:
        for mat in aperture.properties.energy.construction.materials:
            ep_mats[mat.identifier] = mat
    
    phpp_materials = []
    for i, (k, v) in enumerate(ep_mats.items()):
        ud_num = i+1
        new_window_material = LBT2PH.materials.PHPP_Material_Window_EP(v, ud_num)
        phpp_materials.append(new_window_material)

    return phpp_materials

def get_aperture_constructions_from_model(_model):
    ep_constructions = {}
    for aperture in _model.apertures:
        construction = aperture.properties.energy.construction
        ep_constructions[construction.identifier] = construction

    phpp_constructions = []
    for k, v in ep_constructions.items():
        new_construction = LBT2PH.assemblies.PHPP_Construction(v)
        phpp_constructions.append(new_construction)
    
    return phpp_constructions        

def get_aperture_surfaces_from_model(_model, _ghdoc):
    ''' Returns a list of PHPP_Window objects found in the HB Model '''
    
    phpp_apertures = []
    
    for hb_aperture in _model.apertures:
        try:
            window_dict = hb_aperture.user_data['phpp']
            new_phpp_aperture = LBT2PH.windows.PHPP_Window.from_dict( window_dict )
            new_phpp_aperture.aperture = hb_aperture
            new_phpp_aperture.rh_library = LBT2PH.windows.get_rh_doc_window_library(_ghdoc)
            
            phpp_apertures.append(new_phpp_aperture)
        except KeyError as e:
            print(e)

    return phpp_apertures


    apertures = []
    for aperture in _model.apertures:
        try: params = aperture.user_data['phpp']['aperture_params']
        except: params = {}

        rh_doc_window_library = LBT2PH.windows.get_rh_doc_window_library(_ghdoc)
        new_window = LBT2PH.windows.PHPP_Window(aperture, params, rh_doc_window_library)
        apertures.append(new_window)

    return apertures




def get_spaces_from_model(_model, _ghdoc):
    ''' Returns a list of PHPP_Space objects found in the HB Model '''
    rooms = []

    for room in _model.rooms:
        if isinstance(room.user_data, dict):
            spaces_dict = room.user_data
        elif isinstance(room.user_data, str):
            spaces_dict = json.loads(room.user_data)
        else:
            print('Error loading PHPP space data')
            spaces_dict = {}
            return []

        if not spaces_dict.has_key('phpp'):
            print('Honeybee Room has no "phpp" data?')
            return []

        if not spaces_dict['phpp'].has_key('spaces'):
            print('Honeybee Room user_data.phpp has no key "spaces"?')
            return []

        for space_data in spaces_dict['phpp']['spaces'].values():
            space_obj = LBT2PH.spaces.Space.from_dict(space_data)
            rooms.append(space_obj)
    
    return rooms

def get_ventilation_systems_from_model(_model, _ghenv):
    model_vent_systems = set()
    for hb_room in _model.rooms:
        if not hb_room.user_data.has_key('phpp'):
            return []
        
        if not hb_room.user_data['phpp'].has_key('vent_system'):
            return []
        
        vent_system_dict = hb_room.user_data['phpp']['vent_system']
        room_vent_system = LBT2PH.ventilation.PHPP_Sys_Ventilation.from_dict(vent_system_dict, _ghenv)
        model_vent_systems.add(room_vent_system)

    return list(model_vent_systems)
