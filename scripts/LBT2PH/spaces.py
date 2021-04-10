import rhinoscriptsyntax as rs
import random
import ghpythonlib.components as ghc
import Grasshopper.Kernel as ghK
import Rhino
from System import Object

try:  # import the core honeybee dependencies
    from ladybug_rhino.togeometry import to_face3d
    from ladybug_rhino.fromgeometry import from_face3d
    from ladybug_geometry.geometry3d import Point3D, Face3D
except ImportError as e:
    raise ImportError('\nFailed to import honeybee:\n\t{}'.format(e))

import LBT2PH
import LBT2PH.ventilation

reload(LBT2PH)
reload(LBT2PH.ventilation)

class TFA_Surface(Object):
    ''' Represents an individual TFA Surface floor element '''
    
    def __init__(self, _surface=None, _host_room_name=None, 
                _params={}, _sub_surfaces=[]):
        self._inset = 0.150
        self._neighbors = None
        self._area_gross = None
        self._depth = None

        self.id = random.randint(0,99999)
        self.surface = _surface
        self.host_room_name = _host_room_name
        self.params = _params
        self.sub_surfaces = _sub_surfaces

    def __eq__(self, other):
        return self.id == other.id

    @property
    def inset(self):
        return self._inset

    @inset.setter
    def inset(self, _in):
        try:
            self._inset = float(_in)
        except ValueError as e:
            print(e)
            print( 'Cannot set inset to {}'.format(_in) )

    @property
    def non_res_usage(self):
        return self.get_surface_param('useType', '-')

    @non_res_usage.setter
    def non_res_usage(self, _val):
        self.set_surface_param('useType', _val)

    @property
    def non_res_lighting(self):
        return self.get_surface_param('lighting', '-')
    
    @non_res_lighting.setter
    def non_res_lighting(self, _val):
        self.set_surface_param('lighting', _val)

    @property
    def non_res_motion(self):
        return self.get_surface_param('motion', '-')

    @non_res_motion.setter
    def non_res_motion(self, _val):
        self.set_surface_param('motion', _val)

    @property
    def tfa_factor(self):
        try:
            return float( self.get_surface_param('TFA_Factor', 1) )
        except Exception as e:
            print('Error getting the TFA Factor as a number?')
            print(e)

    @tfa_factor.setter
    def tfa_factor(self, _val):
        try:
            self.set_surface_param('TFA_Factor', float(_val) )
        except Exception as e:
            print('Please supply a number for the TFA-Factor on Surface {}'.format(self.space_name) )
            print('Error setting "{}" as the TFA-Factot'.format( _val ) )
            print(e)

    @property
    def space_number(self):
        try:
            return self.get_surface_param('Room_Number', None)
        except Exception as e:
            print('Error getting the Space Number?')
            print(e)

    @space_number.setter
    def space_number(self, _val):
        try:
            self.set_surface_param('Room_Number', _val )
        except Exception as e:
            print('Error setting "{}" as the Space-Number on surface "{}"?'.format( _val, self.space_name ) )
            print(e)

    @property
    def space_name(self):
        try:
            return self.get_surface_param('Object Name', None)
        except Exception as e:
            print('Error getting the Space Name?')
            print(e)

    @space_name.setter
    def space_name(self, _val):
        try:
            self.set_surface_param('Object Name', _val )
        except Exception as e:
            print('Error setting "{}" as the Space-Name on surface "{}"?'.format( _val, self.space_name ) )
            print(e)

    @property
    def area_tfa(self):
        return self.area_gross * self.tfa_factor

    @property
    def area_gross(self):
        if self._area_gross:
            return self._area_gross
        else:
            # Compute the Gross Area
            try:
                return self.surface.GetArea()
            except Exception as e:
                print('Error calculating the Gross Area?')
                print(e)
                return None

    @area_gross.setter
    def area_gross(self, _val):
        try:
            self._area_gross = float(_val)
        except Exception as e:
            print('Error setting "{}" as the Gross-Area for surface "{}"?'.format( _val, self.space_name ) )
            print(e)

    @property
    def surface_perimeter(self):
        brep_edges = self.surface.Edges
        brep_edges = [edg.DuplicateCurve() for edg in brep_edges]
        srfc_perimeter = Rhino.Geometry.Curve.JoinCurves(brep_edges)

        return srfc_perimeter[0]

    @property
    def neighbors(self):
        if self._neighbors is None:
            return set([self.id])
        else:
            return self._neighbors

    def set_neighbors(self, _in):
        self._neighbors = self.neighbors.union(_in)

    def get_vent_flow_rate(self, _type='V_sup'):
        ''' type = V_sup, V_eta or V_trans '''
        try:
            return float(self.params.get(_type, 0.0))
        except Exception as e:
            print(e)
            print('Error getting {} ventilation flow rate?'.format(_type))

    def set_vent_flow_rate(self, _type, _val):
        if not self.params:
            self.params = {}
        
        if _type not in ['V_sup', 'V_eta', 'V_trans']:
            print("Error setting Vent Flow? Please input flow type:\n"\
                "'V_sup', 'V_eta' or 'V_trans'")
            return None

        self.params[_type] = float(_val)

    def get_surface_param(self, _key, _default=None):
        """ Gets a value from the 'params' dictionary """
        try:
            return self.params.get(_key, _default)
        except AttributeError as e:
            print(e)
            print('No "{}" parameter found in TFA Suface "{}" Params dict?'.format(_key, self.space_name))
            return _default

    def set_surface_param(self, _key, _val):
        ''' Sets a value in the 'params' dictionary '''
        try:
            self.params[_key] = _val
        except Exception as e:
            print(e)
            print('Error setting "{}" Parameter on TFA Surface "{}"?'.format(_key, _val))
    
    @staticmethod
    def _find_hb_room_floor_surfaces( _hb_room, _ghenv ):
        '''Looks at a single input Honeybee room, finds the floor surface(s) '''

        floor_surfaces = [srfc for srfc in _hb_room.faces if str(srfc.type) == 'Floor']
        if not floor_surfaces:
            msg = 'Could not find any Floor surfacs in HB-Room: "{}"?\n'\
            'Check the room surfaces and types to be sure there is at least one Floor.'.format(_hb_room.display_name)
            _ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Remark, msg)

        return floor_surfaces

    @staticmethod
    def _inset_floor_surfaces( _floor_surface, _inset_dist, _ghenv ):
        '''Shrinks/Insets the surface by the specified amount '''

        try:
            rh_srfc = from_face3d(_floor_surface.geometry)
        except Exception as e:
            msg = 'Error. Can not convert floor surface: "{}" to Rhino geometry?'.format( _floor_surface )
            _ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Remark, msg)
            return None

        if _inset_dist < 0.001:
            return rh_srfc
        
        #-----------------------------------------------------------------------
        srfcPerim = ghc.JoinCurves( ghc.BrepEdges(rh_srfc)[0], preserve=False )
        
        # Get the inset Curve
        srfcCentroid = Rhino.Geometry.AreaMassProperties.Compute(rh_srfc).Centroid
        plane = ghc.XYPlane(srfcCentroid)
        srfcPerim_Inset_Pos = ghc.OffsetCurve(srfcPerim, _inset_dist, plane, 1)
        srfcPerim_Inset_Neg = ghc.OffsetCurve(srfcPerim, _inset_dist*-1, srfcCentroid, 1)
        
        # Choose the right Offset Curve. The one with the smaller area
        srfcInset_Pos = ghc.BoundarySurfaces( srfcPerim_Inset_Pos )
        srfcInset_Neg = ghc.BoundarySurfaces( srfcPerim_Inset_Neg )
        area_Pos = ghc.Area(srfcInset_Pos).area
        area_neg = ghc.Area(srfcInset_Neg).area
        
        if area_Pos < area_neg:
            return srfcInset_Pos
        else:
            return srfcInset_Neg

    @property
    def depth(self):
        '''Used for non-res lighting evaluation. The room depth(m) from the main window wall '''
        
        if self._depth:
            return self._depth
        
        worldXplane = ghc.XYPlane( Rhino.Geometry.Point3d(0,0,0) )
        
        # Find the 'short' edge and the 'long' egde of the srfc geometry
        srfcEdges = ghc.DeconstructBrep(self.surface).edges
        segLengths = ghc.SegmentLengths(srfcEdges).longest_length
        srfcEdges_sorted = ghc.SortList(segLengths, srfcEdges).values_a
        endPoints = ghc.EndPoints(srfcEdges_sorted[-1])
        longEdgeVector = ghc.Vector2Pt(endPoints.start, endPoints.end, False).vector
        shortEdgeVector = ghc.Rotate(longEdgeVector, ghc.Radians(90), worldXplane).geometry
        
        # Use the edges to find the orientation and dimensions of the room
        srfcAligedPlane = ghc.ConstructPlane(ghc.Area(self.surface).centroid, longEdgeVector, shortEdgeVector)
        srfcAlignedWorld = ghc.Orient(self.surface, srfcAligedPlane, worldXplane).geometry
        dims = ghc.BoxProperties( srfcAlignedWorld ).diagonal
        dims = [dims.X, dims.Y]
        width = min(dims)
        depth = max(dims)
        
        return depth

    @property
    def dict_key(self):
        if self.space_name and self.space_number:
            tfa_dict_key = '{}-{}'.format(self.space_number, self.space_name)
        else:
            tfa_dict_key = '{}-NONAME'.format(self.id)
        
        return tfa_dict_key

    def to_dict(self):
        d = {}

        d.update( {'id':self.id} )
        d.update( {'space_number':self.space_number} )
        d.update( {'space_name':self.space_name} )
        d.update( {'host_room_name':self.host_room_name} )
        d.update( {'params':self.params} )
        d.update( {'area_gross':self.area_gross} )
        d.update( {'depth':self.depth} )

        if self.surface:
            # Remeber, to_face3d returns a LIST of surfaces incase it triangulates
            # so for now, just getitng the first one in that list to pass along
            # Someday this'll break everything...

            lbt_surface = to_face3d(self.surface)
            
            d.update( {'surface_list': lbt_surface[0].to_dict()  } )

        return d

    @classmethod
    def from_dict(cls, _dict_tfa, _dict_sub_surfaces):
        
        sub_surfaces = []
        for sub_surface in _dict_sub_surfaces.values():
            new_sub_surface = cls.from_dict( sub_surface, {} )
            sub_surfaces.append( new_sub_surface )

        new_tfa_obj = cls()
        new_tfa_obj.id = _dict_tfa.get('id')        
        new_tfa_obj.host_room_name = _dict_tfa.get('host_room_name')
        new_tfa_obj.params = _dict_tfa.get('params')
        new_tfa_obj.sub_surfaces = sub_surfaces
        new_tfa_obj._inset = 0.1
        new_tfa_obj._neighbors = None
        new_tfa_obj._area_gross = _dict_tfa.get('area_gross')
        new_tfa_obj._depth = _dict_tfa.get('depth', None)

        srfc_list = _dict_tfa.get('surface_list')
        if srfc_list:
            # Remeber, to_face3d returns a LIST of surfaces incase it triangulates
            # so for now, just getitng the first one in that list to pass along
            # Someday this'll break everything...

            lbt_surface = Face3D.from_dict( srfc_list )
            rh_surface = from_face3d( lbt_surface )
            new_tfa_obj.surface = rh_surface

        return new_tfa_obj

    @classmethod
    def from_hb_room(cls, _hb_room, _ghenv):
        '''Creates a LIST of Tfa-Surface objects from a Honeybee Room '''
        
        new_objs = []
        
        floor_surfaces = cls._find_hb_room_floor_surfaces(_hb_room, _ghenv)
        
        for srfc in floor_surfaces:
            new_obj = cls()
        
            tfa_surface = new_obj._inset_floor_surfaces( srfc, new_obj.inset, _ghenv )
            new_obj.tfa_factor = 1.0
            new_obj.space_number = '0000'
            new_obj.space_name = _hb_room.display_name
            new_obj.surface = tfa_surface
            new_obj.host_room_name = _hb_room.display_name

            new_objs.append( new_obj )

        return new_objs


    def __unicode__(self):
        return u'A PHPP Treated Floor Area (TFA) Object: < {} >'.format(self.id)
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
       return "{}(_surface={!r}, _host_room_name={!r}, "\
               "params={!r}, _sub_surfaces={!r} )".format(
               self.__class__.__name__,
               self.surface,
               self.host_room_name,
               self.params,
               self.sub_surfaces)


