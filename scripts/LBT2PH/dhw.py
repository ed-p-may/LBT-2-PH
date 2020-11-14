import random
from System import Object

class PHPP_DHW_System:
    def __init__(self, _rms_assigned=[], _name='DHW', _usage=None, _fwdT=60,
                _pCirc={}, _pBran={}, _t1=None, _t2=None, _tBf=None):
        self.id = random.randint(1000,9999)
        self.SystemName = _name
        self.usage = _usage
        self.forwardTemp = _fwdT
        self.circulation_piping = _pCirc
        self.branch_piping = _pBran
        self.tank1 = _t1
        self.tank2 = _t2
        self.tank_buffer = _tBf
        self.rooms_assigned_to = _rms_assigned
    
    def to_dict(self):
        d = {}

        d.update( {'id':self.id} )
        d.update( {'rooms_assigned_to': self.rooms_assigned_to} )
        d.update( {'SystemName':self.SystemName} )
        d.update( {'usage': self.usage.to_dict() } )
        d.update( {'forwardTemp':self.forwardTemp} )
        
        d.update( {'circulation_piping': {} } ) 
        for circ_piping_obj in self.circulation_piping.values():
            d['circulation_piping'].update( { circ_piping_obj.id:circ_piping_obj.to_dict() } )
        
        d.update( {'branch_piping': {} } ) 
        for piping_obj in self.branch_piping.values():
            d['branch_piping'].update( { piping_obj.id:piping_obj.to_dict() } )

        d.update( {'tank1':self.tank1.to_dict()} )
        d.update( {'tank2':self.tank2.to_dict()} )
        d.update( {'tank_buffer':self.tank_buffer.to_dict() } )

        return d

    @classmethod
    def from_dict(cls, _dict):
        new_obj = cls()

        new_obj.rooms_assigned_to = _dict.get('rooms_assigned_to')
        new_obj.SystemName = _dict.get('SystemName')
        new_obj.forwardTemp = _dict.get('forwardTemp')
        
        circ_pipings = _dict.get('circulation_piping')
        for circ_piping in circ_pipings.values():
            new_piping_obj = PHPP_DHW_RecircPipe.from_dict( circ_piping )
            new_obj.circulation_piping.update( {new_piping_obj.id:new_piping_obj} )

        branch_piping = _dict.get('branch_piping')
        for branch_pipe_obj in branch_piping.values():
            new_piping_obj = PHPP_DHW_branch_piping.from_dict( branch_pipe_obj )
            new_obj.branch_piping.update( {new_piping_obj.id:new_piping_obj} )
                
        new_obj.tank1 = PHPP_DHW_tank.from_dict( _dict.get('tank1') )
        new_obj.tank2 = PHPP_DHW_tank.from_dict( _dict.get('tank2') )
        new_obj.tank_buffer = PHPP_DHW_tank.from_dict( _dict.get('tank_buffer') )
    
        usage = _dict.get('usage')
        if usage:
            if usage.get('type') == 'Res':
                usage = PHPP_DHW_usage_Res.from_dict( _dict.get('usage') )
            elif usage.get('type') == 'NonRes':
                usage = PHPP_DHW_usage_NonRes.from_dict( _dict.get('usage') )
        else:
            usage = PHPP_DHW_usage_Res()
        new_obj.usage = usage
        
        return new_obj

    def __unicode__(self):
        return u'A PHPP Style DHW System: < {self.SystemName} >'.format(self=self)
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
       return "{}( _name={!r}, _usage={!r}, _fwdT={!r}, _pCirc={!r}, "\
              "_pBran={!r}, _t1={!r}, _t2={!r}, _tBf={!r} )".format(
               self.__class__.__name__,
               self.SystemName,
               self.usage,
               self.forwardTemp,
               self.circulation_piping,
               self.branch_piping,
               self.tank1,
               self.tank2,
               self.tank_buffer)

class PHPP_DHW_usage_Res(Object):
    
    def __init__(self, _type='Res', _shwr=16, _other=9):
        self.id = random.randint(1000,9999)
        self.type = 'Res'
        self.demand_showers = _shwr
        self.demand_others = _other
    
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

class PHPP_DHW_usage_NonRes(Object):
    
    def __init__(self, args={}):
        self.id = random.randint(1000,9999)
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

