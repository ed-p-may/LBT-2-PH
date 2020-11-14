import math
import ghpythonlib.components as ghc
import Grasshopper.Kernel as ghK
import random

class Appliances:

    def __init__(self, _appliance_list=[]):
        self.id = random.randint(1000,9999)
        self.appliance_list = _appliance_list

    def to_dict(self):
        d = {}

        d.update( {'id':self.id} )
        
        appliances = {}
        for appliance in self.appliance_list:
            appliances.update( {appliance.id:appliance.to_dict()} )
        d.update( {'appliance_list':appliances } )
        
        return d

    @classmethod
    def from_dict(cls, _dict):
        new_obj = cls()

        new_obj.id = _dict.get('id')
        new_obj.appliance_list = []
        appliance_dict = _dict.get('appliance_list')
        for appliance in appliance_dict.values():
            new_obj.appliance_list.append( ElecEquipAppliance.from_dict( appliance) )

        return new_obj

    def __unicode__(self):
        return u'PHPP Style Appliances List: < {} >'.format(self.id)
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
        return "{}( _appliance_list={!r})".format(
                self.__class__.__name__,
                self.appliance_list)


class ElecEquipAppliance():
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
    
    def __init__(self, _nm=None, _nomDem=None, _utilFac=1, _freq=1, type=None):
        self.id = random.randint(1000,9999)
        self.name = _nm
        self._nominal_demand = _nomDem
        self.utilization_factor = float(_utilFac) if _utilFac else 1
        self.frequency = float(_freq) if _freq else 1
        self.type = type
    
    @property
    def nominal_demand(self):
        if self._nominal_demand is None:
            return None
        
        try:
            return float(self._nominal_demand)
        except:
            return self.defaults.get(self.name, 0)
    
    def calc_annual_demand(self, _bldgOccupancy=0, _numResUnits=0):
        demandByOccupancy = self.nominal_demand * self.utilization_factor * self.frequency * _bldgOccupancy 
        demandByHousehold = self.nominal_demand * self.utilization_factor * self.frequency * _numResUnits
        
        if self.Name == 'fridge' or self.Name == 'freezer' or self.Name == 'fridgeFreezer':
            return demandByHousehold
        elif self.Name == 'other':
            return self.nominal_demand
        else:
            return demandByOccupancy
    
    def to_dict(self):
        d = {}

        d.update( {'id':self.id} )
        d.update( {'name':self.name} )
        d.update( {'id':self.id} )
        d.update( {'_nominal_demand':self.nominal_demand} )
        d.update( {'utilization_factor':self.utilization_factor} )
        d.update( {'frequency':self.frequency} )
        d.update( {'type':self.type} )

        return d

    @classmethod
    def from_dict(cls, _dict):
        new_obj = cls()

        new_obj.id = _dict.get('id')
        new_obj.name = _dict.get('name')
        new_obj.nominal_demand = _dict.get('_nominal_demand')
        new_obj.utilization_factor = _dict.get('utilization_factor')
        new_obj.frequency = _dict.get('frequency')
        new_obj.type = _dict.get('type')

        return new_obj

    def __unicode__(self):
        return u'PHPP Style Appliance: {}'.format(self.Name)
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


def calc_occupancy(_hb_rooms, _num_dwelling_units):
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
    bldgOccupancy = (1+1.9*(1 - math.exp(-0.00013 * math.pow((bldgTFA/_num_dwelling_units-7), 2))) + 0.001 * bldgTFA/_num_dwelling_units ) * _num_dwelling_units
    bldgFloorArea = sum([get_zone_total_floor_area(room) for room in _hb_rooms])
    
    return bldgFloorArea, bldgOccupancy, bldgOccupancy / bldgFloorArea

def calc_lighting(_lightingEff, _bldgOcc, _bldgFloorArea):
    lighting_FrequencyPerPerson = 2.9 #kh/(Person-year)
    lighting_Frequency = lighting_FrequencyPerPerson * _bldgOcc
    lighting_Demand = 720 / _lightingEff
    lighting_UtilizFactor = 1
    lighting_AnnualEnergy = lighting_Demand * lighting_UtilizFactor * lighting_Frequency #kWh / year
    lighting_AvgHourlyWattage =  lighting_AnnualEnergy * 1000  / 8760 # Annual Average W / hour for a constant schedule
    lightingDensityPerArea = lighting_AvgHourlyWattage / _bldgFloorArea # For constant operation schedule
    
    return lightingDensityPerArea

def calc_elec_equip_appliances(_hb_rooms, _bldgOcc, _numUnits, _bldgFA, _ghenv):
    appliances = []
    for room in _hb_rooms:
        phpp_dict = room.user_data.get('phpp', {})
        appliance_dict = phpp_dict.get('appliances', None)
        new_obj = Appliances.from_dict(appliance_dict)
        print new_obj.appliance_list
        if not appliance_dict:
            msg = 'Error getting appliance values for HB Room: <{}>. Are you sure you applied\n'\
                'values to this room using the "PHPP Res. Appliance" component?'.format(room.display_name)
            _ghenv.Component.AddRuntimeMessage( ghK.GH_RuntimeMessageLevel.Error, msg )


    
    #appliances = [appliance for room in _hb_rooms for appliance in room.PHPP_ElecEquip]
    #appliance_annual_kWh = [appliance.calcAnnualDemand(_bldgOcc, _numUnits) for appliance in appliances]
    #appliance_avg_hourly_W = sum(appliance_annual_kWh) * 1000 / 8760
    
    return None#appliance_avg_hourly_W / _bldgFA



