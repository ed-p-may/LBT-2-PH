from System import Object
import random

class PHPP_PER(Object):
    def __init__(self, _htPrim='5-Direct electricity', _htSec=None,
                _ht_frac=1, _dhw_frac=1, _mechClg=False):
        self.id = random.randint(1000,9999)
        self._primary_heat = _htPrim
        self._secondary_heat = _htSec
        self._primary_heat_frac = _ht_frac
        self._dhw_frac = _dhw_frac
        self._mech_cooling = _mechClg

    @property
    def primary_heat(self):
        if '1' in str(self._primary_heat):
            return '1-HP compact unit' 
        elif '2' in str(self._primary_heat):
            return '2-Heat pump(s)'
        elif '3' in str(self._primary_heat):
            return '3-District heating, CGS'
        elif '4' in str(self._primary_heat):
            return '4-Heating boiler'
        elif '6' in str(self._primary_heat):
            return '6-Other'
        else:
            return '5-Direct electricity' 

    @primary_heat.setter
    def primary_heat(self, _in):
        self._primary_heat = _in

    @property
    def secondary_heat(self):
        if not self._secondary_heat or str(self._secondary_heat) == '-':
            return '-'
        elif '1' in str(self._secondary_heat):
            return '1-HP compact unit' 
        elif '2' in str(self._secondary_heat):
            return '2-Heat pump(s)'
        elif '3' in str(self._secondary_heat):
            return '3-District heating, CGS'
        elif '4' in str(self._secondary_heat):
            return '4-Heating boiler'
        elif '6' in str(self._secondary_heat):
            return '6-Other'
        else:
            return '5-Direct electricity'
    
    @secondary_heat.setter
    def secondary_heat(self, _in):
        self._secondary_heat = _in

    @property
    def primary_heat_frac(self):
        return self._primary_heat_frac
    
    @primary_heat_frac.setter
    def primary_heat_frac(self, _in):
        try:
            val = float(_in)
            if val > 1:
                self._primary_heat_frac = val/100
            else:
                self._primary_heat_frac = val
        except ValueError:
            print('Primary-Heat Fraction input should be a number')
    
    @property
    def dhw_frac(self):
        return self._dhw_frac
    
    @dhw_frac.setter
    def dhw_frac(self, _in):
        try:
            val = float(_in)
            if val > 1:
                self._dhw_frac = val/100
            else:
                self._dhw_frac = val
        except ValueError:
            print('DHW-Heat Fraction input should be a number')

    @property
    def mech_cooling(self):
        if self._mech_cooling:
            return 'x'
        else:
            return None

    @mech_cooling.setter
    def mech_cooling(self, _in):
        if _in:
            self._mech_cooling = True

    def to_dict(self):
        d = {}

        d.update( {'primary_heat':self.primary_heat} )
        d.update( {'secondary_heat':self.secondary_heat} )
        d.update( {'primary_heat_frac':self.primary_heat_frac} )
        d.update( {'dhw_frac':self.dhw_frac} )
        d.update( {'mech_cooling':self.mech_cooling} )    

        return d

    def from_dict(cls, _dict):
        new_obj = cls()
        
        new_obj._primary_heat = _dict.get('primary_heat')
        new_obj._secondary_heat = _dict.get('secondary_heat')
        new_obj._primary_heat_frac = _dict.get('primary_heat_frac')
        new_obj._dhw_frac = _dict.get('dhw_frac')
        new_obj.mech_cooling = _dict.get('mech_cooling') 

        return new_obj

    def __unicode__(self):
        return u"A PHPP PER Object < {} >".format(self.id)
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
       return "{}(  _htPrim={!r}, _htSec={!r}, _ht_frac={!r},"\
           "_dhw_frac={!r}, _mechClg={!r}".format(
            self.__class__.__name__,
            self.primary_heat,
            self.secondary_heat,
            self.primary_heat_frac,
            self.dhw_frac,
            self.mech_cooling)

