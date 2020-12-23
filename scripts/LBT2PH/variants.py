from System import Object
import Grasshopper.Kernel as ghK
from collections import namedtuple

class Variants(Object):

    def __init__(self, _ghenv=None):
        self.ghenv = _ghenv
        self.windows = False
        self.u_values = False
        self.airtightness = False
        self.thermal_bridges = False
        self.certification = False
        self.primary_energy = False
        self.default_ventilation = False
        self.custom_ventlilation = False

    @property
    def ventilation(self):
        pass
    
    @ventilation.setter
    def ventilation(self, _in):
        if len(_in)==1:
            self.default_ventilation = bool(_in[0])
            self.custom_ventlilation = False
        else:
            self.default_ventilation = False
            self.custom_ventlilation = _in[0:5]
        
        if len(_in) not in [0, 1, 5]:
            self.default_ventilation = False
            self.custom_ventlilation = False
            msg = "Error: I don't understand the ventialtion_? Please either input TRUE to use the defaults\n"\
                "or input a multiline line string (panel) with the 5 excel formulas to you'd like to write?\n"\
                "Because sometimes the 'Additional Vent' worksheet might get enlarged by a user (if you\n"\
                "have more than the standard number of rooms) you need to tell this component exactly where each\n"\
                "'Section' starts in that worksheet. If you have not changed / edited that worksheet at all, just\n"\
                "use the default values (set 'ventaltion_' input to True).\n"\
                "But for custom PHPPs, the multine string format should look like:\n"\
                "------------\n"\
                "   Additional Vent!F{Your Row Number}=Variants!D856\n"\
                "   Additional Vent!H{Your Row Number}=Variants!D858\n"\
                "   Additional Vent!H{Your Row Number}=Variants!D858\n"\
                "   Additional Vent!L{Your Row Number}=Variants!D857\n"\
                "   Additional Vent!L{Your Row Number}=Variants!D857\n"
            self.ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, msg)

    @property
    def use_default_locations(self):
        if self.ventilation[0] and len(self.ventilation)==1:
            return True
        else:
            return False
    
    def get_custom_rows(self):
        output = []
        Item = namedtuple('Item', ['worksheet', 'range', 'reference'])
        
        for item in self.custom_ventlilation:
            item = item.replace('{', '')
            item = item.replace('}','')
            item = item.rstrip()
            item = item.lstrip()
            first, reference = item.split('=')
            wrksht, rng = first.split('!')
            output.append( Item(wrksht, rng, '='+reference) )
        
        return output

    def __unicode__(self):
        return u'A PHPP-Vaiants configuration object'
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
       return "{}()".format(
            self.__class__.__name__)
    def ToString(self):
        return str(self)