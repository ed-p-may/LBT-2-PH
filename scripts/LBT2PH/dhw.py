from uuid import uuid4
from collections import defaultdict
import functools

class PHPP_DHW_Tap_Point:
    """A single DHW Tap point (faucet, fixture, etc) """

    def __init__(self):
        self.id = str(uuid4())
        self.location = None # Point3D not implemented yet
        self.openings_per_day = 6
        self.utilization = 365

    def to_dict(self):
        d = {}

        d.update( {'id':self.id} )
        d.update( {'location':self.location} )
        d.update( {'openings_per_day':self.openings_per_day} )
        d.update( {'utilization':self.utilization} )

        return d

    @classmethod
    def from_dict(cls, _dict):
        new_obj = cls()

        new_obj.location = _dict.get('location')
        new_obj.location = _dict.get('openings_per_day')
        new_obj.location = _dict.get('utilization')

        return new_obj

    def __unicode__(self):
        return u'A PHPP Style DHW Tap-Point: < {} >'.format(self.id)
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)
    def ToString(self):
        return str(self)

class PHPP_DHW_Pipe_Segment(object):
    """ The base element of a Pipe Section / Run. Represents a single pipe piece / segment """
    
    def __init__(self):
        self.id = str(uuid4())
        self.length = 10 #m
        self._diameter = 0.0127 #m
        self._insul_thickness = 0.0127 #m
        self._insul_conductivity = 0.04 #W/mk
        self._insul_reflective = 'x'
        self._quality = '1-None'
        self._period = 18
    
    @property
    def diameter(self):
        return self._diameter
    
    @diameter.setter
    def diameter(self, _in):
        """Allows for my sloppy input types / formats from RH dict """
        
        try:
            input = float(_in)
        except ValueError:
            try:
                # sometimes gets an input like: "25.4 (1in)"
                input = float( str(_in).split(' ')[0] )
            except ValueError as e:
                raise e

        if input > 1:
            input = input / 1000 #convert to m
        self._diameter = input

    @property
    def insulation_thickness(self):
        return self._insul_thickness

    @insulation_thickness.setter
    def insulation_thickness(self, _in):
        try:
            self._insul_thickness = float(_in)
        except:
            try:
                # sometimes gets inpiut like '25.5 (1in)'...
                self._insul_thickness = float(str(_in).split(' ')[0])
            except:
                raise Exception('Error: Insualtion Thickness input: "{}" should be a number.'.format(_in))

    @property
    def insulation_conductivity(self):
        return self._insul_conductivity

    @insulation_conductivity.setter
    def insulation_conductivity(self, _in):
        try:
            self._insul_conductivity = float(_in)
        except:
            raise Exception('Error: Insualtion Conductivity input: "{}" should be a number.'.format(_in))

    @property
    def insulation_reflective(self):
        return self._insul_reflective

    @insulation_reflective.setter
    def insulation_reflective(self, _in):
        if _in is False or 'False' in str(_in):        
            self._insul_reflective = ''
        else:
            self._insul_reflective = 'x'

    @property
    def insulation_quality(self):
        return self._quality

    @insulation_quality.setter
    def insulation_quality(self, _in):
        if '2' in str(_in):
            self._quality = '2 - Moderate'
        elif '3' in str(_in):
            self._quality = '3 - Good'
        else:
            self._quality = '1-None'
    
    @property
    def daily_period(self):
        return self._period

    @daily_period.setter
    def daily_period(self, _in):
        try:
            self._period = float(_in)
        except Exception as e:
            raise e('Error: Daily Period input: "{}" should be a number.'.format(_in))
        
        assert self._period > 0  and self._period < 24, 'Error: Daily Period should be a number between 0 and 24 hours.'
    
    def _length_weighted_attribute_join(self, other, attr):
        # used by __add__ to join attributes weighted by pipe length
        val_a = getattr(self, attr, 0) * self.length
        val_b = getattr(other, attr, 0) * other.length
        total_val = val_a + val_b
        weighted_val = total_val / (self.length + other.length)
        
        return weighted_val

    def __add__(self, other):
        """Allows you to '+' or sum() PHPP_DHW_Pipe_Segment instances """
        new_obj = self.__class__()
        
        new_obj.insulation_thickness = self._length_weighted_attribute_join(other, 'insulation_thickness')
        new_obj.insulation_conductivity = self._length_weighted_attribute_join(other, 'insulation_conductivity')
        new_obj.diameter = self._length_weighted_attribute_join(other, 'diameter')
        new_obj.length = self.length + other.length
        #new_obj.insulation_reflective = self.insulation_reflective or other.insulation_reflective
        #new_obj.insulation_quality = 2
        #new_obj.daily_period = max(self.daily_period, other.daily_period)

        return new_obj

    __radd__ = __add__

    def to_dict(self):
        d = {}

        d.update( {'id':self.id} )
        d.update( {'length':self.length} )
        d.update( {'diameter':self.diameter} )
        d.update( {'insulation_thickness':self.insulation_thickness} )
        d.update( {'insulation_conductivity':self.insulation_conductivity} )
        d.update( {'insulation_reflective':self.insulation_reflective} )
        d.update( {'insulation_quality':self.insulation_quality} )
        d.update( {'daily_period':self.daily_period} )

        return d

    @classmethod
    def from_dict(cls, _dict):
        new_obj = cls()

        new_obj.id = _dict.get('id')
        new_obj.length = _dict.get('length')
        new_obj.diameter = _dict.get('diameter')
        new_obj.insulation_thickness = _dict.get('insulation_thickness')
        new_obj.insulation_conductivity = _dict.get('insulation_conductivity')
        new_obj.insulation_reflective = _dict.get('insulation_reflective')
        new_obj.insulation_quality = _dict.get('insulation_quality')
        new_obj.daily_period = _dict.get('daily_period')

        return new_obj

    @classmethod
    def from_existing(cls, other):
        """Create a new object based on another """

        new_obj = cls()
        
        new_obj.length = other.length
        new_obj.diameter = other.diameter
        new_obj.insulation_thickness = other.insulation_thickness
        new_obj.insulation_conductivity = other.insulation_conductivity
        new_obj.insulation_reflective = other.insulation_reflective
        new_obj.insulation_quality = other.insulation_quality
        new_obj.daily_period = other.daily_period

        return new_obj

    def __unicode__(self):
        return u'A PHPP Style DHW Pipe Branch: < {} >'.format(self.id)
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
        return '{}: len={}, diam={}'.format(
            self.__class__.__name__,
            self.length,
            self.diameter,
        )    
    def ToString(self):
        return str(self)