class PHPP_Boiler(object):
    
    # Type Data and Type/Fuel combinations allowed
    boiler_types = {
        1:  {'name':'1-None',
            'valid_fuels':['None', '-']},
        10: {'name':'10-Improved gas condensing boiler',
            'valid_fuels':[30, 31, 32, 98]},
        12: {'name':'12-Gas condensing boiler',
            'valid_fuels':[30, 31, 32, 98]},
        20: {'name':'20-Low temperature boiler gas',
            'valid_fuels':[30, 31, 32, 98]},
        11: {'name':'11-Improved oil condensing boiler',
            'valid_fuels':[20, 21, 22]},
        13: {'name':'13-Oil condensing boiler',
            'valid_fuels':[20, 21, 22]},
        21: {'name':'21-Low temperature boiler oil',
            'valid_fuels':[20, 21, 22]},
        30: {'name':'30-Firewood pieces (direct and indirect heat emission)',
            'valid_fuels':[44, 46, 47, 41, 42, 98]},
        31: {'name':'31-Wood pellets (direct and indirect heat emission)',
            'valid_fuels':[50]},
        32: {'name':'32-Wood pellets (only indirect heat emission)',
            'valid_fuels':[50]},
    }

    # PHPP Fuel-Type data
    fuel_types = {
        1:  {'name': 'None'},
        20: {'name': '20-Heating oil'},
        21: {'name': '21-Pyrolysis oil or bio oil'},
        30: {'name': '30-Natural gas'},
        31: {'name': '31-LPG'},
        32: {'name': '32-Biogas'},
        33: {'name': '33-RE-Gas'},
        44: {'name': '44-Wood logs'},
        46: {'name': '46-Forest woodchips'},
        47: {'name': '47-Poplar woodchips'},
        41: {'name': '41-Hard coal'},
        42: {'name': '42-Brown coal'},
        50: {'name': '50-Pellets'},
    }

    def __init__(self, _name="Default Boiler", _type='1-None', _fuel='None', _params=False):
        self.id = random.randint(1000,9999)
        self.name = _name
        self._type = _type
        self._type_num = 1
        self._fuel = _fuel
        self._fuel_num = 'None'
        self.params = _params

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, _in):
        if not _in: return None

        if '10' in str(_in): self._type_num = 10
        elif '11' in str(_in): self._type_num = 11
        elif '12' in str(_in): self._type_num = 12
        elif '13' in str(_in): self._type_num = 13
        elif '20' in str(_in): self._type_num = 20
        elif '21' in str(_in): self._type_num = 21
        elif '30' in str(_in): self._type_num = 30
        elif '31' in str(_in): self._type_num = 31
        elif '32' in str(_in): self._type_num = 32
        else: self._type_num = 1

        self._type = self.boiler_types[self._type_num]['name']
    @property
    def fuel(self):
        return self._fuel

    @fuel.setter
    def fuel(self, _in):
        if not _in: return None
        
        if '20' in str(_in): self._fuel_num = 20
        elif '21' in str(_in): self._fuel_num = 21
        elif '22' in str(_in): self._fuel_num = 22
        elif '30' in str(_in): self._fuel_num = 30
        elif '31' in str(_in): self._fuel_num = 31
        elif '32' in str(_in): self._fuel_num = 32
        elif '33' in str(_in): self._fuel_num = 33
        elif '44' in str(_in): self._fuel_num = 44
        elif '46' in str(_in): self._fuel_num = 46
        elif '47' in str(_in): self._fuel_num = 47
        elif '41' in str(_in): self._fuel_num = 41
        elif '42' in str(_in): self._fuel_num = 42
        elif '50' in str(_in): self._fuel_num = 50
        else: self._fuel_num = 1
        
        self._fuel = self.fuel_types.get(self._fuel_num)['name']

    def check_valid_fuel(self):
        """ Gives a warning to the user if an invalid combination of type+fuel is input """
        
        valid_fuels = self.boiler_types.get(self._type_num)['valid_fuels']
        if not self._fuel_num in valid_fuels:
            msg =  'Please select a valid fuel type.\n'\
                'The boiler type: "{}" is not \n'\
                'compatible with fuel type: "{}".'.format(self.type, self.fuel)

            return msg
        
    def get_params(self):
        """ Splits the input string/list into a dictionary
        Args:
            self.params
        Returns:
            param_dict (dict): A dict with the structure {CellRange:Value, ....}
        """
        
        if not self.params:
            return {}
        
        param_dict = {}
        for input_string in self.params:
            parts = input_string.split(':')
            if len(parts) != 2:
                continue
            else:
                param_dict[parts[0]] = parts[1]

        return param_dict

    def to_dict(self):
        d = {}

        d.update({'id':self.id})
        d.update({'name':self.name})
        d.update({'type':self.type})
        d.update({'fuel':self.fuel})
        d.update({'params':self.params})

        return d

    @classmethod
    def from_dict(cls, _dict):
        new_obj = cls()
        
        new_obj.id = _dict.get('id')
        new_obj.name = _dict.get('name')
        new_obj.type = _dict.get('type')
        new_obj.fuel = _dict.get('fuel')
        new_obj.params = _dict.get('params')

        return new_obj

    def __unicode__(self):
        return u"A PHPP Boiler Object < {} >".format(self.id)
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
       return "{}(_name={!r}, _type={!r}, _fuel={!r}, _params={!r})".format(
            self.__class__.__name__, 
            self.name,
            self.type,
            self.fuel,
            self.params,
             )
    def ToString(self):
        return str(self)

