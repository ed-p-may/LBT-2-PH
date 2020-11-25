import math
from occupancy import Occupancy
import ghpythonlib.components as ghc
import Grasshopper.Kernel as ghK
import random
from System import Object

class ApplianceSet(Object):

    def __init__(self, _appliance_list=[], _hb_room_ids=[]):
        self.id = random.randint(1000,9999)
        self.appliance_list = _appliance_list
        self._host_room_tfa = None
        self._lighting_efficacy = None

    def __iter__(self):
        return self.appliance_list

    @property
    def lighting_efficacy(self):
        if self._lighting_efficacy:
            return self._lighting_efficacy
        else:
            return 50

    @lighting_efficacy.setter
    def lighting_efficacy(self, _input):
        self._lighting_efficacy = _input

    @property
    def host_room_tfa(self):
        return self._host_room_tfa

    @host_room_tfa.setter
    def host_room_tfa(self, _in):
        try:
            self._host_room_tfa = float( _in )
        except Exception as e:
            print(e)

    def to_dict(self):
        d = {}

        d.update( {'id':self.id} )
        d.update( {'_host_room_tfa':self.host_room_tfa} )
        d.update( {'lighting_efficacy':self.lighting_efficacy} )
                
        appliances = {}
        for appliance in self.appliance_list:
            appliances.update( {appliance.id:appliance.to_dict()} )
        d.update( {'appliance_list':appliances } )
        
        return d

    @classmethod
    def from_dict(cls, _dict):
        new_obj = cls()

        new_obj.id = _dict.get('id')
        new_obj._host_room_tfa = _dict.get('_host_room_tfa')    
        new_obj.lighting_efficacy = _dict.get('lighting_efficacy')      
        
        new_obj.appliance_list = []
        appliance_dict = _dict.get('appliance_list')
        for appliance in appliance_dict.values():
            new_obj.appliance_list.append( ElecEquipAppliance.from_dict( appliance) )

        return new_obj

    def hb_lighting_per_m2(self, _occupancy, _floor_area):
        
        lighting_FrequencyPerPerson = 2.9 #kh/(Person-year)
        lighting_Frequency = lighting_FrequencyPerPerson * _occupancy
        lighting_Demand = 720 /  self.lighting_efficacy
        lighting_UtilizFactor = 1
        lighting_AnnualEnergy = lighting_Demand * lighting_UtilizFactor * lighting_Frequency #kWh / year
        lighting_AvgHourlyWattage =  lighting_AnnualEnergy * 1000  / 8760 # Annual Average W / hour for a constant schedule
        lightingDensityPerArea = lighting_AvgHourlyWattage / _floor_area
        
        return lightingDensityPerArea

    def hb_elec_equip_per_m2(self, _occupancy, _num_units, _floor_area):

        appliance_annual_kWh = [appliance.calc_annual_demand(_occupancy, _num_units) for appliance in self.appliance_list]
        appliance_avg_hourly_W = sum(appliance_annual_kWh) * 1000 / 8760
        specific_appliance_avg_hourly_W = appliance_avg_hourly_W / _floor_area

        return specific_appliance_avg_hourly_W

    def __unicode__(self):
        return u'PHPP Style Appliances Collection: < {} >'.format(self.id)
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
        return "{}( _appliance_list={!r}, _hb_room_ids={!r})".format(
                self.__class__.__name__,
                self.appliance_list,
                self.hb_host_room_ids)