class PHPP_DHW_RecircPipe(Object):
    def __init__(self, _len=[], _d=[0.0254], _t=[0.0254], _lam=[0.04],
                    _ref=['x'], _q='1-None', _p=18):    
        self.id = random.randint(1000,9999)
        self.lengths = _len
        self.diams = _d
        self.insul_thicknesses = _t
        self.insul_conductivities = _lam
        self.insul_reflectives = _ref
        self.quality = _q
        self.period = _p
    
    def _len_weighted(self, _input_list, _default_value):
        """ Utils function to return length-weighted avg. value """

        if not self.lengths:
            return None
        
        weighted_result = []
        for i, segment_len in enumerate( self.lengths ):
            try:
                weighted_result.append( float(segment_len) * float(_input_list[i]) )
            except:
                try:
                    weighted_result.append( float(segment_len) * float(_input_list[0]) )
                except SystemError as e:
                    # Catches any 'None' values in the list
                    print('-'*25)
                    print(e)
                    print("DHW Error. Parameter value is missing on Rhino piping curve someplace?")
                    print(_input_list)
                    weighted_result.append( float(segment_len) * _default_value)
        
        return sum(weighted_result) / sum(self.lengths)

    @property
    def length(self):
        return sum(self.lengths)

    @property
    def diameter(self):
        return self._len_weighted( self.diams, 0.0254 )

    @property
    def insul_thickness(self):
        return self._len_weighted( self.insul_thicknesses, 0.0254 )

    @property
    def insul_relfective(self):
        return 'x' if 'x' in self.insul_reflectives else ''
    
    @property
    def insul_lambda(self):
        return self._len_weighted( self.insul_conductivities, 0.04 )

    def to_dict(self):
        d = {}

        d.update( {'id':self.id} )
        d.update( {'length':self.lengths} )
        d.update( {'diam':self.diams} )
        d.update( {'insul_thicknesses':self.insul_thicknesses} )
        d.update( {'insul_conductivities':self.insul_conductivities} )
        d.update( {'insul_reflectives':self.insul_reflectives} )
        d.update( {'quality':self.quality} )
        d.update( {'period':self.period} )

        return d

    @classmethod
    def from_dict(cls, _dict):
        new_obj = cls()

        new_obj.id = _dict.get('id')
        new_obj.lengths = _dict.get('length')
        new_obj.diams = _dict.get('diam')
        new_obj.insul_thicknesses = _dict.get('insul_thicknesses')
        new_obj.insul_conductivities = _dict.get('insul_conductivities')
        new_obj.insul_reflectives = _dict.get('insul_reflectives')
        new_obj.quality = _dict.get('quality')
        new_obj.period = _dict.get('period')

        return new_obj
    
    def __unicode__(self):
        return u'A DHW Recirculation Pipe Object <{}>'.format(self.id)
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
        return "{}( _len={!r}, _d={!r}, _t={!r}, "\
              "_lam={!r}, _ref={!r} _q={!r}, _p={!r})".format(
               self.__class__.__name__,
               self.lengths,
               self.diams,
               self.insul_thicknesses,
               self.insul_conductivities,
               self.insul_reflectives,
               self.quality,
               self.period)

class PHPP_DHW_branch_piping(Object):
    def __init__(self, _ds=[0.0127], _lens=[], _opens=6, _utiliz=365):
        self.id = random.randint(1000,9999)
        self._diams = _ds
        self._lens = _lens
        self.tap_openings = _opens
        self.utilisation = _utiliz
       
    def _len_weighted(self, _input_list, _default_value):
        """ Utils function to return length-weighted avg. value """

        if not self._lens:
            return None
        
        weighted_result = []
        for i, segment_len in enumerate( self._lens ):
            try:
                weighted_result.append( float(segment_len) * float(_input_list[i]) )
            except:
                try:
                    weighted_result.append( float(segment_len) * float(_input_list[0]) )
                except SystemError as e:
                    # Catches any 'None' values in the list
                    print('-'*25)
                    print(e)
                    print("DHW Error. Parameter value is missing on Rhino piping curve someplace?")
                    print(_input_list)
                    weighted_result.append( float(segment_len) * _default_value)
        
        return sum(weighted_result) / sum(self._lens)
    
    @property
    def tap_points(self):
        return len(self._lens)

    @property
    def length(self):
        return sum(self._lens)

    @length.setter
    def length(self, _input):
        if isinstance(_input, list):
            self._lens = _input
        else:
            self._lens = [ _input ]

    @property
    def diameter(self):
        return self._len_weighted( self._diams, 0.0127)

    @diameter.setter
    def diameter(self, _input):
        if isinstance(_input, list):
            self._diams = _input
        else:
            self._diams = [ _input ]

    def to_dict(self):
        d = {}

        d.update( {'id':self.id} )
        d.update( {'_diams':self._diams} )
        d.update( {'_lens':self._lens} )
        d.update( {'tap_openings':self.tap_openings} )
        d.update( {'utilisation':self.utilisation} )

        return d

    @classmethod
    def from_dict(cls, _dict):
        new_obj = cls()

        new_obj.id = _dict.get('id')
        new_obj._diams = _dict.get('_diams')
        new_obj._lens = _dict.get('_lens')
        new_obj.tap_openings = _dict.get('tap_openings')
        new_obj.utilisation = _dict.get('utilisation')

        return new_obj
    
    def __unicode__(self):
        return u'A DHW Branch Piping Object <{}>'.format(self.id)
    def __str__(self):
        return unicode(self).encode('utf-8') 
    def __repr__(self):
        return "{}( _d={!r}, _len={!r}, "\
              "_opens={!r}, _utiliz={!r} )".format(
               self.__class__.__name__,
               self._diams,
               self._lens,
               self.tap_openings,
               self.utilisation)

class PHPP_DHW_tank(Object):
    def __init__(self, _type=None, _solar=None, _hl_rate=None,
                    _vol=None, _stndby_frac=None, _loc='1-Inside', _loc_T=''):
        self.id = random.randint(1000,9999)
        self.type = _type
        self.solar = _solar
        self.hl_rate = _hl_rate
        self.vol = _vol
        self.stndbyFrac = _stndby_frac
        self.loction = _loc
        self.locaton_t = _loc_T
        
    def to_dict(self):
        d = {}

        d.update( {'id':self.id} )
        d.update( {'type':self.type } )
        d.update( {'solar':self.solar} )
        d.update( {'hl_rate':self.hl_rate} )
        d.update( {'vol':self.vol} )
        d.update( {'stndbyFrac':self.stndbyFrac} )
        d.update( {'loction':self.loction} )
        d.update( {'locaton_t':self.locaton_t} )

        return d

    @classmethod
    def from_dict(cls, _dict):
        new_obj = cls()

        new_obj.idd = _dict.get('id')
        new_obj.type = _dict.get('type')
        new_obj.solar = _dict.get('solar')
        new_obj.hl_rate = _dict.get('hl_rate')
        new_obj.vol = _dict.get('vol')
        new_obj.stndbyFrac = _dict.get('stndbyFrac')
        new_obj.locaton = _dict.get('loction')
        new_obj.locaton_t = _dict.get('locaton_t')

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
               self.loction,
               self.locaton_t)

