import random
from System import Object

class PHPP_Verification(Object):
    def __init__(self, _specCapacity=60, _bldgName=None,
                _bldgCountry='US-United States of America', 
                _cert_stndard='1-Passive House', _cert_class="1-Classic", 
                _pe="1-PE (non-renewable)",
                _enerPHit="2-Energy demand method", _retrofit="1-New building"):
        self.id = random.randint(1000,9999)
        self._spec_capacity = _specCapacity
        self.bldg_name = _bldgName
        self.bldg_country = _bldgCountry

        self._cert_standard = _cert_stndard
        self._cert_class = _cert_class
        self._cert_pe = _pe
        self._enerPHit = _enerPHit
        self._retrofit = _retrofit

    @property
    def spec_capacity(self):
        try:
            return float(self._spec_capacity)
        except Exception as e:
            print(e)
            return 60

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

    @cert_standard.setter
    def cert_standard(self, _in):
        if _in:
            self._cert_standard = str(_in)

    @property
    def cert_class(self):
        if '2' in str(self._cert_class):
            return "2-Plus"
        elif '3' in str(self._cert_class):
            return "3-Premium"
        else:
            return "1-Classic"

    @cert_class.setter
    def cert_class(self, _in):
        if _in:
            self._cert_class = str(_in)

    @property
    def pe(self):
        if '2' in str(self._cert_pe):
            return "2-PER (renewable)"
        else:
            return "1-PE (non-renewable)"

    @pe.setter
    def pe(self, _in):
        if _in:
            self._cert_pe = str(_in)

    @property
    def enerPHit(self):
        if '2' in str(self._enerPHit):
            return "2-Energy demand method"
        else:
            return "1-Component method" 

    @enerPHit.setter
    def enerPHit(self, _in):
        if _in:
            self._enerPHit = str(_in)

    @property
    def retrofit(self):
        if '2' in str(self._retrofit):
            return "2-Retrofit"
        elif '3' in str(self._retrofit):
            return "3-Step-by-step retrofit"
        else:
            return "1-New building"

    @retrofit.setter
    def retrofit(self, _in):
        if _in:
            self._retrofit = str(_in)

    def to_dict(self):
        d = {}

        d.update( {'id':self.id } )
        d.update( {'spec_capacity':self.spec_capacity } )
        d.update( {'bldg_name':self.bldg_name } )
        d.update( {'bldg_country':self.bldg_country } )
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
        new_obj._spec_capacity = _dict.get('spec_capacity')
        new_obj.bldg_name = _dict.get('bldg_name')
        new_obj.bldg_country = _dict.get('bldg_country')
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
       return "{}( _specCapacity={!r}, _bldgName={!r}, _bldgCountry={!r},"\
                "_cert_stndard={!r}, _cert_class={!r}, _pe={!r}"\
                "_enerPHit={!r} _retrofit={!r})".format( self.__class__.__name__,
                self._spec_capacity,
                self.bldg_name,
                self.bldg_country,
                self._cert_standard,
                self._cert_class,
                self._cert_pe,
                self._enerPHit,
                self._retrofit)