class Volume:
    ''' Represents an individual volume / part of a larger Space '''

    def __init__(self, _tfa_surface=None, _space_geometry=None, _space_height=2.5):
        self.id = random.randint(0,99999)
        self.tfa_surface = _tfa_surface
        self._space_geom = _space_geometry
        self._space_height = _space_height
        self._space_vn50 = None
        self._offset_z = 0
        self._phpp_vent_flow_rates = {'V_sup':0, 'V_eta':0, 'V_trans':0}

    @property
    def non_res_usage(self):
        return self.tfa_surface.non_res_usage
    
    @property
    def non_res_lighting(self):
        return self.tfa_surface.non_res_lighting
    
    @property
    def non_res_motion(self):
        return self.tfa_surface.non_res_motion

    @property
    def dict_key(self):
        return '{}-{}'.format(self.volume_number, self.volume_name)
    
    @property
    def host_room_name(self):
        return self.tfa_surface.host_room_name

    @property
    def volume_name(self):
        return self.tfa_surface.space_name
    
    @property
    def volume_number(self):
        return self.tfa_surface.space_number

    @property
    def volume_height(self):
        try:
            # Try and get the height from the input geometry
            z_positions = []
            vol_brep = self.volume_brep
            for brep in vol_brep:
                vert_list = brep.Vertices
                for vert in vert_list.Item:
                    z_positions.append( vert.Location.Z )

            highest =  max(z_positions)
            lowest = min(z_positions)
            vertical_distance = abs(highest - lowest)
            
            return float( vertical_distance )
        except:
            try:
                return float(self._space_height)
            except:
                return 2.5

    @property
    def volume_brep(self):
        try:
            if self._space_geom:
                return self._build_volume_brep_from_geom()
            else:
                return self._build_volume_brep_from_zone()
        except Exception as e:
            return None

    @property
    def area_tfa(self):
        return float( self.tfa_surface.area_tfa )

    @property
    def vn50(self):
        try:
            volumes = []
            breps = self.volume_brep
            for brep in breps:
                try:
                    volumes.append( abs(float( brep.GetVolume() ) ) )
                except:
                    volumes.append( 0 )
            
            return sum(volumes)
        except Exception as e:
            try:
                return float(self._space_vn50)
            except:
                return 5

    @property
    def depth(self):
        return self.tfa_surface.depth

    @property
    def area_gross(self):
        return self.tfa_surface.area_gross

    def _build_volume_brep_from_geom(self):
        results = ghc.BrepJoin( [self.tfa_surface.surface, self._space_geom.breps] )
        #Un-pack the results
        output = []
        if results:
            for brep, closed in zip(results.breps, results.closed):
                if closed:
                    output.append( brep )

        return output  

    def _build_volume_brep_from_zone(self):      
        # Floor Surface
        floor_surface = rs.coercebrep(self.tfa_surface.surface)
        floor_surface = ghc.Move(floor_surface, ghc.UnitZ(self._offset_z) )[0]  # 0 is the new translated geometry

        # Extrusion curve
        surface_centroid = Rhino.Geometry.AreaMassProperties.Compute(floor_surface).Centroid
        end_point = ghc.ConstructPoint(surface_centroid.X, surface_centroid.Y, surface_centroid.Z + self._space_height)
        extrusion_curve = rs.AddLine(surface_centroid, end_point)

        volume_brep = rs.ExtrudeSurface(surface=floor_surface, curve=extrusion_curve, cap=True)
        volume_brep = rs.coercebrep(volume_brep)
        
        return [volume_brep]

    def _get_vent_flow_rate(self, _type):
        try:
            return float(self.tfa_surface.get_vent_flow_rate(_type))
        except:
            return self._phpp_vent_flow_rates[_type]

    def set_phpp_vent_rates(self, _dict):
        self._phpp_vent_flow_rates = _dict
        
        self.tfa_surface.set_vent_flow_rate('V_sup', _dict['V_sup'])
        self.tfa_surface.set_vent_flow_rate('V_eta', _dict['V_eta'])
        self.tfa_surface.set_vent_flow_rate('V_trans', _dict['V_trans'])

    def to_dict(self):
        d = {}
        d.update( {'id': self.id} )
        d.update( {'volume_height': self.volume_height})
        d.update( {'tfa_surface': self.tfa_surface.to_dict() } )
        d.update( {'_space_vn50': self.vn50 } )

        tfa_sub_surfaces = {}
        for sub_surface in self.tfa_surface.sub_surfaces:
            key = '{}_{}'.format(sub_surface.dict_key, str(sub_surface.id) )
            tfa_sub_surfaces.update( { key:sub_surface.to_dict() } )
        d.update( {'tfa_sub_surfaces': tfa_sub_surfaces } )
    
        vent_rates = {}
        vent_rates.update( {'V_sup':self._get_vent_flow_rate('V_sup') })
        vent_rates.update( {'V_eta':self._get_vent_flow_rate('V_eta') })
        vent_rates.update( {'V_trans':self._get_vent_flow_rate('V_trans') })
        d.update( {'_phpp_vent_flow_rates':vent_rates} )

        return d

    @classmethod
    def from_dict(cls, _dict):
        
        new_volume = cls()
        new_volume.tfa_surface = TFA_Surface.from_dict( _dict['tfa_surface'], _dict['tfa_sub_surfaces'] )
        new_volume._space_geom = None
        new_volume.volume_height = _dict['volume_height']
        new_volume.id = _dict['id']
        new_volume._space_vn50 = _dict['_space_vn50']
        new_volume._phpp_vent_flow_rates = _dict['_phpp_vent_flow_rates']
    
        return new_volume

    def __unicode__(self):
        return u'A PHPP Space Volume Object: < {} >'.format(self.id)
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
       return "{}(_tfa_surface={!r}, _space_geometry={!r}, "\
               "_space_height={!r})".format(
               self.__class__.__name__,
               self.tfa_surface,
               self._space_geom,
               self._space_height)


