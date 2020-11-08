from random import randint
import rhinoscriptsyntax as rs
import ghpythonlib.components as ghc
import Grasshopper.Kernel as ghK
import re
import random
import scriptcontext as sc

import LBT2PH
import LBT2PH.helpers


class PHPP_Sys_Duct:
    def __init__(self, _duct_input=[], _wMM=[], _iThckMM=[], _iLambda=[], _ghdoc=[]):
        """
        Args:
            _duct_input (List<float | Curve>): The individual duct segments for a single 'leg' of the ERV. ERV will have two 'legs' total. Input can be either number or a Curve
            _wMM (List<float>): The duct segment widths (for round ducts) value is the diameter in MM
            _iThckMM (List<float>): The duct segment insualtion thicknesses in MM 
            _iLambda (List<float>): The duct segment insualtion lambda valies in W/mk
            _ghdoc: The "ghdoc" object from the Grasshopper scene
        """
        
        self.duct_id = random.randint(1000,9999)
        self.Warnings = []
        self._ghdoc = _ghdoc
        self._duct_input = _duct_input
        self._duct_length = None
        self._duct_width = None
        self._insulation_thickness = None
        self._insulation_lambda = None

        self._set_params_from_defaults()
        self._set_params_from_rhino_obj( _duct_input )
        self._set_params_from_user_input( _duct_input, _wMM, _iThckMM, _iLambda )

    def _set_params_from_defaults(self):
        self._duct_length = [5]
        self._duct_width = [104]
        self._insulation_thickness = [52]
        self._insulation_lambda = [0.04]

    def _set_params_from_rhino_obj(self, _duct_input):
        if not self._ghdoc:
            return None

        if not self._duct_input:
            return None

        rhino_guids = []
        with LBT2PH.helpers.context_rh_doc(self._ghdoc):
            for input in _duct_input:
                try:
                    rs.coercecurve( input )
                    rhino_guids.append( input )
                except:
                    pass
        
        if rhino_guids:
            le, wd, tk, la = self._calculate_segment_params( rhino_guids )
            
            self._duct_length = [le]
            self._duct_width = [wd]
            self._insulation_thickness = [tk]
            self._insulation_lambda = [la]

    def _calculate_segment_params(self, _rhino_curves):
        # Combine duct segments with different param into a single 'leg', find the length-weighted avg values
        l, w, t, c = self._get_param_values_from_rhino(_rhino_curves)
        
        totalLen = sum(l) if sum(l) != 0 else 1
        len_weighted_width = (sum([(len*width) for (len, width) in zip(l, w)])) / totalLen
        len_weighted_insul_thickness =(sum([(len*thck) for (len, thck) in zip(l, t)])) / totalLen
        len_weighted_insul_lambda =(sum([(len*cond) for (len, cond) in zip(l, c)])) / totalLen

        return (totalLen, len_weighted_width, len_weighted_insul_thickness, len_weighted_insul_lambda)

    def _get_param_values_from_rhino(self, _rhino_objects):
        """ Looks at Rhino scene to try get Param values from UserText """
        if not self._ghdoc:
            return

        l, w, t, c = [], [], [], []
        
        with LBT2PH.helpers.context_rh_doc(self._ghdoc):
            for rhino_obj in _rhino_objects:
                try:
                    l.append( float(ghc.Length(rhino_obj)) )
                    w.append( float( self.get_UserText_with_default(rhino_obj, 'ductWidth', self._duct_width) ))
                    t.append( float( self.get_UserText_with_default(rhino_obj, 'insulThickness', self._insulation_thickness) ))
                    c.append( float( self.get_UserText_with_default(rhino_obj, 'insulConductivity', self._insulation_lambda) ))
                except:
                    self.Warnings.append('No param values found in Rhino. Using GH values or defaults.')
        
        return l, w, t, c

    @staticmethod
    def get_UserText_with_default(_obj, _key, _default=None):
        """ Why doesn't rs.GetUserText() do this by Default already? Sheesh...."""
        result = rs.GetUserText(_obj, _key)
        if result:
            return result
        else:
            return _default

    def _set_params_from_user_input(self, _duct_input, _wMM, _iThckMM, _iLambda):
        def constant_len_list(_input_list, _target_len):
            if not _input_list:
                return None

            if len(_input_list) == _target_len:
                return _input_list
            else:
                return [ _input_list[0] ]*_target_len

        if not _duct_input:
            return None

        # Clean up the inputs, make all the same length
        input_widths = constant_len_list(_wMM, len(_duct_input))
        input_thicknesses = constant_len_list(_iThckMM, len(_duct_input))
        input_lambdas = constant_len_list(_iLambda, len(_duct_input))

        # Get the length values
        input_lengths = []
        if _duct_input:
            for input in _duct_input:
                try:
                    input_lengths.append( float(input) )
                except:
                    pass
        
        if input_lengths:
            self._duct_length = [ sum(input_lengths) ]
        else:
            input_lengths = self._duct_length

        # Calc all the length-weighted total values
        if input_widths:
            length_weighted_width = sum([l*w for l, w in zip(input_lengths, input_widths)])/sum(input_lengths)
            self._duct_width = [length_weighted_width]
        if input_thicknesses:
            length_weighted_thickness = sum([l*t for l, t in zip(input_lengths, input_thicknesses)])/sum(input_lengths)
            self._insulation_thickness = [length_weighted_thickness]
        if input_lambdas:
            length_weighted_lambda = sum([l*k for l, k in zip(input_lengths, input_lambdas)])/sum(input_lengths)
            self._insulation_lambda = [length_weighted_lambda]

    def to_dict(self):
        d = {}
        d.update( { 'duct_id':self.duct_id} )
        d.update( { 'duct_input':self._duct_input } )
        d.update( { 'duct_length':self._duct_length } )
        d.update( { 'duct_width':self._duct_width } )
        d.update( { 'insulation_thickness':self._insulation_thickness } )
        d.update( { 'insulation_lambda':self._insulation_lambda } )
        
        return d
    
    @classmethod
    def from_dict(cls, _dict):
        new_duct = cls()
        new_duct.duct_id = _dict['duct_id']
        new_duct.Warnings = []
        new_duct._ghdoc = None
        new_duct._duct_length = _dict['duct_length']
        new_duct._duct_input = _dict['duct_input']
        new_duct._duct_width = _dict['duct_width']
        new_duct._insulation_thickness = _dict['insulation_thickness']
        new_duct._insulation_lambda = _dict['insulation_lambda']
        
        return new_duct

    def __unicode__(self):
        return u'PHPP Ventilation Duct Object'
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
        return "{}( _lenM={!r}, _wMM={!r}, _iThckMM={!r}, _iLambda={!r}, _ghdoc={!r})".format(
                self.__class__.__name__,
                self._duct_input,        
                self._duct_width,
                self._insulation_thickness,
                self._insulation_lambda,
                self._ghdoc)