class ElecEquipAppliance(Object):
    defaults = {
        'dishwasher': {'demand': 1.1, 'util_frac': 1, 'freq':65},
        'clothesWasher':{'demand':1.1, 'util_frac': 1, 'freq':57},
        'clothesDryer':{'demand':3.5, 'util_frac': 1, 'freq':57},
        'fridge':{'demand':0.78, 'util_frac': 1, 'freq':365},
        'freezer':{'demand':0.88, 'util_frac': 1, 'freq':365},
        'fridgeFreezer':{'demand':1.0, 'util_frac': 1, 'freq':365},
        'cooking':{'demand':0.25, 'util_frac': 1, 'freq':500},
        'other_kWhYear_':{'demand':0.0, 'util_frac': 1, 'freq':1},
        'consumerElec':{'demand': 80.0, 'util_frac': 1, 'freq':0.55},
    }
    
    def __init__(self, _nm=None, _nomDem=None, _utilFac=None, _freq=None, _type=None):
        self.id = random.randint(1000,9999)
        self.name = _nm
        self._nominal_demand = _nomDem
        self._utilization_factor = _utilFac
        self._frequency = _freq
        self._type = _type
        self.hb_wattage = None
        self.hb_avg_daily_util_frac = None

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, _input_val):
        if self.name == 'dishwasher':
            if '2' in str(_input_val):
                self._type = '2-Cold water connection'
            else:
                self._type =  '1-DHW connection'
        elif self.name == 'clothesWasher':
            if '2' in str(_input_val):
                self._type =  '2-Cold water connection'
            else:
                self._type =  '1-DHW connection'
        elif self.name == 'clothesDryer':
            if '1' in str(_input_val):
                self._type =  '1-Clothes line'
            if '2' in str(_input_val):
                self._type =  '2-Drying closet (cold!)'
            elif '3' in str(_input_val):
                self._type =  '3-Drying closet (cold!) in extract air'
            elif '5' in str(_input_val):
                self._type =  '5-Electric exhaust air dryer'
            elif '6' in str(_input_val):
                self._type =  '6-Gas exhaust air dryer'
            else:
                self._type =  '4-Condensation dryer'
        elif self.name == 'cooking':
            if '2' in str(_input_val):
                self._type =  '2-Natural gas'
            elif '3' in str(_input_val):
                self._type =  '3-LPG'
            else:
                self._type =  '1-Electricity'
        else:
            self._type =  None

    @property
    def frequency(self):
        return self._frequency

    @frequency.setter
    def frequency(self, _in):
        if not _in:
            self._frequency = self.defaults.get(self.name, {}).get('freq', 0)
        else:
            self._frequency = float(_in)

    @property
    def utilization_factor(self):
        return self._utilization_factor

    @utilization_factor.setter
    def utilization_factor(self, _in):
        if not _in:
            self._utilization_factor = self.defaults.get(self.name, {}).get('util_frac', 0)
        else:
            self._utilization_factor = float(_in)

    @property
    def nominal_demand(self):
        return self._nominal_demand
    
    @nominal_demand.setter
    def nominal_demand(self, _in):
        if not _in:
            self._nominal_demand = self.defaults.get(self.name, {}).get('demand', 0)
        else:
            self._nominal_demand = float(_in)

    def calc_annual_demand(self, _bldgOccupancy=0, _numResUnits=0):
        demandByOccupancy = self.nominal_demand * self.utilization_factor * self.frequency * _bldgOccupancy 
        demandByHousehold = self.nominal_demand * self.utilization_factor * self.frequency * _numResUnits
        
        if self.name == 'fridge' or self.name == 'freezer' or self.name == 'fridgeFreezer':
            return demandByHousehold
        elif self.name == 'other':
            return self.nominal_demand
        else:
            return demandByOccupancy
    
    @classmethod
    def from_ud(cls, _use_defaults, _name, _nom_demand, _utilFac=None, _freq=None, _type=None):
        if not _use_defaults and not _nom_demand:
            return None
        else:
            appliance_obj = cls()
            appliance_obj.name = _name
            appliance_obj.utilization_factor = _utilFac
            appliance_obj.type = _type
            appliance_obj.frequency = _freq
            appliance_obj.nominal_demand = _nom_demand
        
            return appliance_obj

    @classmethod
    def from_hb(cls, _name, _load, _sched):
        appliance_obj = cls()
        appliance_obj.name = _name   
        appliance_obj.hb_wattage = _load
        appliance_obj.hb_avg_daily_util_frac = _sched

        return appliance_obj

    def to_dict(self):
        d = {}

        d.update( {'id':self.id} )
        d.update( {'name':self.name} )
        d.update( {'_nominal_demand':self.nominal_demand} )
        d.update( {'_utilization_factor':self.utilization_factor} )
        d.update( {'_frequency':self.frequency} )
        d.update( {'_type':self._type} )
        d.update( {'hb_wattage':self.hb_wattage} )
        d.update( {'hb_avg_daily_util_frac':self.hb_avg_daily_util_frac} )

        return d

    @classmethod
    def from_dict(cls, _dict):
        new_obj = cls()

        new_obj.id = _dict.get('id')
        new_obj.name = _dict.get('name')
        new_obj._nominal_demand = _dict.get('_nominal_demand')
        new_obj._utilization_factor = _dict.get('_utilization_factor')
        new_obj._frequency = _dict.get('_frequency')
        new_obj._type = _dict.get('_type')
        new_obj.hb_wattage = _dict.get('hb_wattage')
        new_obj.hb_avg_daily_util_frac = _dict.get('hb_avg_daily_util_frac')

        return new_obj

    def __unicode__(self):
        return u'PHPP Style Appliance: {}'.format(self.name)
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
        return "{}( _nm={!r}, _nomDem={!r}, _utilFac={!r}, _freq={!r}, type={!r})".format(
                self.__class__.__name__,
                self.name,
                self._nominal_demand,
                self.utilization_factor,
                self.frequency,
                self.type)