class Space:
    ''' A 'Space' or Room in a Zone. Made up of one or more Volumes/parts '''
    
    def __init__(self, _volumes=None, _vent_sched=LBT2PH.ventilation.PHPP_Sys_VentSchedule() ):
        self.id = random.randint(0,99999)
        self.volumes = _volumes
        self.phpp_vent_system_id = 'default'
        self._phpp_vent_flow_rates = {'V_sup':0, 'V_eta':0, 'V_trans':0}
        self.vent_sched = _vent_sched
        self._tfa = None
    
    @property
    def non_res_usage(self):
        output = [volume.non_res_usage for volume in self.volumes]
        output = list(set(filter( None, output )))

        if len(output) == 0:
            print('Error: No Non-Res "Usage" found on room {}. Check your TFA surface assignments?'.format(self.space_name))
            return '-'
        elif len(output) > 1:
            print('Error: More than one Non-Res "Usage" found on room {}. Check your TFA surface assignments?'.format(self.space_name))
            return output[0]
        else:
            return output[0]

    @property
    def non_res_lighting(self):
        output = [volume.non_res_lighting for volume in self.volumes]
        output = list(set(filter( None, output )))

        if len(output) == 0:
            print('Error: No Non-Res "Lighting" found on room {}. Check your TFA surface assignments?'.format(self.space_name))
            return '1-'
        elif len(output) > 1:
            print('Error: More than one Non-Res "Lighting" found on room {}. Check your TFA surface assignments?'.format(self.space_name))
            return output[0]
        else:
            return output[0]

    @property
    def non_res_motion(self):
        output = [volume.non_res_motion for volume in self.volumes]
        output = list(set(filter( None, output )))

        if len(output) == 0:
            print('Error: No Non-Res "Motion Detector" found on room {}. Check your TFA surface assignments?'.format(self.space_name))
            return '-'
        elif len(output) > 1:
            print('Error: More than one Non-Res "Motion Detector" found on room {}. Check your TFA surface assignments?'.format(self.space_name))
            return output[0]
        else:
            return output[0]

    @property
    def space_vent_supply_air(self):
        vent_rates = []
        try:
            for vol in self.volumes:
                vent_rates.append( vol._get_vent_flow_rate('V_sup') )
            return max(vent_rates)
        except:
            return self._phpp_vent_flow_rates['V_sup']
        
    @property
    def space_vent_extract_air(self):
        vent_rates = []
        try:
            for vol in self.volumes:
                vent_rates.append( vol._get_vent_flow_rate('V_eta') )           
            return max(vent_rates)
        except:
            return self._phpp_vent_flow_rates['V_eta']
        
    @property
    def space_vent_transfer_air(self):
        vent_rates = []
        try:
            for vol in self.volumes:
                vent_rates.append( vol._get_vent_flow_rate('V_trans') )
            return max(vent_rates)
        except:
            return self._phpp_vent_flow_rates['V_trans']

    @property
    def space_breps(self):
        output = []
        for volume in self.volumes:
            volume_brep = volume.volume_brep
        
        
            if volume_brep is None:
                continue

            if isinstance(volume.volume_brep, list):
                for brep in volume.volume_brep:
                    output.append(brep)
            else:
                output = volume.volume_brep

        return output
    
    @property
    def space_tfa_surfaces(self):
        tfa_surface_breps = []
        for volume in self.volumes:
            tfa_surface_breps.append( volume.tfa_surface.surface )
        
        return tfa_surface_breps

    @property
    def center_point(self):
        cps = [ ghc.Area(tfa_srfc).centroid for tfa_srfc in self.space_tfa_surfaces ]
        cp = ghc.Average(cps)
              
        return rs.CreatePoint(*cp)

    @property
    def host_room_name(self):
        host_room_names = set()
        for volume in self.volumes:
            host_room_names.add(volume.host_room_name)

        if len(host_room_names) != 1:
            print('Error. Multiple Host Zones found? Fix your room geometry')
            return list(host_room_names)[0]
        else:
            return list(host_room_names)[0]

    @property
    def space_name(self):
        space_names = set()
        for volume in self.volumes:
            space_names.add(volume.volume_name)
        
        if len(space_names) != 1:
            print('Error. Multiple volume names found? Please fix your room parameters.')
            return None
        else:
            return space_names.pop()

    @property
    def space_number(self):
        space_nums= set()
        for volume in self.volumes:
            space_nums.add(volume.volume_number)
        
        if len(space_nums) != 1:
            print('Error. Multiple volume numbers found? Please fix your room parameters')
            return None
        else:
            return str(space_nums.pop())

    @property
    def dict_key(self):
        return '{}_{}_{}'.format(self.space_number, self.space_name, self.id)

    @property
    def space_vn50(self):
        return sum([volume.vn50 for volume in self.volumes])

    @property
    def space_tfa(self):
        try:
            return float(self._tfa)
        except:
            return sum(volume.area_tfa for volume in self.volumes)



    #TODO: fix this.... area weighted....
    #
    #
    #
    #
    @property
    def space_tfa_factor(self):
        return 1
    #
    #
    #
    #





    @property
    def depth(self):
        """ Returns the largest of the Volume depths """
        
        depth = [volume.depth for volume in self.volumes]
        return max(depth)

    @property
    def area_gross(self):
        return sum( volume.area_gross for volume in self.volumes )

    @property
    def space_avg_clear_ceiling_height(self):
        return sum([volume.volume_height for volume in self.volumes])/len(self.volumes)

    def set_phpp_vent_rates(self, _dict):
        if 'V_sup' in _dict.keys() and 'V_eta' in _dict.keys() and 'V_trans' in _dict.keys():
            self._phpp_vent_flow_rates = _dict

        for vol in self.volumes:
            vol.set_phpp_vent_rates( _dict )

    def to_dict(self):

        d = {}
        d.update( {'id': self.id} )
        d.update( {'_tfa':self.space_tfa} )
        d.update( {'phpp_vent_system_id': self.phpp_vent_system_id} )
        d.update( {'volumes' : {} } )

        for volume in self.volumes:
            key = '{}_{}'.format(volume.dict_key, volume.id)
            d['volumes'].update( { key : volume.to_dict() } )
        
        vent_rates = {}
        vent_rates.update( {'V_sup': self.space_vent_supply_air} )
        vent_rates.update( {'V_eta': self.space_vent_extract_air} )
        vent_rates.update( {'V_trans': self.space_vent_transfer_air} )
        d.update( {'_phpp_vent_flow_rates': vent_rates} )
        d.update( {'vent_sched': self.vent_sched.to_dict()} )

        return d

    @classmethod
    def from_dict(cls, _dict):

        dict_volumes = _dict['volumes']
        volumes = []
        for volume in dict_volumes.values():
            new_volume = Volume.from_dict(volume)
            volumes.append(new_volume)

        new_space =  cls()
        new_space._tfa = _dict.get('_tfa')
        new_space.id = _dict.get('id')
        new_space.phpp_vent_system_id = _dict.get('phpp_vent_system_id')
        new_space._phpp_vent_flow_rates = _dict.get('_phpp_vent_flow_rates')
        new_space.volumes = volumes
        new_space.vent_sched = LBT2PH.ventilation.PHPP_Sys_VentSchedule.from_dict( _dict.get('vent_sched') )

        return new_space

    def __unicode__(self):
        return u'A PHPP Space Object: < {} > {}-{}'.format(self.id, self.space_number, self.space_name)
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
       return "{}(_volumes={!r}, _vent_sched={!r} )".format(
               self.__class__.__name__,
               self.volumes, self.vent_sched)