class PHPP_Sys_VentUnit:
    def __init__(self, _nm='97ud-Default HRV unit', _hr=0.75, _mr=0, _elec=0.45, _frsotT=-5, _ext=False):
        self.id = random.randint(1000,9999)
        self.name = _nm
        self.HR_eff = float(_hr)
        self.MR_eff = float(_mr)
        self.elec_eff = float(_elec)
        self.frost_temp = _frsotT
        self.exterior = 'x' if _ext==True else ''
    
    def to_dict(self):
        d = {}
        d.update( {'id':self.id} )
        d.update( {'name':self.name } )
        d.update( {'HR_eff':self.HR_eff } )
        d.update( {'MR_eff':self.MR_eff } )
        d.update( {'elec_eff':self.elec_eff } )
        d.update( {'frost_temp':self.frost_temp } )
        d.update( {'exterior':self.exterior } )

        return d
   
    @classmethod
    def from_dict(cls, _dict):
        id = _dict['id']
        name = _dict['name']
        hr = _dict['HR_eff']
        mr = _dict['MR_eff']
        elec = _dict['elec_eff']
        frost_temp = _dict['frost_temp']
        ext = _dict['exterior']
        
        new_vent_unit = cls(name, hr, mr, elec, frost_temp, ext)
        new_vent_unit.id = id

        return new_vent_unit

    def __unicode__(self):
        return u'PHPP Ventilation Unit (ERV/HRV) Object: <{self.name}>'.format(self=self)
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
        return "{}( _nm={!r}, _hr={!r}, _mr={!r}, _elec={!r}, _frsot={!r}, _ext={!r}".format(
                self.__class__.__name__,
                self.name,        
                self.HR_eff,
                self.MR_eff,
                self.elec_eff,
                self.frost_temp,
                self.exterior)