class PHPP_DHW_System(object):
    """An organized collection of DHW items """

    def __init__(self):
        self._id = str(uuid4())
        self.system_name = 'DHW'
        self.usage = PHPP_DHW_usage_Res()
        self.forward_temp = 60 #C
        self.tap_points = []
        self.circulation_piping = []
        self.branch_piping = []
        self.rooms_assigned_to = []
        self._tank1 = None
        self._tank2 = None
        self.tank_buffer = None
        self.solar = None

    @property
    def id(self):
        return str(self._id)

    @id.setter
    def id(self, _in):
        if _in:
            self._id = str(_in)

    @property
    def number_of_tap_points(self):
        return len(self.tap_points)

    @property
    def tap_openings_per_day(self):
        return 6
    
    @property
    def tap_utilisation_days(self):
        return 365
   
    @property
    def tank1(self):
        return self._tank1

    @tank1.setter
    def tank1(self, _in):
        if not _in:
            return None
        
        if 'DEFAULT' in str(_in).upper():
            self._tank1 = PHPP_DHW_tank.from_default()
        else:
            self._tank1 = _in

    @property
    def tank2(self):
        return self._tank2

    @tank2.setter
    def tank2(self, _in):
        if not _in: return None
        
        if 'DEFAULT' in str(_in).upper():
            self._tank2 = PHPP_DHW_tank.from_default()
        else:
            self._tank2 = _in

    @staticmethod
    def _add_tanks(t1, t2):
        """Clean join of tank objects when combining systems since either could be 'None' """
        
        if t1 and not t2:
            return t1
        elif t2 and not t1:
            return t2
        elif t1 and t2:
            return t1 + t2
        else:
            return None

    @staticmethod
    def _add_solars(s1, s2):
        """Clean join of Solar thermal systems when combining systems since either could be 'None' """
        
        if s1 and not s2:
            return s1
        elif s2 and not s1:
            return s2
        elif s1 and s2:
            return s1 + s2
        else:
            return None

    def __add__(self, other):
        """Allows you to '+' or sum() PHPP_DHW_System instances """
        new_obj = self.__class__()

        new_obj.system_name = 'Combined System'
        new_obj.usage = self.usage + other.usage
        new_obj.tap_points = self.tap_points + other.tap_points
        new_obj.circulation_piping = self.circulation_piping + other.circulation_piping
        new_obj.branch_piping = self.branch_piping + other.branch_piping
        new_obj.rooms_assigned_to = self.rooms_assigned_to + self.rooms_assigned_to
        new_obj.forward_temp = (self.forward_temp + other.forward_temp)/2
        
        new_obj.tank1 = self._add_tanks( self.tank1, other.tank1 )
        new_obj.tank2 = self._add_tanks( self.tank2, other.tank2 )
        new_obj.tank_buffer = self._add_tanks( self.tank_buffer, other.tank_buffer )
        new_obj.solar = self._add_solars( self.solar, other.solar)
   
        return new_obj
    
    __raddd__ = __add__
    
    @property
    def recirc_piping_PHPP_sets(self): #-> [List]
        """Sorted list of the branch piping 'sets' for the PHPP. Sets are joined
            together based on the input
        
        Returns:
            sets [list] ie: [ seg1, seg2, seg3... ]
        """

        return self._get_piping_set( self.circulation_piping )

    @property
    def branch_piping_PHPP_sets(self): #-> [List]
        """Sorted list of the branch piping 'sets' for the PHPP. Sets are joined
            together based on the input
        
        Returns:
            sets [list] ie: [ seg1, seg2, seg3... ]
        """

        return self._get_piping_set( self.branch_piping )

    def _get_piping_set(self, _piping): #-> [List]
        """Sorted list of the branch piping 'sets' for the PHPP. Sets are joined
            together based on the input
        Args:
            _piping [list]: The piping objects to organize
        Returns:
            sets [list] ie: [ seg1, seg2, seg3... ]
        """
        
        set_dict = self._get_piping_set_by_diameter(_piping)
        list_of_segments = [ set_dict[key] for key in sorted(set_dict.keys(), reverse=True)]

        pipe_sets = []
        for pipe_set in list_of_segments:
            if len(pipe_set) == 0:
                pass
            elif len(pipe_set) == 1:
                pipe_sets.append(pipe_set[0])
            else:
                # Use reduce instead of sum to avoid default length propblem
                pipe_sets.append( functools.reduce(lambda a, b: a+b, pipe_set) )

        return pipe_sets

    def _get_piping_set_by_diameter(self, _piping): #-> [Dict]
        """ Returns a dict with pipe segments organized/binned by their diameter 
        
        This is used to split up / organize the data for the PHPP which has 5 
        'sets' of Piping it can accept. The 'sets' should be organized / diferentiated
        based on the diameter of the piping and the insulation thickness / type (for recirc)

        Args:
            __piping [list]: The piping objects to organize
        Returns:
            pipe_sets [dict] ie: { 25mm: [seg1, seg2, ...], 75mm:[seg4, seg12, ...] }
        """
        
        pipe_sets = defaultdict(list)

        for pipe_segment in _piping:
            pipe_sets[pipe_segment.diameter].append(pipe_segment)

        return pipe_sets

    def check_tanks_for_solar_connection(self):
        """Looks at all the tanks to see if any have a solar connection """
        
        solar_connection = False
        for tank in [self.tank1, self.tank2, self.tank_buffer]:
            if not tank: continue
            if tank.solar:
                solar_connection = True
                break

        if solar_connection:
            msg = None
        else:
            msg = 'It appears you have a Solar Thermal systems applied, but none\n'\
                'of the tanks have a solar thermal connection? Please make sure that\n'\
                'at least one tank has "tank_solar_" set to "True".'
        return msg

    def to_dict(self):
        d = {}

        d.update( {'id':self.id} )
        d.update( {'rooms_assigned_to': self.rooms_assigned_to} )
        d.update( {'system_name':self.system_name} )
        d.update( {'forward_temp':self.forward_temp} )

        d.update( {'tap_points': {} } ) 
        for tap_obj in self.tap_points:
            d['tap_points'].update( { tap_obj.id:tap_obj.to_dict() } )

        d.update( {'circulation_piping': {} } ) 
        for piping_obj in self.circulation_piping:
            d['circulation_piping'].update( { piping_obj.id:piping_obj.to_dict() } )
        
        d.update( {'branch_piping': {} } ) 
        for piping_obj in self.branch_piping:
            d['branch_piping'].update( { piping_obj.id:piping_obj.to_dict() } )

        if self.usage:        d.update( {'usage': self.usage.to_dict() } )
        if self._tank1:       d.update( {'tank1':self.tank1.to_dict()} )
        if self._tank2:       d.update( {'tank2':self.tank2.to_dict()} )
        if self.tank_buffer:  d.update( {'tank_buffer':self.tank_buffer.to_dict() } )
        if self.solar:        d.update( {'solar':self.solar.to_dict() } ) 
        
        return d
    
    @classmethod
    def from_dict(cls, _dict):
        new_obj = cls()
        
        new_obj.id = _dict.get('id')
        new_obj.rooms_assigned_to = _dict.get('rooms_assigned_to')
        new_obj.system_name = _dict.get('system_name')
        new_obj.forward_temp = _dict.get('forward_temp')

        tap_points = _dict.get('tap_points')
        for tap_point_obj in tap_points.values():
            new_tap_point_obj = PHPP_DHW_Tap_Point.from_dict( tap_point_obj )
            new_obj.tap_points.append( new_tap_point_obj )

        circulation_piping = _dict.get('circulation_piping', {})
        for circ_pipe_obj in circulation_piping.values():
            new_piping_obj = PHPP_DHW_Pipe_Segment.from_dict( circ_pipe_obj )
            new_obj.circulation_piping.append( new_piping_obj )

        branch_piping = _dict.get('branch_piping', {})
        for branch_pipe_obj in branch_piping.values():
            new_piping_obj = PHPP_DHW_Pipe_Segment.from_dict( branch_pipe_obj )
            new_obj.branch_piping.append( new_piping_obj )

        new_obj.tank1 = PHPP_DHW_tank.from_dict( _dict.get('tank1') )
        new_obj.tank2 = PHPP_DHW_tank.from_dict( _dict.get('tank2') )
        new_obj.tank_buffer = PHPP_DHW_tank.from_dict( _dict.get('tank_buffer') )
        new_obj.solar = PHPP_DHW_Solar.from_dict( _dict.get('solar') )
        
        usage = _dict.get('usage')
        if usage:
            if usage.get('type') == 'Res':
                usage = PHPP_DHW_usage_Res.from_dict( _dict.get('usage') )
            elif usage.get('type') == 'NonRes':
                usage = PHPP_DHW_usage_NonRes.from_dict( _dict.get('usage') )
        else:
            usage = None
        new_obj.usage = usage
        
        return new_obj

    def __unicode__(self):
        return u'A PHPP Style DHW System: < {} >'.format(self.id)
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)
    def ToString(self):
        return str(self)