def find_all_tfa_surfaces( _tfa_surfaces, _ghenv, _ghdoc ):
    input_num = _TFA_surfaces_input_number(_ghenv)
    
    rhino_tfa_objects = []
    for i, tfa_input in enumerate(_tfa_surfaces):
        rhino_guid = _ghenv.Component.Params.Input[input_num].VolatileData[0][i].ReferenceID
        rhino_obj = Rhino.RhinoDoc.ActiveDoc.Objects.Find( rhino_guid )
        
        if rhino_obj:
            # Input is a Rhino surface
            with LBT2PH.helpers.context_rh_doc(_ghdoc):
                tfa_obj = get_tfa_surface_data_from_Rhino( rhino_guid )
                rhino_tfa_objects.append( tfa_obj )
        else:
            # Input is a Grasshoppper-generated surface
            geom = rs.coercegeometry( tfa_input )
            
            # Give each room a unique number so it won't try and
            # join them together into a single room later
            params = {}
            #params['Object Name'] = 'Unnamed Room' #<--- make this 'turn on-able'
            #params['Room_Number'] = i

            tfa_obj = ( geom, params )
            rhino_tfa_objects.append( tfa_obj )
    
    return rhino_tfa_objects

def _TFA_surfaces_input_number(_ghenv):
    """Searches the Component for the right input """

    for i, input in enumerate(_ghenv.Component.Params.Input):
        if '_HB_rooms' == input.Name or '_TFA_surfaces' == input.NickName:
            return i

