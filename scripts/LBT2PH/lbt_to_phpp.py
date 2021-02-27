import Grasshopper.Kernel as ghK
import ghpythonlib.components as ghc
import Rhino.Geometry.Vector2d
import rhinoscriptsyntax as rs
import math
import json
from collections import OrderedDict
from collections import namedtuple

import LBT2PH.materials
import LBT2PH.assemblies
import LBT2PH.windows
import LBT2PH.spaces
import LBT2PH.ground
import LBT2PH.dhw
import LBT2PH.appliances
import LBT2PH.climate
import LBT2PH.summer_vent
import LBT2PH.heating_cooling
import LBT2PH.occupancy
import LBT2PH.surfaces

reload(LBT2PH.materials)
reload(LBT2PH.assemblies)
reload(LBT2PH.windows)
reload(LBT2PH.spaces)
reload(LBT2PH.ground)
reload(LBT2PH.dhw)
reload(LBT2PH.appliances)
reload(LBT2PH.climate)
reload(LBT2PH.summer_vent)
reload(LBT2PH.heating_cooling)
reload(LBT2PH.occupancy)
reload(LBT2PH.surfaces)

try:
    import ladybug.epw as epw  
    from ladybug_rhino.fromgeometry import from_face3d
    from ladybug_rhino.togeometry import to_vector2d
except ImportError as e:
    raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))

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
        
        if self.vn50:
            n50 = infil_flow_rate_at_50PA / self.vn50
            return n50
        else:
            return None

    @property
    def vn50(self):
        vn50_total = sum([space.space_vn50 for space in self.phpp_spaces])
        return vn50_total

    def _create_phpp_spaces(self):
        spaces = []
        if not self.hb_room.user_data:
            return spaces
        
        try:
            phpp_spaces = self.hb_room.user_data.get('phpp', {}).get('spaces', {})
            for space_dict in phpp_spaces.values():
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


def rhino_vector2d_from_angle(_angle=0):
    """ Get a Rhino Vector2d from a numeric angle

        Arguments:
            _angle (float): Angle in degrees. Note, this should
            be a positive value representing the degree of
            rotation (about the Z axis) from Y. North 0=0
            West=90, South=180, East=270
    """

    if not _angle:
        return None

    # Use the Grasshopper rotate to create the new vector
    # according to the numeric angle
    origin = Rhino.Geometry.Point3d(0,0,0)
    north_axis = Rhino.Geometry.Vector3d(0,1,0) 
    angle = ghc.Radians(_angle)
    rotation_axis_vec = Rhino.Geometry.Vector3d(0,0,1)
    rotation_axis_line = ghc.LineSDL(origin, rotation_axis_vec, 1)
    north_vec = ghc.RotateAxis(north_axis, angle, rotation_axis_line).geometry

    return north_vec

def _find_north( _north ):
    if _north:
        try:
            # If the input is a vector, convert to ladybug vector2d
            return to_vector2d( _north )
        except AttributeError as e:  
            # If its not an error, must be a number. So first create a Rhino vector
            try:
                rh_vec = rhino_vector2d_from_angle(float(_north))
                return to_vector2d( rh_vec )
            except Exception as e:
                print(e)
                raise e
    else:
        return to_vector2d( Rhino.Geometry.Vector2d(0,1) )

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
            bc = str(face.boundary_condition)
            if bc != 'Surface':
                phpp_srfc = LBT2PH.surfaces.PHPP_Surface(face, room_name, room_id, _north, _ghenv )
                exposed_surfaces.append(phpp_srfc)

    return exposed_surfaces

def get_opaque_materials_from_model(_model, _ghenv):
    phpp_materials = {}
    for face in _model.faces:
        for ep_mat in face.properties.energy.construction.materials:
            if ep_mat.display_name not in phpp_materials:
                phpp_material = LBT2PH.materials.PHPP_Material_Opaque( ep_mat )
                phpp_materials[ep_mat.display_name] = phpp_material
            
    return phpp_materials