class PHPP_DHW_usage_Res(object):
    
    def __init__(self, _type='Res', _shwr=16, _other=9):
        self._id = str(uuid4())
        self.type = 'Res'
        self.demand_showers = _shwr
        self.demand_others = _other
    
    @property
    def id(self):
        return str(self._id)

    @id.setter
    def id(self, _in):
        if _in:
            self._in = _in

    def __add__(self, other):
        new_obj = self.__class__()

        new_obj.demand_showers = (self.demand_showers + other.demand_showers)/2
        new_obj.demand_others = (self.demand_others + other.demand_others)/2

        return new_obj  
    __radd__ = __add__

    def to_dict(self):
        d = {}

        d.update( {'id':self.id} )
        d.update( {'type': self.type})
        d.update( {'demand_showers':self.demand_showers} )
        d.update( {'demand_others':self.demand_others} )
        
        return d

    @classmethod
    def from_dict(cls, _dict):
        new_obj = cls()

        new_obj.id =  _dict.get('id')
        new_obj.demand_showers =  _dict.get('demand_showers')
        new_obj.demand_others = _dict.get('demand_others')

        return new_obj

    def __unicode__(self):
        return u'A Residential DHW usage profile Object'.format()
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
        return "{}( showers_demand_={}, other_demand_={!r} )".format(
               self.__class__.__name__,
               self.demand_showers,
               self.demand_others)
    def ToString(self):
        return str(self)