def get_tfa_surface_data_from_Rhino(_guid):  
   
    geom = rs.coercegeometry(_guid)
    nm = rs.ObjectName(_guid)

    params = {}
    param_keys = rs.GetUserText(_guid)
    
    for k in param_keys:
        params[k] =rs.GetUserText(_guid, k)
    
    if 'Object Name' in params.keys():
        params['Object Name'] = nm

    return (geom, params)

def find_tfa_host_room(_tfa_srfc_geom, _hb_rooms):
    """Evaluates the Centoid of a TFA srf to see if it is inside an HB-Room """
    
    srfc_centroid_a = Rhino.Geometry.AreaMassProperties.Compute(_tfa_srfc_geom).Centroid
    
    # Note: move the centroid 'up' just a tiny bit, otherwise 'is_point_inside'
    # test will return False. Must not work if point is 'on' a surface...
    move_distance = 0.1
    srfc_centroid_b = Rhino.Geometry.Point3d(srfc_centroid_a.X, srfc_centroid_a.Y, srfc_centroid_a.Z + move_distance)
    
    # Also, to use 'is_point_inside' need to convert the Point to a Ladybug Point3D
    srfc_centroid_c = Point3D(srfc_centroid_b.X, srfc_centroid_b.Y, srfc_centroid_b.Z)
    
    host_room = None
    for room in _hb_rooms:
        if room.geometry.is_point_inside( srfc_centroid_c ):
            host_room = room.display_name
            break

    return srfc_centroid_a, host_room

