import Grasshopper.Kernel as ghK
import random


class PHPP_Verification:
    def __init__(self, _numResUnits=1, _specCapacity=60, _bldgName=None,
                _bldgCountry='US-United States of America', _bldgType='1-Residential building', 
                _ihgType='10-Dwelling', _ihgVals='2-Standard', _occupancy=None,
                _cert_stndard='1-Passive House', _cert_class="1-Classic", _pe="1-PE (non-renewable)",
                _enerPHit="2-Energy demand method", _retrofit="1-New building"):
        self.id = random.randint(1000,9999)
        self._num_res_units = _numResUnits
        self._spec_capacity = _specCapacity
        self.bldg_name = _bldgName
        self.bldg_country = _bldgCountry
        self._building_type = _bldgType
        self._ihg_type = _ihgType
        self._ihg_values = _ihgVals
        self._occupancy = _occupancy
        self._cert_standard = _cert_stndard
        self._cert_class = _cert_class
        self._cert_pe = _pe
        self._enerPHit = _enerPHit
        self._retrofit = _retrofit

    @property
    def occupancy(self):
        if self._occupancy:
            return self.occupancy
        else:
            return None

    @property
    def spec_capacity(self):
        try:
            return float(self._spec_capacity)
        except Exception as e:
            print(e)
            return 60

    @property
    def occupancy_method(self):
        if self.occupancy:
            return '2-User determined'
        else:
            return '1-Standard (only for residential buildings)'

    @property
    def num_res_units(self):
        if '2' in self.occupancy_method:
            return 1
        else:
            return self._num_res_units

    @property
    def building_type(self):
        if '2' in str(self._building_type):
            return "2-Non-residential building"
        else:
            return "1-Residential building"

    @property
    def ihg_type(self):
        if '11' in self._ihg_type:
            return "11-Nursing home / students"
        elif '12' in self._ihg_type:
            return "12-Other"
        elif '20' in self._ihg_type:
            return "20-Office / Admin. building"
        elif '21' in self._ihg_type:
            return "21-School"
        elif '22' in self._ihg_type:
            return "22-Other"
        else:
            return "10-Dwelling"
    
    @property
    def ihg_values(self):
        if 'Non' in self.building_type:
            if '4' in str(self._ihg_values):
                return "4-PHPP calculation ('IHG non-res' worksheet)"
            else:
                return "2-Standard"
        else:
            if '3' in str(self._ihg_values):
                return "3-PHPP calculation ('IHG' worksheet)"
            else:
                return "2-Standard"

    @property
    def cert_standard(self):
        if '2' in str(self._cert_standard):
            return "2-EnerPHit"
        elif '3' in str(self._cert_standard):
            return "3-PHI Low Energy Building"
        elif '4' in str(self._cert_standard):
            return "4-Other" 
        else:
            return "1-Passive House"  

    @property
    def cert_class(self):
        if '2' in str(self._cert_class):
            return "2-Plus"
        elif '3' in str(self._cert_class):
            return "3-Premium"
        else:
            return "1-Classic"

    @property
    def pe(self):
        if '2' in str(self._cert_pe):
            return "2-PER (renewable)"
        else:
            return "1-PE (non-renewable)"

    @property
    def enerPHit(self):
        if '2' in str(self._enerPHit):
            return "2-Energy demand method"
        else:
            return "1-Component method" 

    @property
    def retrofit(self):
        if '2' in str(self._retrofit):
            return "2-Retrofit"
        elif '3' in str(self._retrofit):
            return "3-Step-by-step retrofit"
        else:
            return "1-New building"

    def check_non_res(self, _ghenv):
        if 'Non' in self.building_type and '1' in self.occupancy_method:
            warning = "For Non-Residential buildings, please be sure to input\n"\
            "the occupancy for the building."
            _ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, warning)
        
        if 'Non' in self.building_type and '10' in self.ihg_type:
            warning = "For Non-Residential buildings, please select a valid\n"\
            "Utilization Pattern: '20-Office / Admin. buildin', '21-School', or '22-Other'"
            _ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, warning)
    
        if 'Non' not in self.building_type and self.occupancy:
            warning = "For Residential buildings, please leave the occupancy blank.\n"\
            "Occupancy will be determined by the PHPP automatically. Only input an occupancy if\n"\
            "you are certain and that the Certifier will allow it."
            _ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, warning)
    
    def to_dict(self):
        d = {}

        d.update( {'id':self.id } )
        d.update( {'num_res_units':self._num_res_units } )
        d.update( {'spec_capacity':self.spec_capacity } )
        d.update( {'bldg_name':self.bldg_name } )
        d.update( {'bldg_country':self.bldg_country } )
        d.update( {'building_type':self.building_type } )
        d.update( {'ihg_type':self.ihg_type } )
        d.update( {'ihg_values':self.ihg_values } )
        d.update( {'occupancy':self._occupancy } )
        d.update( {'cert_standard':self.cert_standard } )
        d.update( {'cert_class':self.cert_class } )
        d.update( {'pe':self.pe } )
        d.update( {'enerPHit':self.enerPHit } )        
        d.update( {'retrofit':self.retrofit } )        

        return d

    @classmethod
    def from_dict(cls, _dict):
        new_obj = cls()

        new_obj.id = _dict.get('id')
        new_obj._num_res_units = _dict.get('num_res_units')
        new_obj._spec_capacity = _dict.get('spec_capacity')
        new_obj.bldg_name = _dict.get('bldg_name')
        new_obj.bldg_country = _dict.get('bldg_country')
        new_obj._building_type = _dict.get('building_type')
        new_obj._ihg_type = _dict.get('ihg_type')
        new_obj._ihg_values = _dict.get('ihg_values')
        new_obj._occupancy = _dict.get('occupancy')
        new_obj._cert_standard = _dict.get('cert_standard')
        new_obj._cert_class = _dict.get('cert_class')
        new_obj._cert_pe = _dict.get('pe')
        new_obj._enerPHit = _dict.get('enerPHit')        
        new_obj._retrofit = _dict.get('retrofit')        

        return new_obj

    def __unicode__(self):
        return u'A PHPP Setup Object: < {} >'.format(self.id)
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
       return "{}(_numResUnits={!r}, _specCapacity={!r},"\
                "_bldgName={!r}, _bldgCountry={!r}, _bldgType={!r},"\
                "_ihgType={!r}, _ihgVals={!r}, _occupancy={!r},"\
                "_cert_stndard={!r}, _cert_class={!r}, _pe={!r}"\
                "_enerPHit={!r} _retrofit={!r})".format( self.__class__.__name__,
                self._num_res_units,
                self._spec_capacity,
                self.bldg_name,
                self.bldg_country,
                self._building_type,
                self._ihg_type,
                self._ihg_values,
                self._occupancy,
                self._cert_standard,
                self._cert_class,
                self._cert_pe,
                self._enerPHit,
                self._retrofit)