def get_opaque_constructions_from_model(_model, _ghenv):
    ep_constructions = {}
    for face in _model.faces:
        construction = face.properties.energy.construction
        ep_constructions[construction.display_name] = construction
    
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

def get_aperture_surfaces_from_model(_model, _ghenv):
    ''' Returns a list of PHPP_Window objects found in the HB Model '''
    
    phpp_apertures = []
    
    for hb_aperture in _model.apertures:
        try:
            window_dict = hb_aperture.user_data.get('phpp', {})
            if not window_dict:
                raise AttributeError

            new_phpp_aperture = LBT2PH.windows.PHPP_Window.from_dict( window_dict )
            new_phpp_aperture.aperture = hb_aperture
            
            phpp_apertures.append(new_phpp_aperture)
        except AttributeError as e:
            try:
                msg = 'I did not find any user-determined info for window: < {} >.\n'\
                    'I will use the basic Honeybee Aperture info for now, but to customize\n'\
                    'this window you can use a PH-Tools "Create PHPP Aperture" Component\n'\
                    'to apply specific PHPP style information to this element.'.format(hb_aperture.display_name)
                _ghenv.Component.AddRuntimeMessage( ghK.GH_RuntimeMessageLevel.Remark, msg)
                
                # Build a basic aperture from the Honeybee only
                new_phpp_aperture = LBT2PH.windows.PHPP_Window.from_aperture(hb_aperture)
                
                phpp_apertures.append(new_phpp_aperture)
            except Exception as e:
                msg = 'Error trying to create the PHPP window for < {} >.\n'\
                    'Make sure that you use a PH-Tools "Create PHPP Aperture" Component\n'\
                    'to apply the PHPP style information to this element.'.format(hb_aperture.display_name)
                _ghenv.Component.AddRuntimeMessage( ghK.GH_RuntimeMessageLevel.Warning, msg)

    return phpp_apertures

def get_spaces_from_model(_model, _ghdoc):
    ''' Returns a list of PHPP_Space objects found in the HB Model '''
    rooms = [] 

    for room in _model.rooms:
        if not room.user_data:
            print('No User_Data dict found for room < {} >.\n'\
            'Ignoring any Space/Room/TFA/Volume info for now.'.format(room.display_name))
            return []
        
        spaces_dict = room.user_data.get('phpp', {}).get('spaces', {})
        for space_data in spaces_dict.values():
            space_obj = LBT2PH.spaces.Space.from_dict( space_data )
            rooms.append(space_obj)
    
    return rooms

def get_ventilation_systems_from_model(_model, _ghenv):
    model_vent_systems = set()
    
    for hb_room in _model.rooms:
        
        if not hb_room.user_data:
            continue
        
        vent_system_dict = hb_room.user_data.get('phpp', {}).get('vent_system', {})
        
        if vent_system_dict:
            room_vent_system = LBT2PH.ventilation.PHPP_Sys_Ventilation.from_dict(vent_system_dict, _ghenv)
            model_vent_systems.add(room_vent_system)

    return list(model_vent_systems)

def get_ground_from_model(_model, _ghenv):  
    ground_objs = []
    
    for hb_room in _model.rooms:      
        if not hb_room.user_data:
            continue

        ground_dict = hb_room.user_data.get('phpp', {}).get('ground', {})
        if not ground_dict:
            continue

        ground_type = ground_dict.get('type', {})
        if '1' in ground_type:
            obj = LBT2PH.ground.PHPP_Ground_Slab_on_Grade.from_dict( ground_dict, _ghenv )
        elif '2' in ground_type:
            obj = LBT2PH.ground.PHPP_Ground_Heated_Basement.from_dict( ground_dict, _ghenv )
        elif '3' in ground_type:
            obj = LBT2PH.ground.PHPP_Ground_Unheated_Basement.from_dict( ground_dict, _ghenv )
        elif '4' in ground_type:
            obj = LBT2PH.ground.PHPP_Ground_Crawl_Space.from_dict( ground_dict, _ghenv )
        else:
            obj = None
    
        if obj:
            ground_objs.append( obj )

    return ground_objs