def get_hb_room_floor_surfaces(_room):
    hb_floor_surfaces = []
    for face in _room.faces:
        if str(face.type) == 'Floor':
            hb_floor_surfaces.append(face)

    return hb_floor_surfaces

def find_neighbors(_dict_of_TFA_objs):
    for tfa_a in _dict_of_TFA_objs.values():
        for tfa_b in _dict_of_TFA_objs.values():
            if ghc.BrepXBrep(tfa_a.surface, tfa_b.surface).curves:
                tfa_a.set_neighbors(tfa_b.neighbors)
                tfa_b.set_neighbors(tfa_a.neighbors)

    return None

def bin_tfa_srfcs_by_neighbor(_dict_of_tfa_surfaces_by_room_id):
    """ I honestly don't remember what this is doing. Gotta write better comments...
    Args:
        _dict_of_tfa_surfaces_by_room_id: (dict): Looks like ->
                {'19-Kitchen': {5775: TFA_Surface...},
                 '20-Bedroom': {5776: TFA_Surface...},
                 ...
                }
    Returns:
        srfcSets: (dict) :Looks like -->
                {
                    5775: [TFA_Surface, TFA_Surface, ...],
                    5776: [TFA_Surface],
                    ...
                }
    """

    srfcSets = {}
    for _tfa_srfc_room_id, _tfa_srfc_dict in _dict_of_tfa_surfaces_by_room_id.items():
        for tfa_id, tfa_surface_obj in _tfa_srfc_dict.items():

            if len(tfa_surface_obj.neighbors) == 1:
                srfcSets[tfa_surface_obj.id] = [ tfa_surface_obj ]
            
            else:
                for id_num in tfa_surface_obj.neighbors:
                    if id_num in srfcSets.keys():
                        srfcSets[id_num].append( tfa_surface_obj )
                        continue
                else:
                    srfcSets[tfa_surface_obj.id] = [ tfa_surface_obj ]

    return srfcSets

