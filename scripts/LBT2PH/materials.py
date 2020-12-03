class PHPP_Material_Opaque:
    def __init__(self, _hb_mat):
        self.hb_mat = _hb_mat
        self._t = getattr(self.hb_mat, 'thickness', 1)
        self._hb_k = getattr(self.hb_mat, 'conductivity', None)
        self._hb_r = getattr(self.hb_mat, 'resistivity', None)
        self._hb_U = getattr(self.hb_mat, 'u_value', None)
        self._hb_R = getattr(self.hb_mat, 'r_value', None)

    @property
    def identifier(self):
        return self.hb_mat.identifier

    @property
    def hb_display_name(self):
        return self.hb_mat.display_name

    @property
    def phpp_name(self):
        nm = self.hb_mat.display_name
        nm = nm.replace('PHPP_MAT_', '')
        nm = nm.replace(' ', '_')
        nm = nm.replace('__Int__', '')

        return nm

    @property
    def LayerThickness(self):
        if self._t:
            return self._t
        else:
            print('EP Material does not have a thickness, using default 1.0 m')
            return 1
    
    @property
    def LayerConductivity(self):
        if self._hb_k:
            return self._hb_k
        elif self._hb_r:
            return 1/self._hb_r
        elif self._t and self._hb_U:
            return float(self._hb_U) / float(self._t) 
        elif self._t and self._hb_R:
            return 1/float(self._hb_R) / float(self._t) 
        else:
            print('Cannot determine the layer conductivity for some reason?')
            return None

    @property
    def LayerConductance(self):
        if self._hb_U:
            return self._hb_U
        elif self.hb_R:
            return 1/self._hb_R
        elif self._t and self._hb_k:
            return float(self._hb_k) * float(self._t)
        elif self._t and self._hb_r:
            return 1/float(self._hb_r) * float(self._t)
        else:
            print('Cannot determine the layer conductance for some reason?')
            return None

    def __unicode__(self):
        return u'A PHPP-Style Material Object: < {} >'.format(self.phpp_name)
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
       return "{}(_hb_mat={!r})".format(self.__class__.__name__, self.hb_mat)

class PHPP_Material_Window_EP:
    def __init__(self, _mat, _ud_num):
        self._EP_Mat = _mat
        self._ud_num = _ud_num
    
    @property
    def name(self):
        return self._EP_Mat.display_name

    @property
    def uValue(self):
        try:
            return float(self._EP_Mat.u_value)
        except:
            return None

    @property
    def VT(self):
        return self._EP_Mat.vt

    @property
    def gValue(self):
        return self._EP_Mat.shgc

    def __unicode__(self):
        return u'A PHPP-Style Window Material Object: < {} >'.format(self.name)
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
       return "{}(_mat={!r})".format(self.__class__.__name__, self._EP_Mat)