def get_dhw_systems(_model):
    dhw_systems = []

    for hb_room in _model.rooms:
        if not hb_room.user_data:
            continue

        dhw_dict = hb_room.user_data.get('phpp', {}).get('dhw_systems', {})
        
        for system in dhw_dict.values():
            dhw_systems.append( LBT2PH.dhw.PHPP_DHW_System.from_dict( system ))

    return dhw_systems

def get_appliances(_model):
    appliance_objs = []

    if not _model.user_data:
        print('No User_Data dict found on the model. Ignoring Appliances for now')
        return appliance_objs

    appliances_set_dict = _model.user_data.get('phpp', {}).get('appliances', {})
    appliances_set = LBT2PH.appliances.ApplianceSet.from_dict( appliances_set_dict )
    for app_obj in appliances_set:
        appliance_objs.append(app_obj)

    return appliance_objs

def get_lighting(_model):
    Lighting = namedtuple('Lighting', ['efficacy', 'hb_room_name', 'hb_room_tfa'])

    out = []
    for room in _model.rooms:
        if not room.user_data:
            continue
        
        name = room.display_name
        efficacy =  float( room.user_data.get('phpp', {}).get('appliances', {}).get('lighting_efficacy', 50) )

        space_tfas = []
        for space_dict in room.user_data.get('phpp', {}).get('spaces', {}).values():
            space_tfas.append( float( space_dict.get('_tfa', 0)) )
        space_tfa = sum(space_tfas)

        out.append( Lighting(efficacy, name, space_tfa) )

    return out

def get_climate(_model, _epw_file):
    if not _model.user_data:
        # No user_data, so auto-find the nearest climate based on the EPW file location

        print('No User_Data dict found on the model. Using automatic climate for now.')
        return find_nearest_phpp_climate( _epw_file )
    else:
        # If there IS a user_dict on the model, try and pull the climate info out of it.
        # Try and build a new UD-Climate obj from the dict data.
        # If any of the dict data for Country, Region and Set are None, then
        # use the EPW to find the nearest cliamte instead.

        ud_climate_params = _model.user_data.get('phpp', {}).get('climate', None)

        if ud_climate_params:
            for climate_dict in ud_climate_params.values():
                ud_climate_obj = LBT2PH.climate.PHPP_ClimateDataSet.from_dict( climate_dict )
                
                if ud_climate_obj:
                    return [ ud_climate_obj ]
                else:
                    return find_nearest_phpp_climate( _epw_file )  
        else:
            return find_nearest_phpp_climate( _epw_file )  

def find_nearest_phpp_climate(_epw_file):
    """ Finds the nearest PHPP Climate zone to the EPW Lat / Long 
    
    Methodology copied from the PHPP v 9.6a (SI) Climate worksheet
    """
    
    #---------------------------------------------------------------------------
    # Get the Long and Lat
    if _epw_file:
        try:
            ep = epw.EPW(_epw_file)
            location = ep.location
            latitude = location.latitude
            longitude = location.longitude
        except Exception as e:
            print(e)
            print('Error reading Location from EPW for some reason?')
    else:
        latitude = 40
        longitude = -74
        print('No EPW file input? I will just use NYC then.')

    #---------------------------------------------------------------------------
    # Find the closest PHPP Climate/Location
    climate_data = LBT2PH.climate.phpp_climate_data()
    for each in climate_data:
        eachLat = float(each.get('Latitude', 0))
        eachLong = float(each.get('Longitude', 0))

        a = math.sin(math.pi/180*eachLat)
        b = math.sin(math.pi/180*latitude)
        c = math.cos(math.pi/180*eachLat)
        d = math.cos(math.pi/180*latitude)
        e = math.cos(math.pi/180*(eachLong-longitude))
        f = a * b + c * d * e
        g = max([-1, f])
        h = min([1, g])
        j = math.acos(h)
        kmFromEPWLocation = 6378 * j
        
        each['distToEPW'] = kmFromEPWLocation
    
    climate_data.sort(key=lambda e: e['distToEPW'])
    climate_set_to_use = climate_data[0]
    
    dataSet = climate_set_to_use.get('Dataset', 'US0055b-New York')
    alt = '=J23'
    country = climate_set_to_use.get('Country', 'US-United States of America')
    region = climate_set_to_use.get('Region', 'New York')
    
    climate_set_to_use = LBT2PH.climate.PHPP_ClimateDataSet(dataSet, alt, country, region)
    
    return [ climate_set_to_use ]