class PHPP_Sys_ExhaustVent:
    def __init__(self, nm='Default_Exhaust_Vent',
                airFlowRate_On=450,
                airFlowRate_Off=25,
                hrsPerDay_On=0.5,
                daysPerWeek_On=7,
                default_duct=PHPP_Sys_Duct()):
        
        self.id = random.randint(1000,9999)
        self.name = nm
        self.vent_floor_area = 10
        self.vent_area_height = 2.5
        
        self.flow_rate_on = self._evaluateInputUnits(airFlowRate_On)
        self.flow_rate_off = self._evaluateInputUnits(airFlowRate_Off)
        self.hours_per_day_on = hrsPerDay_On
        self.days_per_week_on = daysPerWeek_On
        self.holidays = 0
        
        self.duct_01 = default_duct
        self.duct_02 = default_duct
        
    def _evaluateInputUnits(self, _in):
        """If values are passed including a 'cfm' string, will
        set the return value to the m3/h equivalent"""
        
        if _in is None: return None

        outputVal = 0
        
        try:
            outputVal = float(_in)
        except:
            # Pull out just the decimal characters
            inputVal = _in.replace(' ', '')
            for each in re.split(r'[^\d\.]', inputVal):
                if len(each)>0:
                    outputVal = each
            
            # Convert to m3/h if necessary
            if 'cfm' in inputVal:
                outputVal = float(outputVal) * 1.699010796 #cfm--->m3/h
        
        return float(outputVal)
    
    def to_dict(self):
        d = {}
        d.update( {'id':self.id} )
        d.update( {'name':self.name } )
        d.update( { 'vent_floor_area':self.vent_floor_area } )
        d.update( { 'vent_area_height':self.vent_area_height } )
        d.update( { 'flow_rate_on':self.flow_rate_on } )
        d.update( { 'flow_rate_off':self.flow_rate_off } )
        d.update( { 'hours_per_day_on':self.hours_per_day_on } )
        d.update( { 'days_per_week_on':self.days_per_week_on } )
        d.update( { 'holidays':self.holidays } )
        d.update( { 'duct_01':self.duct_01.to_dict() } )
        d.update( { 'duct_02':self.duct_02.to_dict() } )
        
        return d
    
    @classmethod
    def from_dict(cls, _dict):
        nm = _dict['name']
        airFlowRate_On = _dict['flow_rate_on']
        airFlowRate_Off =_dict['flow_rate_off']
        hrsPerDay_On = _dict['hours_per_day_on']
        daysPerWeek_On =_dict['days_per_week_on']
        default_duct = _dict['duct_01']

        new_exhaust_obj = cls(nm, airFlowRate_On, airFlowRate_Off, hrsPerDay_On, daysPerWeek_On, default_duct)
        new_exhaust_obj.id = _dict['id']
        new_exhaust_obj.duct_01 = PHPP_Sys_Duct.from_dict(_dict['duct_01'])
        new_exhaust_obj.duct_02 = PHPP_Sys_Duct.from_dict(_dict['duct_02'])
        new_exhaust_obj.holidays = _dict['holidays']

        return new_exhaust_obj

    def __str__(self):
        return unicode(self).encode('utf-8')
    def __unicode__(self):
        return u'A PHPP Exhaust-Air Object: < {self.name} >'.format(self=self)
    def __repr__(self):
       return "{}( nm={!r}, airFlowRate_On={!r}, airFlowRate_Off={!r},"\
               "hrsPerDay_On={!r},daysPerWeek_On={!r},"\
               "default_duct={!r} )".format(
               self.__class__.__name__,
               self.name,
               self.flow_rate_on,
               self.flow_rate_off,
               self.hours_per_day_on,
               self.days_per_week_on,
               self.duct_01)