class PHPP_DHW_usage_NonRes(object):
    
    def __init__(self, args={}):
        self._id = str(uuid4())
        self.type = 'NonRes'
        self.use_daysPerYear = args.get('useDaysPerYear_', 365)
        self.useShowers = args.get('showers_', 'x')
        self.useHandWashing = args.get('handWashBasin_', 'x')
        self.useWashStand = args.get('washStand_', 'x')
        self.useBidets = args.get('bidet_', 'x')
        self.useBathing = args.get('bathing_', 'x')
        self.useToothBrushing = args.get('toothBrushing_', 'x')
        self.useCooking = args.get('cookingAndDrinking_', 'x')
        self.useDishwashing = args.get('dishwashing_', 'x')
        self.useCleanKitchen = args.get('cleaningKitchen_', 'x')
        self.useCleanRooms = args.get('cleaningRooms_', 'x')
    
    @property
    def id(self):
        return str(self._id)

    @id.setter
    def id(self, _in):
        if _in:
            self._in = _in
    
    def __add__(self, other):
        new_obj = self.__class__()
        #
        #
        #
        #TODO
        #
        #
        #        
        return self

    __radd__ = __add__

    def to_dict(self):
        d = {}

        d.update( {'type':self.type})
        d.update( {'id':self.id })
        d.update( {'use_daysPerYear':self.use_daysPerYear })
        d.update( {'useShowers':self.useShowers })
        d.update( {'useHandWashing':self.useHandWashing })
        d.update( {'useWashStand':self.useWashStand })
        d.update( {'useBidets':self.useBidets })
        d.update( {'useBathing':self.useBathing })
        d.update( {'useToothBrushing':self.useToothBrushing })
        d.update( {'useCooking':self.useCooking })
        d.update( {'useDishwashing':self.useDishwashing })
        d.update( {'useCleanKitchen':self.useCleanKitchen })
        d.update( {'useCleanRooms':self.useCleanRooms })

        return d

    @classmethod
    def from_dict(cls, _dict):
        new_obj = cls()

        new_obj.id = _dict.get('id')
        new_obj.use_daysPerYear = _dict.get('use_daysPerYear')
        new_obj.useShowers = _dict.get('useShowers')
        new_obj.useHandWashing = _dict.get('useHandWashing')
        new_obj.useWashStand = _dict.get('useWashStand')
        new_obj.useBidets = _dict.get('useBidets')
        new_obj.useBathing = _dict.get('useBathing')
        new_obj.useToothBrushing = _dict.get('useToothBrushing')
        new_obj.useCooking = _dict.get('useCooking')
        new_obj.useDishwashing = _dict.get('useDishwashing')
        new_obj.useCleanKitchen = _dict.get('useCleanKitchen')
        new_obj.useCleanRooms = _dict.get('useCleanRooms')
        
        return new_obj

    def __unicode__(self):
        return u'A Non-Residential DHW usage profile Object'.format()
    def __str__(self):
        return unicode(self).encode('utf-8')    
    def __repr__(self):
        return "{}( useDaysPerYear_={!r}, showers_={!r}, handWashBasin_={!r}, bidet_={!r}, bathing_={!r},"\
        "toothBrushing_={!r}, cookingAndDrinking_={!r}, dishwashing_={!r}, cleaningKitchen_={!r}, cleaningRooms_={!r})".format(
                self.__class__.__name__,
                self.use_daysPerYear,
                self.useShowers,
                self.useHandWashing,
                self.useBidets,
                self.useBathing,
                self.useToothBrushing,
                self.useCooking,
                self.useDishwashing,
                self.useCleanKitchen,
                self.useCleanRooms)
    def ToString(self):
        return str(self)