class PHPP_Cooling_SupplyAir(Object):
    def __init__(self, _on_off=None, _maxCap=1000, _seer=3):
        self.id = random.randint(1000,9999)
        self._on_off = _on_off
        self._max_capacity = _maxCap
        self._seer = _seer

    @property
    def on_off(self):
        if self._on_off:
            return 'x'
        else:
            return None

    @on_off.setter
    def on_off(self, _in):
        if _in:
            self._on_off = 'x'
        else:
            self._on_off = None

    @property
    def max_capacity(self):
        return self._max_capacity

    @max_capacity.setter
    def max_capacity(self, _in):
        self._max_capacity = _in

    @property
    def seer(self):
        return self._seer

    @seer.setter
    def seer(self, _in):
        self._seer = _in

    def to_dict(self):
        d = {}

        d.update( {'id':self.id} )
        d.update( {'on_off':self.on_off} )
        d.update( {'max_capacity':self.max_capacity} )
        d.update( {'seer':self.seer} )

        return d

    @classmethod
    def from_dict(cls, _dict):
        new_obj = cls()

        new_obj.id = _dict.get('id')
        new_obj._on_off = _dict.get('on_off')
        new_obj._max_capacity = _dict.get('max_capacity')
        new_obj._seer = _dict.get('seer')

        return new_obj

    def __unicode__(self):
        return u"A PHPP Cooling | Supply-Air Object < {} >".format(self.id)
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
       return "{}(_on_off={!r}, _maxCap={!r}, _seer={!r} )".format(
            self.__class__.__name__,
            self.on_off,
            self.max_capacity,
            self.seer)
    def ToString(self):
        return str(self)

class PHPP_Cooling_RecircAir(Object):
    def __init__(self, _on_off=None, _maxCap=1000, _nomVol=100, _varVol=None, _seer=3):
        self.id = random.randint(1000,9999)
        self._on_off = _on_off
        self._max_capacity = _maxCap
        self._nominal_vol = _nomVol
        self._variable_vol = _varVol
        self._seer = _seer

    @property
    def on_off(self):
        if self._on_off:
            return 'x'
        else:
            return None

    @on_off.setter
    def on_off(self, _in):
        if _in:
            self._on_off = 'x'
        else:
            self._on_off = None

    @property
    def max_capacity(self):
        return self._max_capacity

    @max_capacity.setter
    def max_capacity(self, _in):
        self._max_capacity = _in

    @property
    def nominal_vol(self):
        return self._nominal_vol

    @nominal_vol.setter
    def nominal_vol(self, _in):
        self._nominal_vol = _in
    
    @property
    def variable_vol(self):
        return self._variable_vol

    @variable_vol.setter
    def variable_vol(self, _in):
        self._variable_vol = 'x'
        if _in == False:
            self._variable_vol = None

    @property
    def seer(self):
        return self._seer

    @seer.setter
    def seer(self, _in):
        self._seer = _in

    def to_dict(self):
        d = {}

        d.update( {'id':self.id} )
        d.update( {'on_off':self.on_off} )
        d.update( {'max_capacity':self.max_capacity} )
        d.update( {'nominal_vol':self.nominal_vol} )
        d.update( {'variable_vol':self.variable_vol} )
        d.update( {'seer':self.seer} )

        return d

    @classmethod
    def from_dict(cls, _dict):
        new_obj = cls()

        new_obj.id = _dict.get('id')
        new_obj._on_off = _dict.get('on_off')
        new_obj._max_capacity = _dict.get('max_capacity')
        new_obj._nominal_vol = _dict.get('nominal_vol')
        new_obj._variable_vol = _dict.get('variable_vol')
        new_obj._seer = _dict.get('seer')

        return new_obj

    def __unicode__(self):
        return u"A PHPP Cooling | Recirc-Air Object < {} >".format(self.id)
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
       return "{}(_on_off={!r}, _maxCap={!r}, _nomVol={!r}, _varVol={!r}, _seer={!r} )".format(
            self.__class__.__name__, self.on_off,
            self.max_capacity, self.nominal_vol,
            self.variable_vol, self.seer)
    def ToString(self):
        return str(self)

