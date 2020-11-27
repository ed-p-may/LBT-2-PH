from random import randint
import rhinoscriptsyntax as rs
import ghpythonlib.components as ghc
import Grasshopper.Kernel as ghK
import re
import random
import scriptcontext as sc
from System import Object
from collections import namedtuple

from honeybee_energy.schedule.ruleset import ScheduleRuleset
from honeybee_energy.lib.schedules import schedule_by_identifier
from ladybug.dt import Date

import LBT2PH
import LBT2PH.helpers


class PHPP_Sys_Duct(Object):
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

    @property
    def duct_length(self):
        try:
            return float(self._duct_length[0])
        except Exception as e:
            print(e, self._duct_length)
            return 5.0

    @property
    def duct_width(self):
        try:
            return float(self._duct_width[0])
        except Exception as e:
            print(e, self._duct_width)
            return 104
    
    @property
    def insulation_thickness(self):
        try:
            return float(self._insulation_thickness[0])
        except Exception as e:
            print(e, self._insulation_thickness)
            return 52

    @property
    def insulation_lambda(self):
        try:
            return float(self._insulation_lambda[0])
        except Exception as e:
            print(e, self._insulation_lambda)
            return 0.04

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


class PHPP_Sys_VentUnit(Object):
    def __init__(self, _nm='97ud-Default HRV unit', _hr=0.75, _mr=0, _elec=0.45, _frsotT=-5, _ext=False):
        self.id = random.randint(1000,9999)
        self._name = _nm
        self._HR_eff = _hr
        self._MR_eff = _mr
        self._elec_eff = _elec
        self._frost_temp = _frsotT
        self._exterior = _ext
    
    @property
    def name(self):
        try:
            return str(self._name)
        except:
            return 'Default Name'

    @name.setter
    def name(self, _in):
        try:
            self._name = str(_in)
        except Exception as e:
            print(e)
            pass

    @property
    def HR_eff(self):
        try:
            return float(self._HR_eff)
        except:
            return 0.75

    @HR_eff.setter
    def HR_eff(self, _in):
        try:
            self._HR_eff = float(_in)
        except Exception as e:
            print(e)
            pass

    @property
    def MR_eff(self):
        try:
            return float(self._MR_eff)
        except:
            return 0.0

    @MR_eff.setter
    def MR_eff(self, _in):
        try:
            self._MR_eff = float(_in)
        except Exception as e:
            print(e)
            pass

    @property
    def elec_eff(self):
        try:
            return float(self._elec_eff)
        except:
            return 0.45

    @MR_eff.setter
    def elec_eff(self, _in):
        try:
            self._elec_eff = float(_in)
        except Exception as e:
            print(e)
            pass
    
    @property
    def frost_temp(self):
        try:
            return float(self._frost_temp)
        except:
            return -5

    @frost_temp.setter
    def frost_temp(self, _in):
        try:
            self._frost_temp = float(_in)
        except Exception as e:
            print(e)
            pass

    @property
    def exterior(self):
        try:
            return 'x' if self._exterior else ''
        except:
            return ''

    @exterior.setter
    def exterior(self, _in):
        try:
            self._exterior = 'x' if _in else ''
        except Exception as e:
            print(e)
            pass

    def to_dict(self):
        d = {}
        d.update( {'id':self.id} )
        d.update( {'_name':self.name } )
        d.update( {'_HR_eff':self.HR_eff } )
        d.update( {'_MR_eff':self.MR_eff } )
        d.update( {'_elec_eff':self.elec_eff } )
        d.update( {'_frost_temp':self.frost_temp } )
        d.update( {'_exterior':self.exterior } )

        return d
   
    @classmethod
    def from_dict(cls, _dict):
        id = _dict['id']
        name = _dict['_name']
        hr = _dict['_HR_eff']
        mr = _dict['_MR_eff']
        elec = _dict['_elec_eff']
        frost_temp = _dict['_frost_temp']
        ext = _dict['_exterior']
        
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