def get_footprint( _surfaces ):
    # Finds the 'footprint' of the building for 'Primary Energy Renewable' reference
    # 1) Re-build the Opaque Surfaces
    # 2) Join all the surface Breps into a single brep
    # 3) Find the 'box' for the single joined brep
    # 4) Find the lowest Z points on the box, offset another 10 units 'down'
    # 5) Make a new Plane at this new location
    # 6) Projects the brep edges onto the new Plane
    # 7) Split a surface using the edges, combine back into a single surface
    
    Footprint = namedtuple('Footprint', ['Footprint_surface', 'Footprint_area'])
    
    #----- Build brep
    surfaces = (from_face3d(surface.Srfc) for surface in _surfaces)
    bldg_mass = ghc.BrepJoin( surfaces ).breps
    bldg_mass = ghc.BoundaryVolume(bldg_mass)
    if not bldg_mass:
        return Footprint(None, None)
    
    #------- Find Corners, Find 'bottom' (lowest Z)
    bldg_mass_corners = [v for v in ghc.BoxCorners(bldg_mass)]
    bldg_mass_corners.sort(reverse=False, key=lambda point3D: point3D.Z)
    rect_pts = bldg_mass_corners[0:3]

    #------- Projection Plane
    projection_plane1 = ghc.Plane3Pt(rect_pts[0], rect_pts[1], rect_pts[2])
    projection_plane2 = ghc.Move(projection_plane1, ghc.UnitZ(-10)).geometry
    matrix = rs.XformPlanarProjection(projection_plane2)

    #------- Project Edges onto Projection Plane
    projected_edges = []
    for edge in ghc.DeconstructBrep(bldg_mass).edges:
        projected_edges.append( ghc.Transform( edge, matrix) )

    #------- Split the projection surface using the curves
    l1 = ghc.Line(rect_pts[0], rect_pts[1])
    l2 = ghc.Line(rect_pts[0], rect_pts[2])
    max_length = max(ghc.Length(l1), ghc.Length(l2))

    projection_surface = ghc.Polygon(projection_plane2, max_length*100, 4, 0).polygon
    projected_surfaces = ghc.SurfaceSplit( projection_surface, projected_edges)

    #------- Remove the biggest surface from the set(the background srfc)
    projected_surfaces.sort( key=lambda x: x.GetArea()) 
    projected_surfaces.pop(-1)
    
    #------- Join the new srfcs back together into a single one
    unioned_NURB = ghc.RegionUnion( projected_surfaces )
    unioned_surface = ghc.BoundarySurfaces(unioned_NURB)

    return Footprint(unioned_surface, unioned_surface.GetArea())

def get_thermal_bridges(_model, _ghenv):
    results = []
    try:
        if not _model.user_data:
            raise ValueError
        
        tb_dict = _model.user_data.get('phpp', {}).get('tb', {})
        for tb_obj_dict in tb_dict.values():
            new_obj = LBT2PH.tb.PHPP_ThermalBridge.from_dict( tb_obj_dict )
            results.append( new_obj )
    except TypeError as e:
        msg = 'Error getting the PHPP/tb dict from the model.user_data?'
        msg += str(e)
        _ghenv.Component.AddRuntimeMessage( ghK.GH_RuntimeMessageLevel.Warning, msg)
    except ValueError:
        print('No User_Data dict found on the model. Ignoring Thermal Bridging for now.')

    return results