class PHPP_Cooling_Dehumid(Object):
    def __init__(self, _wst2Rm=None, _seer=3):
        self.id = random.randint(1000,9999)
        self._waste_to_room = _wst2Rm
        self._seer = _seer
    
    @property
    def waste_to_room(self):
        if self._waste_to_room:
            return 'x'
        else:
            return None

    @waste_to_room.setter
    def waste_to_room(self, _in):
        if _in:
            self._waste_to_room = 'x'
        else:
            self._waste_to_room = None

    @property
    def seer(self):
        return self._seer

    @seer.setter
    def seer(self, _in):
        self._seer = _in

    def to_dict(self):
        d = {}

        d.update( {'id':self.id} )
        d.update( {'waste_to_room':self.waste_to_room} )
        d.update( {'seer':self.seer} )
        
        return d

    @classmethod
    def from_dict(cls, _dict):
        new_obj = cls()

        new_obj.id = _dict.get('id')
        new_obj._waste_to_room = _dict.get('waste_to_room')
        new_obj._seer = _dict.get('seer')

        return new_obj

    def __unicode__(self):
        return u"A PHPP Cooling | Dehumidification Object < {} >".format(self.id)
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
       return "{}( _wst2Rm={!r}, _seer={!r} )".format(
            self.__class__.__name__,self.waste_to_room, self.seer)
    def ToString(self):
        return str(self)

class PHPP_Cooling_Panel(Object):
    def __init__(self, _seer=3):
        self.id = random.randint(1000,9999)
        self._seer = _seer
    
    @property
    def seer(self):
        return self._seer

    @seer.setter
    def seer(self, _in):
        self._seer = _in
    
    def to_dict(self):
        d = {}

        d.update( {'id':self.id} )
        d.update( {'seer':self.seer} )

        return d

    @classmethod
    def from_dict(cls, _dict):
        new_obj = cls()

        new_obj.id = _dict.get('id')
        new_obj.seer = _dict.get('seer')

        return new_obj

    def __unicode__(self):
        return u"A PHPP Cooling | Panel Object < {} >".format(self.id)
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
       return "{}( _seer={!r} )".format(
            self.__class__.__name__, self.seer)
    def ToString(self):
        return str(self)