class PHPP_Sys_ExhaustVent(Object):
    def __init__(self, nm='Default_Exhaust_Vent',
                airFlowRate_On=450,
                airFlowRate_Off=25,
                hrsPerDay_On=0.5,
                daysPerWeek_On=7,
                default_duct=PHPP_Sys_Duct()):
        
        self.id = random.randint(1000,9999)
        self._name = nm
        self.vent_floor_area = 10
        self.vent_area_height = 2.5
        self._phpp_ud_name = None
        
        self.flow_rate_on = self._evaluateInputUnits(airFlowRate_On)
        self.flow_rate_off = self._evaluateInputUnits(airFlowRate_Off)
        self.hours_per_day_on = hrsPerDay_On
        self.days_per_week_on = daysPerWeek_On
        self.holidays = 0
        
        self.duct_01 = default_duct
        self.duct_02 = default_duct
        
    @property
    def name(self):
        try:
            return str(self._name)
        except:
            return 'Exhaust_Unit'

    @name.setter
    def name(self, _in):
        self._name = str(_in)

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
       
    @property
    def phpp_ud_name(self):
        try:
            return str(self._phpp_ud_name)
        except Exception as e:
            print(e)
            return None

    @phpp_ud_name.setter
    def phpp_ud_name(self, _in):
        try:
            self._phpp_ud_name = str(_in)
        except Exception as e:
            print(e)
            pass

    def to_dict(self):
        d = {}
        
        d.update( { 'id':self.id} )
        d.update( { '_name':self.name } )
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
        nm = _dict['_name']
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


class PHPP_Sys_VentSchedule(Object):
    def __init__(self, s_h=1.0, t_h=1.0, s_m=0.77, t_m=0.0, s_l=0.4, t_l=0.0):
        self.id = random.randint(1000,9999)
        self._speed_high = s_h
        self._time_high = t_h
        self._speed_med = s_m
        self._time_med = t_m
        self._speed_low = s_l
        self._time_low = t_l

    def to_dict(self):
        d = {}
        d.update( {'id':self.id} )
        d.update( {'_speed_high':self._speed_high} )
        d.update( {'_time_high':self._time_high} )
        d.update( {'_speed_med':self._speed_med} )
        d.update( {'_time_med':self._time_med} )
        d.update( {'_speed_low':self._speed_low} )
        d.update( {'_time_low':self._time_low} )

        return d

    @classmethod
    def from_dict(cls, _dict):
        new_sched = cls()
        new_sched.id = _dict['id']
        new_sched._speed_high = _dict['_speed_high']
        new_sched._time_high = _dict['_time_high']
        new_sched._speed_med = _dict['_speed_med']
        new_sched._time_med = _dict['_time_med']
        new_sched._speed_low = _dict['_speed_low']
        new_sched._time_low = _dict['_time_low']

        return new_sched

    def __str__(self):
        return unicode(self).encode('utf-8')
    def __unicode__(self):
        return u'A PHPP Ventilation Schedule Object: <{self.id}>'.format(self=self)
    def __repr__(self):
        return "{}( s_h={!r}, t_h={!r}, s_m={!r}, t_m={!r}, s_l={!r}, t_l={!r})".format(
                self.__class__.__name__,
                self._speed_high,
                self._time_high,
                self._speed_med,
                self._time_med,
                self._speed_low,
                self._time_low)


class PHPP_Sys_Ventilation(Object):
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
        self._phpp_ud_name = None
        
        self.setVentSystemType(_ghenv)
    
    @property
    def phpp_ud_name(self):
        try:
            return str(self._phpp_ud_name)
        except Exception as e:
            print(e)
            return None

    @phpp_ud_name.setter
    def phpp_ud_name(self, _in):
        try:
            self._phpp_ud_name = str(_in)
        except Exception as e:
            print(e)
            pass

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


