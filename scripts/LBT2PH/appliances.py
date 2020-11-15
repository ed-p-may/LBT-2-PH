import math
import ghpythonlib.components as ghc
import Grasshopper.Kernel as ghK
import random
from System import Object


class Appliances(Object):

    def __init__(self, _appliance_list=[], _hb_room_ids=[]):
        self.id = random.randint(1000,9999)
        self.hb_host_room_ids = _hb_room_ids
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
        d.update( {'hb_host_room_ids':self.hb_host_room_ids} )
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
        new_obj.hb_host_room_ids = _dict.get('hb_host_room_ids')
        new_obj._host_room_tfa = _dict.get('_host_room_tfa')    
        new_obj.lighting_efficacy = _dict.get('lighting_efficacy')      
        
        new_obj.appliance_list = []
        appliance_dict = _dict.get('appliance_list')
        for appliance in appliance_dict.values():
            new_obj.appliance_list.append( ElecEquipAppliance.from_dict( appliance) )

        return new_obj

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
        'dishwasher':1.1,
        'clothesWasher':1.1,
        'clothesDryer':3.5,
        'fridge':0.78,
        'freezer':0.88,
        'fridgeFreezer':1.0,
        'cooking':0.25,
        'other_kWhYear_':0.0,
        'consumerElec': 80.0
    }
    
    def __init__(self, _nm=None, _nomDem=None, _utilFac=1, _freq=1, _type=None):
        self.id = random.randint(1000,9999)
        self.name = _nm
        self._nominal_demand = _nomDem
        self.utilization_factor = float(_utilFac) if _utilFac else 1
        self.frequency = float(_freq) if _freq else 1
        self._type = _type

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
    def nominal_demand(self):
        if self._nominal_demand is None:
            return None
        
        try:
            return float(self._nominal_demand)
        except:
            return self.defaults.get(self.name, 0)
    
    @nominal_demand.setter
    def nominal_demand(self, _input_val):
        self._nominal_demand = _input_val

    def calc_annual_demand(self, _bldgOccupancy=0, _numResUnits=0):
        demandByOccupancy = self.nominal_demand * self.utilization_factor * self.frequency * _bldgOccupancy 
        demandByHousehold = self.nominal_demand * self.utilization_factor * self.frequency * _numResUnits
        
        if self.name == 'fridge' or self.name == 'freezer' or self.name == 'fridgeFreezer':
            return demandByHousehold
        elif self.name == 'other':
            return self.nominal_demand
        else:
            return demandByOccupancy
    
    def to_dict(self):
        d = {}

        d.update( {'id':self.id} )
        d.update( {'name':self.name} )
        d.update( {'_nominal_demand':self.nominal_demand} )
        d.update( {'utilization_factor':self.utilization_factor} )
        d.update( {'frequency':self.frequency} )
        d.update( {'_type':self._type} )

        return d

    @classmethod
    def from_dict(cls, _dict):
        new_obj = cls()

        new_obj.id = _dict.get('id')
        new_obj.name = _dict.get('name')
        new_obj.nominal_demand = _dict.get('_nominal_demand')
        new_obj.utilization_factor = _dict.get('utilization_factor')
        new_obj.frequency = _dict.get('frequency')
        new_obj._type = _dict.get('_type')

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


def calc_occupancy(_hb_rooms, _num_res_units):
    def get_hb_room_TFA(hb_room):
        phpp_dict = hb_room.user_data.get('phpp')
        if not phpp_dict:
            return 0
        
        spaces_dict = phpp_dict.get('spaces')
        if not spaces_dict:
            return 0
        
        return sum(space.get('_tfa', 0) for space in spaces_dict.values())
    
    def get_zone_total_floor_area(hb_room):       
        return sum(face.area for face in hb_room.faces if str(face.type=='Floor'))
    
    # 1) Get the total Building TFA
    # 2) Calc the total buiding occupancy based on the total TFA
    #    Formula used here is from PHPP 'Verification' worksheet
    # 3) Figure out the Building's Total EP Floor Area
    # 4) Calc the building's Occupancy Per floor-area
    #
    # Returns PHPP Occupancy normalized by E+ Floor Area (gross)
    
    bldgTFA = sum([get_hb_room_TFA(zone) for zone in _hb_rooms])
    bldgOccupancy = (1+1.9*(1 - math.exp(-0.00013 * math.pow((bldgTFA/_num_res_units-7), 2))) + 0.001 * bldgTFA/_num_res_units ) * _num_res_units
    bldgFloorArea = sum([get_zone_total_floor_area(room) for room in _hb_rooms])
    
    return bldgFloorArea, bldgOccupancy, bldgOccupancy / bldgFloorArea

def calc_lighting(_hb_rooms, _bldgOcc, _bldgFloorArea):
    
    def calc_weighted_efficacy(_hb_rooms):
        weighted_efficacies = []
        hb_room_tfas = []
        for room in _hb_rooms:
            space_tfas = []
            lighting_efficacy = room.user_data.get('phpp', {}).get('appliances', {}).get('lighting_efficacy', None)
            for space_dict in room.user_data.get('phpp', {}).get('spaces', {}).values():
                space_tfas.append( space_dict.get('_tfa', 0) )
            
            space_tfa = sum(space_tfas)
            weighted_efficacies.append( float(lighting_efficacy) * space_tfa )
            hb_room_tfas.append( space_tfa )

        if weighted_efficacies and hb_room_tfas:
            return sum(weighted_efficacies) / sum(hb_room_tfas)
        else:
            return 50
    
    lighting_FrequencyPerPerson = 2.9 #kh/(Person-year)
    lighting_Frequency = lighting_FrequencyPerPerson * _bldgOcc
    area_weighted_efficacy = calc_weighted_efficacy( _hb_rooms )
    lighting_Demand = 720 / area_weighted_efficacy
    lighting_UtilizFactor = 1
    lighting_AnnualEnergy = lighting_Demand * lighting_UtilizFactor * lighting_Frequency #kWh / year
    lighting_AvgHourlyWattage =  lighting_AnnualEnergy * 1000  / 8760 # Annual Average W / hour for a constant schedule
    lightingDensityPerArea = lighting_AvgHourlyWattage / _bldgFloorArea # For constant operation schedule
    
    return lightingDensityPerArea

def calc_elec_equip_appliances(_hb_rooms, _num_res_units, _bldgOcc, _bldgFA, _ghenv):
    appliances = []
    
    # Pull out all the appliances in all the hb-zones
    for room in _hb_rooms:
        phpp_dict = room.user_data.get('phpp', {})
        appliances_dict = phpp_dict.get('appliances', None)
        appliances = Appliances.from_dict( appliances_dict )
        
        if not appliances_dict:
            msg = 'Error getting appliance values for HB Room: <{}>. Are you sure you applied\n'\
                'values to this room using the "PHPP Res. Appliance" component?'.format(room.display_name)
            _ghenv.Component.AddRuntimeMessage( ghK.GH_RuntimeMessageLevel.Error, msg )

    # Find the total building (all the hb-rooms) annual average values
    appliance_annual_kWh = [appliance.calc_annual_demand(_bldgOcc, _num_res_units)  for appliance in appliances]
    appliance_avg_hourly_W = sum(appliance_annual_kWh) * 1000 / 8760
    specific_appliance_avg_hourly_W = appliance_avg_hourly_W / _bldgFA

    return specific_appliance_avg_hourly_W