class PHPP_HP_AirSource(Object):
    def __init__(self, _nm='Default Heat Pump', _src='1-Outdoor air', 
            _tsrcs=[-7.0, 2.0, 7.0, 15.0, 20.0, -7.0, 2.0, 7.0, 15.0, 20.0],
            _tsnks=[35.0, 35.0, 35.0, 35.0, 35.0, 50.0, 50.0, 50.0, 50.0, 50.0], 
            _hcs=[2.16, 2.64, 3.12, 3.75, 4.08, 2.04, 2.52, 3.00, 3.72, 3.87], 
            _cops=[2.70, 3.10, 3.70, 4.30, 4.90, 2.00, 2.30, 2.80, 3.30, 3.50], 
            _dtSnks=5.00, _warnings=[]):
        self.id = random.randint(1000,9999)
        self.name = _nm
        self._source = _src
        self._T_sources = _tsrcs
        self._T_sinks = _tsnks
        self._hcs = _hcs
        self._cops = _cops
        self.sink_dt = _dtSnks
        self.warnings = _warnings

    @property
    def source(self):
        if '2' in str(self._source):
            return "2-Ground water"
        elif '3' in str(self._source):
            return "3-Ground probes"
        elif '4' in str(self._source):
            return "4-Horizontal ground collector"
        else:
            return "1-Outdoor air"

    @source.setter
    def source(self, _in):
        self._source = _in

    @property
    def temps_sources(self):
        return self._T_sources

    @temps_sources.setter
    def temps_sources(self, _in):
        if not _in:
            pass
        
        if len(_in)>15:
            msg = 'PHPP limits the number of test points to 15. For now I will\n'\
            'only use the first 15 entries in "_temps_source"'
            self.warnings.append( msg )
            self._T_sources = _in[0:15]
        else:
            self._T_sources = _in

    @property
    def temps_sinks(self):
        return self._T_sinks

    @temps_sinks.setter
    def temps_sinks(self, _in):
        if not _in:
            pass
        
        if len(_in)>15:
            msg = 'PHPP limits the number of test points to 15. For now I will\n'\
            'only use the first 15 entries in "_temps_sink"'
            self.warnings.append( msg )
            self._T_sinks = _in[0:15]
        else:
            self._T_sinks = _in

    @property
    def heating_capacities(self):
        return self._hcs

    @heating_capacities.setter
    def heating_capacities(self, _in):
        if not _in:
            pass
        
        if len(_in)>15:
            msg = 'PHPP limits the number of test points to 15. For now I will\n'\
            'only use the first 15 entries in "_heating_capacities"'
            self.warnings.append( msg )
            self._hcs = _in[0:15]
        else:
            self._hcs = _in

    @property
    def cops(self):
        return self._cops

    @cops.setter
    def cops(self, _in):
        if not _in:
            pass
        
        if len(_in)>15:
            msg = 'PHPP limits the number of test points to 15. For now I will\n'\
            'only use the first 15 entries in "_COPs"'
            self.warnings.append( msg )
            self._cops = _in[0:15]
        else:
            self._cops = _in

    def to_dict(self):
        d = {}

        d.update( {'id':self.id} )
        d.update( {'name':self.name} )
        d.update( {'_source':self.source} )
        d.update( {'_T_sources':self.temps_sources} )
        d.update( {'_T_sinks':self.temps_sinks} ) 
        d.update( {'_hcs':self.heating_capacities} ) 
        d.update( {'_cops':self.cops} ) 
        d.update( {'sink_dt':self.sink_dt} ) 
        
        return d

    @classmethod
    def from_dict(cls, _dict):
        new_obj = cls()

        new_obj.id = _dict.get('id')
        new_obj.name = _dict.get('name')
        new_obj._source = _dict.get('_source')
        new_obj._T_sources = _dict.get('_T_sources')
        new_obj._T_sinks = _dict.get('_T_sinks')
        new_obj._hcs = _dict.get('_hcs')
        new_obj._cops = _dict.get('_cops')
        new_obj.sink_dt = _dict.get('sink_dt')

        return new_obj

    def __unicode__(self):
        return u"A PHPP Heat-Pump | Air-Source Object < {} >".format(self.id)
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
       return "{}(_nm={!r}, _src={!r}, _tsrcs={!r},_tsnks={!r}, _hcs={!r},"\
                "_cops={!r}, _dtSnks={!r}, _warnings={!r})".format(
            self.__class__.__name__, self.name, self._source,
            self._T_sources, self._T_sinks, self._hcs,
            self._cops, self.sink_dt, self.warnings)
    def ToString(self):
        return str(self)