def calc_room_vent_rates_from_HB(_hb_room, _ghenv):
    ''' Uses the EP Loads and Schedules to calc the HB Room's annual flowrate '''

    # Guard
    #---------------------------------------------------------------------------
    if _hb_room.floor_area == 0:
        warning =   "Something wrong with the floor area - are you sure\n"\
                    "there is at least one 'Floor' surface making up the Room?"
        _ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, warning)
        return None


    # Pull the Loads from HB Room
    # ---------------------------------------------------------------------------
    vent_flow_per_area = _hb_room.properties.energy.ventilation.flow_per_area
    vent_flow_per_person = _hb_room.properties.energy.ventilation.flow_per_person
    vent_flow_per_zone = _hb_room.properties.energy.ventilation.flow_per_zone
    vent_flow_ach = _hb_room.properties.energy.ventilation.air_changes_per_hour
    people_per_area = _hb_room.properties.energy.people.people_per_area
    

    # Pull the Schedules from HB Room
    #---------------------------------------------------------------------------
    week_start_day = 'Sunday'
    holidays = None
    start_date, end_date, timestep = Date(1, 1), Date(12, 31), 1

    hb_sched_occ = _hb_room.properties.energy.people.occupancy_schedule
    hb_sched_vent = _hb_room.properties.energy.ventilation.schedule

    if hb_sched_occ:
        hb_sched_occ = schedule_by_identifier(hb_sched_occ.identifier)
        
        if isinstance(hb_sched_occ, ScheduleRuleset):
            data_occ = hb_sched_occ.data_collection(
                timestep, start_date, end_date, week_start_day, holidays, leap_year=False)
    else:
        data_occ = (1 for i in range(8760))

    if hb_sched_vent:
        hb_sched_vent = schedule_by_identifier(hb_sched_vent.identifier) 

        if isinstance(hb_sched_vent, ScheduleRuleset):
            data_vent = hb_sched_vent.data_collection(
                timestep, start_date, end_date, week_start_day, holidays, leap_year=False)
    else:
        data_vent = (1 for i in range(8760))

    #---------------------------------------------------------------------------
    # Nominal (peak) flow rates (m3/h) based on the HB/EP Load values
    # m3/s---> m3/h
    
    nom_vent_flow_per_area = vent_flow_per_area * _hb_room.floor_area * 60.0 * 60.0
    nom_vent_flow_per_zone = vent_flow_per_zone * 60.0 * 60.0
    nom_vent_flow_ach = vent_flow_ach * _hb_room.volume
    nom_vent_flow_per_person = people_per_area * _hb_room.floor_area * vent_flow_per_person * 60.0 * 60.0

    nom_vent_flow_total = nom_vent_flow_per_area + nom_vent_flow_per_person + nom_vent_flow_per_zone + nom_vent_flow_ach
    
    #---------------------------------------------------------------------------
    # Preview results
    print("The HB Room: '{}' has an average annual airflow of: {:.2f} "\
        "m3/h".format(_hb_room.display_name, nom_vent_flow_total) )
    print(">Looking at the Honeybee Program parameters:" )
    print("   *Note: These are the values BEFORE any occupany / activity schedule"\
        "is applied to reduce this (demand control)" )
    print("   *Note: These are the values takes into account the airflow for 'areas', for people, per zone and by ACH." )
    print("   Details:")
    print("      >Reference HB-Room Floor Area used is: {:.2f} m2".format(float(_hb_room.floor_area)) )
    print("      >Reference HB-Room Volume used is: {:.2f} m3".format(float(_hb_room.volume)) )
    print("      >[Ventilation Per Pers: {:.6f} m3/s-prs] x [Floor Area: {:.2f} m2] x [{:.3f} ppl/m2] "\
        "x 3600 s/hr = {:.2f} m3/hr".format(vent_flow_per_person, _hb_room.floor_area,
        people_per_area, nom_vent_flow_per_person) )
    print("      >[Ventilation Per Area: {:.6f} m3/s-m2] x [Floor Area: {:.2f} m2] "\
        "x 3600 s/hr = {:.2f} m3/hr".format(float(vent_flow_per_area),
        float(_hb_room.floor_area), float(nom_vent_flow_per_area)) )
    print("      >[Ventilation per Zone: {:.6f} m3/s] x 3600 s/hr = "\
        "{:.2f} m3/h".format(vent_flow_per_zone, nom_vent_flow_per_zone, ) )
    print("      >[Ventilation by ACH: {:.2f} ACH] x [Volume: {:.2f} m3]"\
        " = {:.2f} m3/h ".format(vent_flow_ach, _hb_room.volume, nom_vent_flow_ach) )
    print("      >[Vent For Area: {:.2f} m3/h] + [Vent For PPL: {:.2f} m3/h]"\
        " + [Vent For Zone: {:.2f} m3/h] + [Vent For ACH: {:.2f} m3/h]"\
        " = {:.2f} m3/h".format(nom_vent_flow_per_area, vent_flow_per_person, 
        nom_vent_flow_per_zone, nom_vent_flow_ach, nom_vent_flow_total) )
    print('- '*100)
    

    # Annual Average flow rates taking schedules into account
    #---------------------------------------------------------------------------
    total_nom_vent_flow = nom_vent_flow_per_area + nom_vent_flow_per_zone + nom_vent_flow_ach
    annual_vent_flow_space = sum( total_nom_vent_flow * val for val in data_vent )/8760
    annual_vent_flow_ppl = sum( nom_vent_flow_per_person * val for val in data_occ )/8760
    annual_vent_flow_total = annual_vent_flow_space + annual_vent_flow_ppl

    Output = namedtuple('Output', ['nominal', 'annual_avg'])
    output = Output( nom_vent_flow_total, annual_vent_flow_total  )

    return output

def hb_schedule_to_data(_schedule_name):
        try:
            _schedule = schedule_by_identifier(_schedule_name)
        except:
            return None
        
        week_start_day = 'Sunday'
        start_date, end_date, timestep = Date(1, 1), Date(12, 31), 1
        holidays = None

        data = _schedule.data_collection(
            timestep, start_date, end_date, week_start_day, holidays, leap_year=False)

        return data