class PHPP_DHW_tank(object):
    def __init__(self, _type='0-No storage tank', _solar=False, _hl_rate=None,
                    _vol=None, _stndby_frac=None, _loc='1-Inside', _loc_T=''):
        self._id = str(uuid4())
        self._type = _type
        self.solar = _solar
        self.hl_rate = _hl_rate
        self.vol = _vol
        self.stndbyFrac = _stndby_frac
        self._location = _loc
        self.location_t = _loc_T
    
    @property
    def id(self):
        return str(self._id)

    @id.setter
    def id(self, _in):
        if _in:
            self._in = _in

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, _in):
        if '1' in str(_in):
            self._type = '1-DHW and heating'
        elif '2' in str(_in):
            self._type = '2-DHW only'
        else:
            self._type = '0-No storage tank'

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, _in):
        if '2' in str(_in):
            self._location = '2-Outside'
        else:
            self._location = '1-Inside'
    
    @staticmethod
    def add_solars(s1, s2):
        if s1 or s2:
            return True
        else:
            return None

    @staticmethod
    def _join_str_values(_in1, _in2, _attr_name):
        """Used when combining tanks. Clean join of string attribute values, checks that they are the same """

        input_values = {_in1, _in2}
        if len(input_values) != 1:
            msg = '\nError Combining DHW Tanks:\n'\
                    'Cannot combine {}: "{}" with "{}"\n'\
                    'Please check your inputs.'.format(_attr_name, _in1, _in2)
            raise Exception(msg)
        else:
            return _in1

    def __add__(self, other):
        new_obj = self.__class__()

        new_obj.type = self._join_str_values(self.type, other.type, 'Tank Type' )
        new_obj.solar = self.add_solars(self.solar, other.solar)
        new_obj.hl_rate = ((self.hl_rate or 0) + (other.hl_rate or 0))/2
        new_obj.vol = ((self.vol or 0) + (other.vol or 0))/2
        new_obj.stndbyFrac = ((self.stndbyFrac or 0) + (other.stndbyFrac or 0))/2
        new_obj.location = self._join_str_values(self.location, other.location, 'Tank Location')
        new_obj.location_t = ((self.location_t or 0) + (other.location_t or 0))/2

        return new_obj
    __radd__ = __add__

    def to_dict(self):
        d = {}

        d.update( {'id':self.id} )
        d.update( {'type':self.type } )
        d.update( {'solar':self.solar} )
        d.update( {'hl_rate':self.hl_rate} )
        d.update( {'vol':self.vol} )
        d.update( {'stndbyFrac':self.stndbyFrac} )
        d.update( {'location':self.location} )
        d.update( {'location_t':self.location_t} )

        return d

    @classmethod
    def from_dict(cls, _dict):
        if not _dict:
            return None
        
        new_obj = cls()

        new_obj.id = _dict.get('id')
        new_obj.type = _dict.get('type')
        new_obj.solar = _dict.get('solar')
        new_obj.hl_rate = _dict.get('hl_rate')
        new_obj.vol = _dict.get('vol')
        new_obj.stndbyFrac = _dict.get('stndbyFrac')
        new_obj.location = _dict.get('location')
        new_obj.location_t = _dict.get('location_t')

        return new_obj
    
    @classmethod
    def from_default(cls):
        
        new_obj = cls()
        new_obj.type = '1-DHW and heating'
        new_obj.hl_rate = 4 #W/k

        return new_obj

    def __unicode__(self):
        return u'A DHW Tank Object'    
    def __str__(self):
        return unicode(self).encode('utf-8')    
    def __repr__(self):
        return "{}( _type={!r}, _solar={!r}, _hl_rate={!r}, "\
              "_vol={!r}, _stndby_frac={!r} _loc={!r}, _loc_T={!r})".format(
               self.__class__.__name__,
               self.type,
               self.solar,
               self.hl_rate,
               self.vol,
               self.stndbyFrac,
               self.location,
               self.location_t)
    def ToString(self):
        return str(self)

