from System import Object
import random

class PHPP_SummVent(Object):
    def __init__(self, _day_ach=None, _night_ach=None):
        self.id = random.randint(1000,9999)
        self._day_ach = _day_ach
        self._night_ach = _night_ach

    @property
    def day_ach(self):
        return self._day_ach

    @day_ach.setter
    def day_ach(self, _in):
        self._day_ach = _in
    
    @property
    def night_ach(self):
        return self._night_ach

    @night_ach.setter
    def night_ach(self, _in):
        self._night_ach = _in
    
    def to_dict(self):
        d =  {}

        d.update( {'id':self.id} )
        d.update( {'day_ach':self.day_ach} )
        d.update( {'night_ach':self.night_ach} )

        return d

    @classmethod
    def from_dict(cls, _dict):
        new_obj = cls()
        
        new_obj.id = _dict.get('id')
        new_obj.day_ach = _dict.get('day_ach')
        new_obj.night_ach = _dict.get('night_ach')

        return new_obj
    
    def __unicode__(self):
        return u"A PHPP Summer Ventilation Object < {} >".format(self.id)
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
       return "{}( _day_ach={!r}, _night_ach={!r}".format(
               self.__class__.__name__,
               self._day_ach,
               self._night_ach)