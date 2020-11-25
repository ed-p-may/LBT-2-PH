import math
from System import Object
import random
import Grasshopper.Kernel as ghK

class Occupancy(Object):

    def __init__(self, _num_uits=1, _occ=None, _tfa=None, 
        _typ="1-Residential building", _ighT="10-Dwelling", ighV="2-Standard"):
        self.id = random.randint(1000,9999)
        self._num_units = _num_uits
        self._tfa = _tfa
        self._occupancy = _occ
        self._building_type = _typ
        self._ihg_type = _ighT
        self._ihg_values = ighV

    @property
    def occupancy(self):
        if self._occupancy:
            return self._occupancy
        else:
            return self.calc_occupancy()

    @occupancy.setter
    def occupancy(self, _in):
        if _in:
            self._occupancy = _in

    @property
    def num_units(self):
        return self._num_units

    @num_units.setter
    def num_units(self, _in):
        if _in:
            self._num_units = _in

    @property
    def tfa(self):
        return self._tfa

    @tfa.setter
    def tfa(self, _in):
        if _in:
            self._tfa = _in

    @property
    def building_type(self):
        return self._building_type
    
    @building_type.setter
    def building_type(self, _in):
        if not _in: return

        if '2' in str(_in):
            self._building_type = "2-Non-residential building"
        else:
            self._building_type = "1-Residential building"

    @property
    def ihg_type(self):
        return self._ihg_type
    
    @ihg_type.setter
    def ihg_type(self, _in):
        if not _in: return

        if '11' in str(_in):
            self._ihg_type = "11-Nursing home / students"
        elif '12' in str(_in):
            self._ihg_type = "12-Other"
        elif '20' in str(_in):
            self._ihg_type = "20-Office / Admin. building"
        elif '21' in str(_in):
            self._ihg_type = "21-School"
        elif '22' in str(_in):
            self._ihg_type = "22-Other"
        else:
            self._ihg_type = "10-Dwelling"
    
    @property
    def ihg_values(self):
        return self._ihg_values
    
    @ihg_values.setter
    def ihg_values(self, _in):
        if not _in: return
        
        if 'Non' in self.building_type:
            if '4' in str(_in):
                self._ihg_values = "4-PHPP calculation ('IHG non-res' worksheet)"
            else:
                self._ihg_values = "2-Standard"
        else:
            if '3' in str(_in):
                self._ihg_values = "3-PHPP calculation ('IHG' worksheet)"
            else:
                self._ihg_values = "2-Standard"

    @property
    def occupancy_method(self):
        if '2' in self.building_type:
            return '2-User determined' 
        else:
            return '1-Standard (only for residential buildings)'

    def calc_occupancy(self):
        """This formula is from the PHPP v9.6a SI"""
 
        _a = 1 - math.exp(-0.00013 * math.pow((self.tfa/self.num_units-7), 2))
        occ = (1 + 1.9 * _a + 0.001 * self.tfa/self.num_units ) * self.num_units

        return occ

    def check_non_res(self, _ghenv):
        if 'Non' in self.building_type and not self._occupancy:
            warning = "For Non-Residential buildings, please be sure to input\n"\
            "the occupancy for the building."
            _ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, warning)
        
        if 'Non' in self.building_type and '10' in self.ihg_type:
            warning = "For Non-Residential buildings, please select a valid\n"\
            "ihgType_ Enter either: '20-Office / Admin. buildin', '21-School', or '22-Other'"
            _ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, warning)
    
        if 'Non' not in self.building_type and self._occupancy:
            warning = "For Residential buildings, please leave the occupancy blank.\n"\
            "Occupancy will be determined by the PHPP automatically. Only input an occupancy if\n"\
            "you are certain and that the Certifier will allow it."
            _ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, warning)
        
    def to_dict(self):
        d = {}

        d.update( {'id':self.id} )
        d.update( {'num_units':self.num_units} )
        d.update( {'tfa':self.tfa} )
        d.update( {'occupancy':self.occupancy} )
        d.update( {'building_type':self.building_type} )
        d.update( {'ihg_type':self.ihg_type} )
        d.update( {'ihg_values':self.ihg_values} )

        return d

    @classmethod
    def from_dict(cls, _dict):
        new_obj = cls()
        
        new_obj.id = _dict.get('id')
        new_obj._num_units = _dict.get('num_units')
        new_obj._tfa = _dict.get('tfa')
        new_obj._occupancy = _dict.get('occupancy')
        new_obj._building_type = _dict.get('building_type')
        new_obj._ihg_type = _dict.get('ihg_type')
        new_obj._ihg_values = _dict.get('ihg_values')

        return new_obj

    def __unicode__(self):
        return u'A PHPP Occupancy Object: < {} >'.format(self.id)
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
       return "{}(_num_uits={!r}, _occ={!r}, _tfa={!r},"\
                "_typ={!r}, _ighT={!r}, ighV={!r} )".format(
               self.__class__.__name__, self.num_units, self.occupancy,
               self.tfa, self.building_type, self.ihg_type, self.ihg_values )