class PHPP_DHW_Solar(object):
    def __init__(self, 
                _angle_off_north=None, 
                _angle_off_horizontal=None, 
                _host_srfc=None,
                _collector_type='6-Standard flat plate collector',                    
                _collector_area=10,
                _collector_height=1,
                _horizon_height=0, 
                _horizon_distance=1000,
                _additional_reduction_fac=1,
                _heating_support=None,
                _dhw_priority='X'):
        self._id = str(uuid4())
        self.angle_off_north = _angle_off_north
        self.angle_off_horizontal = _angle_off_horizontal
        self.host_surface = _host_srfc
        self._collector_type = _collector_type
        self.collector_area = _collector_area
        self.collector_height = _collector_height
        self.horizon_height = _horizon_height
        self.horizon_distance = _horizon_distance
        self._additional_reduction_fac = _additional_reduction_fac
        self.heating_support = _heating_support
        self.dhw_priority = _dhw_priority
    
    @property
    def id(self):
        return str(self._id)

    @id.setter
    def id(self, _in):
        if _in:
            self._in = _in

    @property
    def collector_type(self):
        return self._collector_type

    @collector_type.setter
    def collector_type(self, _in):
        if not _in: return None

        if '7' in str(_in):
            _type = '7-Improved flat place collector'
        elif '8' in str(_in):
            _type = '8-Evacuated tube collector'
        else:
            _type = '6-Standard flat plate collector'

        self._collector_type = _type

    @property
    def additional_reduction_fac(self):
        return self._additional_reduction_fac

    @additional_reduction_fac.setter
    def additional_reduction_fac(self, _in):
        if not _in: return None

        if float(_in) > 1:
            value = float(_in) / 100
        else:
            value = float(_in)
        
        self._additional_reduction_fac = value

    def __add__(self, other):
        #
        #
        #
        # TODO
        # Not Implemented
        #
        #
        #        
        return self
    __radd__ = __add__

    def to_dict(self):
        d = {}

        d.update( {'id':self.id} )
        d.update( {'angle_off_north':self.angle_off_north} )
        d.update( {'angle_off_horizontal':self.angle_off_horizontal} )
        d.update( {'host_surface':self.host_surface} )
        d.update( {'collector_type':self.collector_type} )
        d.update( {'collector_area':self.collector_area} )
        d.update( {'collector_height':self.collector_height} )
        d.update( {'horizon_height':self.horizon_height} )
        d.update( {'horizon_distance':self.horizon_distance} )
        d.update( {'additional_reduction_fac':self.additional_reduction_fac} )
        d.update( {'heating_support':self.heating_support} )
        d.update( {'dhw_priority':self.dhw_priority} )

        return d 

    @classmethod
    def from_dict(cls, _dict):
        if not _dict: return None
        
        new_obj = cls()

        new_obj.id = _dict.get('id')
        new_obj.angle_off_north = _dict.get('angle_off_north')
        new_obj.angle_off_horizontal = _dict.get('angle_off_horizontal')
        new_obj.host_surface = _dict.get('host_surface')
        new_obj.collector_type = _dict.get('collector_type')
        new_obj.collector_area = _dict.get('collector_area')
        new_obj.collector_height = _dict.get('collector_height')
        new_obj.horizon_height = _dict.get('horizon_height')
        new_obj.horizon_distance = _dict.get('horizon_distance')
        new_obj.additional_reduction_fac = _dict.get('additional_reduction_fac')
        new_obj.heating_support = _dict.get('heating_support')
        new_obj.dhw_priority = _dict.get('dhw_priority')

        return new_obj

    def __unicode__(self):
        return u"A Solar Thermal Hot Water System Object < {} >".format(self.id)
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
       return "{}()".format(self.__class__.__name__)
    def ToString(self):
        return str(self)