def join_touching_tfa_groups(_tfa_surface_groups, _ghenv=None):
    tfa_srfcs_joined = []
    
    for group in _tfa_surface_groups.values():
        # if there is only a single element in the group, add it to the list
        # otherwise, try and join together the elements in the group
        
        if len(group) == 1:
            tfa_srfcs_joined.append(group[0])
        else:
            ventFlowRates_Sup = []
            ventFlowRates_Eta = []
            ventFlowRates_Tran = []
            areas_tfa = []
            areas_gross = []
            srfc_exterior_perimeters = []
            sub_surfaces = []
            usage = []
            lighting = []
            motion = []
            for tfa_srfc in group:
                # Get the ventilation flow rates
                ventFlowRates_Sup.append( tfa_srfc.get_vent_flow_rate('V_sup') )
                ventFlowRates_Eta.append( tfa_srfc.get_vent_flow_rate('V_eta') )
                ventFlowRates_Tran.append( tfa_srfc.get_vent_flow_rate('V_trans') )

                # Get the geometric information
                areas_tfa.append(tfa_srfc.area_tfa)
                areas_gross.append(tfa_srfc.area_gross)
                srfc_exterior_perimeters.append(tfa_srfc.surface_perimeter)
                sub_surfaces.append(tfa_srfc)

                # Get the Non-Res params
                usage.append(tfa_srfc.non_res_usage)
                lighting.append(tfa_srfc.non_res_lighting)
                motion.append(tfa_srfc.non_res_motion)

            # Build the new TFA surface
            perim_curve = ghc.RegionUnion(srfc_exterior_perimeters)
            unioned_surface = Rhino.Geometry.Brep.CreatePlanarBreps(perim_curve, 0.01)
            if len(unioned_surface) != 0:
                unioned_surface = unioned_surface[0]
            else:
                break

            host_room_name = group[0].host_room_name
            params = group[0].params
            unionedTFAObj = TFA_Surface(unioned_surface, host_room_name, params, sub_surfaces)

            # Set the new TFA Surface's param properties
            unionedTFAObj.area_gross = sum(areas_gross)
            unionedTFAObj.tfa_factor = sum(areas_tfa) / sum(areas_gross)
            unionedTFAObj.space_number = group[0].space_number
            unionedTFAObj.space_name = group[0].space_name
            unionedTFAObj.set_surface_param('V_sup', max(ventFlowRates_Sup) )
            unionedTFAObj.set_surface_param('V_eta', max(ventFlowRates_Eta) )
            unionedTFAObj.set_surface_param('V_trans', max(ventFlowRates_Tran) )

            # Set the new TFA Surface's Non-Res params
            usage = sorted(list(set(filter(None, usage))))
            lighting = sorted(list(set(filter(None, lighting))))
            motion = sorted(list(set(filter(None, motion))))
            
            unionedTFAObj.non_res_usage = usage[0]
            unionedTFAObj.non_res_lighting = lighting[0]
            unionedTFAObj.non_res_motion = motion[0]

            # Give Warnings if needed
            if len(usage) > 1:
                msg = 'Warning: Found more than one Non-Res. "Usage" type on room "{}"?'.format( unionedTFAObj.space_name )
                _ghenv.Component.AddRuntimeMessage( ghK.GH_RuntimeMessageLevel.Warning, msg )
            if len(lighting) > 1:
                msg = 'Warning: Found more than one Non-Res. "Lighting" type on room "{}"?'.format( unionedTFAObj.space_name )
                _ghenv.Component.AddRuntimeMessage( ghK.GH_RuntimeMessageLevel.Warning, msg ) 
            if len(motion) > 1:
                msg = 'Warning: Found more than one Non-Res. "Motion Detector" type on room "{}"?'.format( unionedTFAObj.space_name )
                _ghenv.Component.AddRuntimeMessage( ghK.GH_RuntimeMessageLevel.Warning, msg ) 

            # Pass back the new Joined TFA surface
            tfa_srfcs_joined.append(unionedTFAObj)

    return tfa_srfcs_joined

def display_host_error(_tfa_obj, _ghenv):

    try:
        tfa_id = _tfa_obj.dict_key
        msg = "Couldn't figure out which room/zone the tfa surface '{}' should "\
        "go in?\nMake sure the room is completely inside one or another zone.".format(tfa_id)
        _ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, msg)

    except:
        msg = "Couldn't figure out which room/zone the tfa surface 'Un-Named' should "\
        "go in?\nMake sure to set the params for each surface and that they are inside "\
        "\none or another zone"
        _ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, msg)

    return None

def get_model_tfa(_model):
    tfa = 0
    for room in _model.rooms:
        for space in room.user_data.get('phpp', {}).get('spaces').values():
            space_obj = Space.from_dict( space )
            tfa += space_obj.space_tfa
    
    return tfa