class PHPP_HP_Options(Object):
    def __init__(self, _fwdT=35, _ph_dist='3-Supply air heating', _nPwr=None,
    _radExp=None, _bckpType='1-Elec. Immersion heater', _dTelec=None, _hpPrior='1-DHW-priority',
    _hpCntrl='1-On/Off', _dGrndWtr=None, _pGrndWtr=None ):
        self.id = random.randint(1000,9999)

        self._hp_dist = _ph_dist
        self._backup_type = _bckpType
        self._hp_priority =_hpPrior
        self._hp_control = _hpCntrl
        
        self.frwd_temp = _fwdT
        self.nom_power = _nPwr
        self.rad_exponent =_radExp
        self.dT_elec_flow = _dTelec
        self.depth_groundwater = _dGrndWtr
        self.power_groundwater = _pGrndWtr

    @property
    def hp_distribution(self):
        return self._hp_dist

    @hp_distribution.setter
    def hp_distribution(self, _in):
        if not _in:
            return None

        if '1' in str(_in):
            self._hp_dist = '1-Underfloor heating'
        elif '2' in str(_in):
            self._hp_dist = '2-Radiators'
        else:
            self._hp_dist = '3-Supply air heating'

    @property
    def backup_type(self):
        return self._backup_type

    @backup_type.setter
    def backup_type(self, _in):
        if not _in:
            return None

        if '2' in str(_in):
            self._backup_type = '2-Electric continuous flow water heater'
        else:
            self._backup_type = '1-Elec. Immersion heater'

    @property
    def hp_priority(self):
        return self._hp_priority

    @hp_priority.setter
    def hp_priority(self, _in):
        if not _in:
            return None

        if '2' in str(_in):
            self._hp_priority = '2-Heating priority'
        else:
            self._hp_priority = '1-DHW-priority'

    @property
    def hp_control(self):
        return self._hp_control

    @hp_control.setter
    def hp_control(self, _in):
        if not _in:
            return None

        if '2' in str(_in):
            self._hp_control = '2-Ideal'
        else:
            self._hp_control = '1-On/Off'

    def to_dict(self):
        d = {}

        d.update( {'id':self.id} )
        d.update( {'hp_distribution':self.hp_distribution} )
        d.update( {'backup_type':self.backup_type} )
        d.update( {'hp_priority':self.hp_priority} )
        d.update( {'hp_control':self.hp_control} )
        d.update( {'frwd_temp':self.frwd_temp} )
        d.update( {'nom_power':self.nom_power} )
        d.update( {'rad_exponent':self.rad_exponent} )
        d.update( {'dT_elec_flow':self.dT_elec_flow} )
        d.update( {'depth_groundwater':self.depth_groundwater} )
        d.update( {'power_groundwater':self.power_groundwater} )

        return d
    
    @classmethod
    def from_dict(cls, _dict):
        new_obj = cls()

        new_obj.id = _dict.get('id')
        new_obj._hp_dist = _dict.get('hp_distribution')
        new_obj._backup_type = _dict.get('backup_type')
        new_obj._hp_priority = _dict.get('hp_priority')
        new_obj._hp_control = _dict.get('hp_control')
        new_obj.frwd_temp = _dict.get('frwd_temp')
        new_obj.nom_power = _dict.get('nom_power')
        new_obj.rad_exponent = _dict.get('rad_exponent')
        new_obj.dT_elec_flow = _dict.get('dT_elec_flow')
        new_obj.depth_groundwater = _dict.get('depth_groundwater')
        new_obj.power_groundwater = _dict.get('power_groundwater')

        return new_obj

    def __unicode__(self):
        return u"A PHPP Heat-Pump | Options Object < {} >".format(self.id)
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
       return "{}(_fwdT={!r}, _ph_dist={!r}, _nPwr={!r}, _radExp={!r}, _bckpType={!r},"\
                "_dTelec={!r}, _hpPrior={!r}, _hpCntrl={!r}, _dGrndWtr={!r}, _pGrndWtr={!r}  )".format(
            self.__class__.__name__, self._hp_dist,
            self._backup_type,
            self._hp_priority,
            self._hp_control,        
            self.frwd_temp,
            self.nom_power,
            self.rad_exponent,
            self.dT_elec_flow,
            self.depth_groundwater,
            self.power_groundwater )
    def ToString(self):
        return str(self)