def get_settings(_model):
    settings_obj = []
    if not _model.user_data:
        print('No User_Data dict found on the model. Ignoring PHPP Settings for now.')
        return settings_obj


    settings_dict = _model.user_data.get('phpp',{}).get('settings',None)
    if settings_dict:
        
        for settings_params in settings_dict.values():
            settings_obj.append( LBT2PH.phpp_setup.PHPP_Verification.from_dict( settings_params ) )
        return settings_obj
    else:
        return settings_obj

def get_summ_vent(_model):
    summ_vent_objs = []
    for room in _model.rooms:
        if not room.user_data:
            continue
        
        summ_vent_d = room.user_data.get('phpp', {}).get('summ_vent', None)
        if summ_vent_d:
            for summ_vent_params in summ_vent_d.values():
                new_obj = LBT2PH.summer_vent.PHPP_SummVent.from_dict( summ_vent_params )    
                summ_vent_objs.append( new_obj )
    
    return summ_vent_objs

def get_heating_cooling(_model):
    hc_objs = {}
    for room in _model.rooms:
        if not room.user_data:
            continue

        d = room.user_data.get('phpp', {}).get('heating_cooling')
        if not d:
            continue
        
        this_room = {}
        for k, v in d.items():
            if 'supply_air_cooling' in k:
                this_room['supply_air_cooling'] = LBT2PH.heating_cooling.PHPP_Cooling_SupplyAir.from_dict(v)
            elif 'recirc_air_cooling' in k:
                this_room['recirc_air_cooling'] = LBT2PH.heating_cooling.PHPP_Cooling_RecircAir.from_dict(v)
            elif 'addnl_dehumid' in k:
                this_room['addnl_dehumid'] = LBT2PH.heating_cooling.PHPP_Cooling_Dehumid.from_dict(v)
            elif 'panel_cooling' in k:
                this_room['panel_cooling'] =  LBT2PH.heating_cooling.PHPP_Cooling_Panel.from_dict(v)
            elif 'hp_heating' in k:
                this_room['hp_heating'] = LBT2PH.heating_cooling.PHPP_HP_AirSource.from_dict(v)
            elif 'hp_DHW_' in k:
                this_room['hp_DHW'] = LBT2PH.heating_cooling.PHPP_HP_AirSource.from_dict(v)
            elif 'hp_options_' in k:
                this_room['hp_options'] = LBT2PH.heating_cooling.PHPP_HP_Options.from_dict(v)
            elif 'hp_ground_' in k:
                this_room['hp_ground'] = None
            elif 'boiler' in k:
                this_room['boiler'] = LBT2PH.heating_cooling.PHPP_Boiler.from_dict(v)
            elif 'compact' in k:
                this_room['compact'] = None
            elif 'district_heat' in k:
                this_room['district_heat'] = None

        hc_objs[room.display_name] = this_room

    return hc_objs

def get_PER( _model ):
    per_objs = {}

    for room in _model.rooms:
        if not room.user_data:
            continue
        
        d = room.user_data.get('phpp', {}).get('PER')
        if not d:
            continue
        
        per_params = d.values()[0]
        per_params.update( {'room_floor_area':room.floor_area} )

        per_objs.update( {room.display_name:per_params} )

    return per_objs

def get_occupancy( _model ):
    if not _model.user_data:
        print('No User_Data dict found on the model. Ignoring PHPP Occupancy for now.')
        return []

    d = _model.user_data.get('phpp', {}).get('occupancy', None)
    if not d:
        return []
        
    return LBT2PH.occupancy.Occupancy.from_dict( d ) 