def calc_space_vent_rates(_space, _hb_room, _hb_room_tfa, _hb_room_peak_vent_rate, _ghenv):
    """Determine the Vent flowrate (m3/h) for each PHPP Room based on the EP/HB Values"""

    #---------------------------------------------------------------------------
    # Guard
    
    if _hb_room.floor_area == 0:
        warning =   "Something wrong with the floor area - are you sure\n"\
                    "there is at least one 'Floor' surface making up the Room?"
        _ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, warning)
        return None

    if _hb_room_tfa == 0:
        warning =   "Got TFA of 0 - are you sure\n"\
                    "there is at least one 'TFA' surface in the Room?"
        _ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, warning)
        return None

    #---------------------------------------------------------------------------
    percent_of_total_zone_TFA = _space.space_tfa / _hb_room_tfa
    room_air_flow = percent_of_total_zone_TFA * _hb_room_peak_vent_rate
    room_air_flow = room_air_flow/2  # Div by 2 cus' half goes to supply, half to extract?

    return { 'V_sup': room_air_flow, 'V_eta': room_air_flow, 'V_trans': room_air_flow }

def generate_histogram(_data, _nbins):
    # Creates a dictionary Histogram of some data in n-bins
    
    min_val = min(_data)
    max_val = max(_data)
    hist_bins = {} # The number of items in each bin
    hist_vals = {} # The avg value for each bin
    total = 0

    # Initialize the dict
    for k in range(_nbins+1):
        hist_bins[k] = 0
        hist_vals[k] = 0
    
    # Create the Histogram
    for d in _data:
        bin_number = int(_nbins * ((d - min_val) / (max_val - min_val)))
        
        hist_bins[bin_number] += 1
        hist_vals[bin_number] += d
        total += 1
    
    # Clean up / fix the data for output
    for n in hist_vals.keys():
        hist_vals[n] =  hist_vals[n] / hist_bins[n]
    
    for h in hist_bins.keys():
        hist_bins[h] = float(hist_bins[h]) / total
    
    # The number of items in each bin, the avg value of the items in the bin
    return hist_bins, hist_vals 

def calc_space_vent_schedule(_space, _hb_room, _hb_room_tfa):
    if _hb_room_tfa == 0:
        return None

    # Create a PHPP-Style 3-part sched from the EP data
    occupancy_sched_name = _hb_room.properties.energy.people.occupancy_schedule.display_name
    bins, vals = generate_histogram(hb_schedule_to_data(occupancy_sched_name).values, 2)
    room_sched_from_hb = PHPP_Sys_VentSchedule( vals[2], bins[2], vals[1], bins[1], vals[0], bins[0] )
    
    # Compute the Room % of Total TFA and Room's Ventilation Airflows
    percentZoneTotalTFA = _space.space_tfa / _hb_room_tfa
    numOfPeoplePerArea = _hb_room.properties.energy.people.people_per_area
    vent_flow_per_person = _hb_room.properties.energy.ventilation.flow_per_person
    vent_flow_per_area = _hb_room.properties.energy.ventilation.flow_per_area
    roomFlowrate_People_Peak = numOfPeoplePerArea * _hb_room.floor_area * vent_flow_per_person * 60 * 60 * percentZoneTotalTFA
    
    # Calc total airflow for People
    # Calc the flow rates for people based on the HB Schedule values
    roomFlowrate_People_High = (room_sched_from_hb._speed_high * roomFlowrate_People_Peak) 
    roomFlowrate_People_Med = (room_sched_from_hb._speed_med * roomFlowrate_People_Peak) 
    roomFlowrate_People_Low = (room_sched_from_hb._speed_low * roomFlowrate_People_Peak) 
    
    roomVentilationPerArea = (vent_flow_per_area * _hb_room.floor_area * 60 * 60 * percentZoneTotalTFA)
    
    if roomVentilationPerArea != 0 and roomFlowrate_People_Peak != 0:
        roomFlowrate_Total_High = (roomFlowrate_People_High + roomVentilationPerArea) / (roomFlowrate_People_Peak + roomVentilationPerArea)
        roomFlowrate_Total_Med = (roomFlowrate_People_Med + roomVentilationPerArea) / (roomFlowrate_People_Peak + roomVentilationPerArea)
        roomFlowrate_Total_Low = (roomFlowrate_People_Low + roomVentilationPerArea) / (roomFlowrate_People_Peak + roomVentilationPerArea)

        # Re-set the Room's Vent Schedule Fan-Speeds based on the calculated rates
        # taking into account both Floor Area and People
        phppRoomVentSched = PHPP_Sys_VentSchedule(roomFlowrate_Total_High, bins[2], roomFlowrate_Total_Med, bins[1], roomFlowrate_Total_Low, bins[0] )
    else:
        phppRoomVentSched = PHPP_Sys_VentSchedule()
    
    return phppRoomVentSched