class PHPP_Sys_Ventilation:
    def __init__(self,
                _ghenv=None,
                _system_id=random.randint(1000,9999),
                _system_type='1-Balanced PH ventilation with HR',
                _systemName='Vent-1',
                _unit=PHPP_Sys_VentUnit(),
                _d01=PHPP_Sys_Duct(),
                _d02=PHPP_Sys_Duct(),
                _exhaustObjs=[ PHPP_Sys_ExhaustVent() ]):
        
        self.ghenv = _ghenv
        self.system_id = _system_id
        self.system_type = _system_type
        self.system_name = _systemName
        self.vent_unit = _unit
        self.duct_01 = _d01
        self.duct_02 = _d02
        self.exhaust_vent_objs = _exhaustObjs
        
        self.setVentSystemType(_ghenv)
    
    def __eq__(self, other):
        return self.id == other.id
    
    def __hash__(self):
        return hash(str(self.system_id))
    
    def setVentSystemType(self, _ghenv):
        if '1' in self.system_type:
            self.system_type = '1-Balanced PH ventilation with HR'
        elif '2' in self.system_type:
            self.system_type = '2-Extract air unit'
        elif '3' in self.system_type:
            self.system_type = '3-Only window ventilation'
        else:
            warning = 'Error setting Ventilation System Type? Input only Type 1, 2, or 3. Setting to Type 1 (HRV) as default'
            try:
                _ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, warning)
            except:
                pass
            self.system_type = '1-Balanced PH ventilation with HR'
    
    def to_dict(self):
        d = {}
        d.update( {'system_id':self.system_id} )
        d.update( {'system_type':self.system_type} )
        d.update( {'system_name':self.system_name} )
        d.update( {'vent_unit':self.vent_unit.to_dict()} )
        d.update( {'duct_01': self.duct_01.to_dict()} )
        d.update( {'duct_02': self.duct_02.to_dict()} )
        d.update( {'exhaust_vent_objs': [exhaust_obj.to_dict() for exhaust_obj in self.exhaust_vent_objs] } )

        return d

    @classmethod
    def from_dict(cls, _dict, _ghenv=None):

        system_id = _dict['system_id']
        system_type = _dict['system_type']
        system_name = _dict['system_name']
        unit = PHPP_Sys_VentUnit.from_dict(_dict['vent_unit'] )
        duct_01 = PHPP_Sys_Duct.from_dict( _dict['duct_01'] )
        duct_02 = PHPP_Sys_Duct.from_dict( _dict['duct_02'] )
        exhaust_systems = []
        for exhaust_system_dict in _dict['exhaust_vent_objs']:
            exhaust_systems.append( PHPP_Sys_ExhaustVent.from_dict(exhaust_system_dict) )

        new_vent_system = cls(_ghenv, system_id, system_type, system_name, unit, duct_01, duct_02, exhaust_systems)
        
        return new_vent_system

    def __str__(self):
        return unicode(self).encode('utf-8')
    def __unicode__(self):
        return u'A PHPP Ventilation System Object: <{self.system_name}>'.format(self=self)
    def __repr__(self):
        return "{}( _ghenv=None, _systemType={!r}, _systemName={!r}, "\
                "_unit={!r}, _d01={!r},"\
                "_d02={!r}, _exhaustObjs={!r})".format(
                self.__class__.__name__,
                self.system_type,
                self.system_name,
                self.vent_unit,
                self.duct_01,
                self.duct_02,
                self.exhaust_vent_objs)