class PNNL_ResidentialLoads:
    # Fraction Schedules from PNNL Example IDF Files
    # https://www.energycodes.gov/development/residential/iecc_models
    schedules = {
        'refrigerator': [0.80,0.78,0.77,0.74,0.73,0.73,0.76,0.80,0.82,0.83,0.80,0.80,0.84,0.84,0.83,0.84,0.89,0.97,1.00,0.97,0.94,0.93,0.89,0.83],
        'dishwasher': [0.12,0.05,0.04,0.03,0.03,0.08,0.15,0.23,0.44,0.49,0.43,0.36,0.31,0.35,0.28,0.27,0.28,0.37,0.66,0.84,0.68,0.50,0.33,0.23],
        'clotheswasher': [0.08,0.06,0.03,0.03,0.06,0.10,0.19,0.41,0.62,0.73,0.72,0.64,0.57,0.51,0.45,0.41,0.43,0.41,0.41,0.41,0.41,0.40,0.27,0.14],
        'clothesdryer': [0.10,0.06,0.04,0.02,0.04,0.06,0.16,0.32,0.49,0.69,0.79,0.82,0.75,0.68,0.61,0.58,0.56,0.55,0.52,0.51,0.53,0.55,0.44,0.24],
        'stove': [0.05,0.05,0.02,0.02,0.05,0.07,0.17,0.28,0.31,0.32,0.28,0.33,0.38,0.31,0.29,0.38,0.61,1.00,0.78,0.40,0.24,0.17,0.10,0.07],
        'mel': [0.61,0.56,0.55,0.55,0.52,0.59,0.68,0.72,0.61,0.52,0.53,0.53,0.52,0.54,0.57,0.60,0.71,0.86,0.94,0.97,1.00,0.98,0.85,0.73],
        'plugloads': [0.61,0.56,0.55,0.55,0.52,0.59,0.68,0.72,0.61,0.52,0.53,0.53,0.52,0.54,0.57,0.60,0.71,0.86,0.94,0.97,1.00,0.98,0.85,0.73],
        'occupancy' : [1.00000,1.00000,1.00000,1.00000,1.00000,1.00000,1.00000,0.88310,0.40861,0.24189,0.24189,0.24189,0.24189,0.24189,0.24189,0.2418,0.29498,0.55310,0.89693,0.89693,0.89693,1.00000,1.00000,1.00000],
        'lighting' : [0.06875,0.06875,0.0687,0.06875,0.20625,0.4296875,0.48125,0.4296875,0.1890625,0.12890625,0.12890625,0.12890625,0.12890625,0.12890625,0.12890625,0.2234375,0.48125,0.6703125,0.90234375,1,1,0.75625,0.42109375,0.171875]
    }

    loads = {
        'refrigerator':91.058,
        'dishwasher': 65.699,
        'clotheswasher': 28.478,
        'clothesdryer':213.065,
        'stove': 248.154,
        'mel':1.713,
        'plugloads':1.544,
        'lighting':1.63,     # (1.15 W/m2 (Hardwired)  + 0.48 W/m2 (Plugin) = 1.63 W/,2)
        'occupancy':0.0091   # (People / m2)
    }
    
    def __init__(self):
        pass

    def schedule(self, _type):
        return self.schedules.get(_type, None)

    def load(self, _type):
        return self.loads.get(_type, None)

    def set_load(self, _load_type, _ud_val):
        if _ud_val:
            self.loads[_load_type] = _ud_val

    def _hourly_wattage(self, _hb_room_floor_area):
        # Calc the hourly Wattage values (load * fraction)
        wattHr_ref =   [ self.load('refrigerator') * hour for hour in self.schedule('refrigerator') ]
        wattHr_dw =    [ self.load('dishwasher') * hour for hour in self.schedule('dishwasher') ]
        wattHr_clWsh = [ self.load('clotheswasher') * hour for hour in self.schedule('clotheswasher') ]
        wattHr_dryer = [ self.load('clothesdryer') * hour for hour in self.schedule('clothesdryer') ]
        wattHr_stove = [ self.load('stove') * hour for hour in self.schedule('stove') ]
        wattHr_mel =   [ self.load('mel') * hour * _hb_room_floor_area for hour in self.schedule('mel') ]
        wattHr_pl =    [ self.load('plugloads') * hour * _hb_room_floor_area for hour in self.schedule('plugloads') ]
        
        # Sum up the wattage from each appliance for each hour
        hourly_total_wattage = []
        for i in range(24):
            hourly_total_wattage.append(wattHr_ref[i] + wattHr_dw[i] + wattHr_clWsh[i] + wattHr_dryer[i] + wattHr_stove[i] + wattHr_mel[i] + wattHr_pl[i])

        return hourly_total_wattage

    def calc_elec_equip_load(self, _hb_room_floor_area):
        peak_wattage = max( self._hourly_wattage( _hb_room_floor_area ) )
        
        return  peak_wattage / _hb_room_floor_area

    def calc_elec_equip_sched(self, _hb_room_floor_area):
        hourly_wattage = self._hourly_wattage( _hb_room_floor_area )
        peak_wattage = max( hourly_wattage )
        
        return [hourly_wattage / peak_wattage for hourly_wattage in hourly_wattage]

    def get_phpp_values(self, _name):
        name = _name
        load = self.load(_name)
        sched = self.schedule(_name)
        avg_util = sum(sched)/len(sched)

        return ( name, load, avg_util  )
