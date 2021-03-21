from collections import namedtuple
import re
import random

import rhinoscriptsyntax as rs
import ghpythonlib.components as ghc
import Rhino
import Grasshopper.Kernel as ghK
from System import Object

from honeybee_energy.schedule.ruleset import ScheduleRuleset
from honeybee_energy.lib.schedules import schedule_by_identifier
from ladybug.dt import Date

import LBT2PH
import LBT2PH.helpers

reload( LBT2PH )
reload( LBT2PH.helpers )

class duct_input_handler:
    """Manages the varous types of inputs that the user might give for the ducts """
    
    def __init__(self, _ghdoc, _ghenv):
        self.ghdoc = _ghdoc
        self.ghenv = _ghenv
    
    def is_gh_geometry(self, _in):
        """Geom that is generated 'in' Grasshopper has a 0 GUID """
        
        if _in == '00000000-0000-0000-0000-000000000000':
            return True
        else:
            return False
    
    def get_input_GUID(self, i, index_num):
        """Find the actual GUID of the input object from its input node 
        Args:
            i (int): The index of the input list to look at
            index_num (int): The index number of the input-node to look at
        """
        
        guid = self.ghenv.Component.Params.Input[index_num].VolatileData[0][i].ReferenceID.ToString()
        
        return guid
    
    def get_params_from_rhino(self, _in):
        """Got and find any param values in the geometry in the RH Scene 
        Args:
            _in (Rhino.Geometry.Curve): The Rhino Curve object to look at
        Returns:
            (tuple) length, width, thickness, lambda
        """
        
        with LBT2PH.helpers.context_rh_doc(self.ghdoc):
            try:
                l = float( ghc.Length(_in) )
                w = float( rs.GetUserText(_in, 'ductWidth') )
                t = float( rs.GetUserText(_in, 'insulThickness') )
                c = float( rs.GetUserText(_in, 'insulConductivity') )
            except Exception as e:
                print('Error getting values from Rhino Scene\n{}'.format(e))
                return None, None, None, None
            
        return l, w, t, c

    def get_segment(self, i, _in, _input_node_index_num):
        """Sorts out and gets the params of the input (number | curve | line) 
        Args:
            i (int): The index of the segment to be analysed
            _in (number | curve | line): The input item to be analysed 
        Returns:
            (namedtuple) Segment(length='', width='', i_thickness='', i_lambda='')
        """
        
        Segment = namedtuple('Segment', ['length', 'width', 'i_thickness', 'i_lambda'])
        
        try:
            # If its just a regular number input
            length =  float(LBT2PH.helpers.convert_value_to_metric(_in, 'M'))
            return Segment(length, None, None, None)
        except AttributeError as e:
            # OK, so its not a regular number, try and sort out what geometry it is...
            seg_GUID = self.get_input_GUID(i, _input_node_index_num)
            
            if isinstance(_in, Rhino.Geometry.Curve):
                if self.is_gh_geometry(seg_GUID):
                    crv = rs.coercecurve(_in)
                    crv_length = crv.GetLength()
                    return Segment(crv_length, None, None, None)
                else:
                    return Segment( *self.get_params_from_rhino(seg_GUID) )
            
            elif isinstance(_in, Rhino.Geometry.Line):
                if self.is_gh_geometry(seg_GUID):
                    line = rs.coerceline(_in)
                    line_len = line.Length
                    return Segment(line_len, None, None, None)
                else:
                    return Segment( *self.get_params_from_rhino(seg_GUID) )
            
            else:
                msg = ' Sorry, I do not understand the input for _duct_length?\n'\
                        'Please input either: a list of Rhino Curves, Lines or numbers representing\n'\
                        'the lengths of the duct segments.\n\n{}'.format(e)
                raise Exception(msg)


class PHPP_Sys_Duct_Segment(Object):
    def __init__(self, _len=1, _width=104, _i_thick=52, _i_lambda=0.04):
        """An individual duct segment. A duct is made of 1 or more segments.

        Args:
            _len (float): The length of the segment in Meters
            _width (float): The width of the segment in MM
            _i_thick (float): The thickness of the segment's insualtion, in MM
            _i_lambda (float): The lambda condictivity of the segment's insualtion in W/mk
        """
        
        self.id = random.randint(1000,9999)
        self.length = _len
        self.width = _width
        self.insul_thick = _i_thick
        self.insul_lambda = _i_lambda

    def to_dict(self):
        d = {}
        d.update( { 'id':self.id} )
        d.update( { 'length':self.length } )
        d.update( { 'width':self.width } )
        d.update( { 'insulation_thickness':self.insul_thick } )
        d.update( { 'insulation_lambda':self.insul_lambda } )
        
        return d

    @classmethod
    def from_dict(cls, _dict):
        new_segment = cls()
        new_segment.id = _dict.get('id')
        new_segment.length = _dict.get('length')
        new_segment.width = _dict.get('width')
        new_segment.insul_thick = _dict.get('insulation_thickness')
        new_segment.insul_lambda = _dict.get('insulation_lambda')
        
        return new_segment

    def __unicode__(self):
        return u'PHPP Ventilation Duct-Segment Object'
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
        return "{}( _len={!r}, _width={!r}, _i_thick={!r}, _i_lambda={!r})".format(
                self.__class__.__name__,
                self.length,        
                self.width,
                self.insul_thick,
                self.insul_lambda
                )
    def ToString(self):
        return str(self)


class PHPP_Sys_Duct(Object):
    def __init__(self, _segments=[PHPP_Sys_Duct_Segment()] ):
        """A Single Duct Object representing a collection of Duct-Segments

        Args: _segments (list): A list of 'PHPP_Sys_Duct_Segment' objects 
        """
        self.id = random.randint(1000,9999)
        self._segments = _segments

    def _len_weighted_avg(self, _attr):
        """Returns length-weighted average duct attr """
        print('here', self._segments)
        for seg in self._segments:
            print(seg.length, _attr, getattr(seg, _attr))

        weighted_total = sum(seg.length * getattr(seg, _attr) for seg in self._segments)
        
        try:
            return weighted_total / self.duct_length
        except ZeroDivisionError:
            msg = " Can't calculate the weighted average. Duct segment has a 0m length?"
            raise ZeroDivisionError(msg)

    @property
    def segments(self):
        return self._segments

    @segments.setter
    def segments(self, _in):
        if isinstance(_in, list):
            self._segments = _in
        else:
            msg = 'Error: input for {} "segments" must be a list.'.format(self.__class__.__name__)
            raise Exception(msg)
    @property
    def duct_length(self):       
        return sum(segment.length for segment in self._segments)

    @property
    def duct_width(self):
        return self._len_weighted_avg('width')

    @property
    def insulation_thickness(self):
        return self._len_weighted_avg('insul_thick')

    @property
    def insulation_lambda(self):
        return self._len_weighted_avg('insul_lambda')
    
    def to_dict(self):
        d = {}

        d.update( { 'id':self.id} )

        seg_d = {}
        for segment in self._segments:
            seg_d.update( {segment.id: segment.to_dict()} )
        d.update( { 'segments':seg_d} )

        return d

    @classmethod
    def from_dict(cls, _dict):
        new_obj = cls()
        new_obj.id = _dict.get('id')

        segments = []
        for segment in _dict.get('segments', {}).values():
            seg = PHPP_Sys_Duct_Segment.from_dict(segment)
            segments.append(seg)
        new_obj.segments = segments

        return new_obj

    def __unicode__(self):
        return u'PHPP Ventilation Duct Object'
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
        return "{}( _segments={!r})".format(
                self.__class__.__name__,
                self.segments)
    def ToString(self):
        return str(self)
    

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
    def ToString(self):
        return str(self)


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
    def ToString(self):
        return str(self)


class PHPP_Sys_VentSchedule(Object):
    def __init__(self, s_h=1.0, t_h=1.0, s_m=0.77, t_m=0.0, s_l=0.4, t_l=0.0):
        self.id = random.randint(1000,9999)
        self.speed_high = s_h
        self.time_high = t_h
        self.speed_med = s_m
        self.time_med = t_m
        self.speed_low = s_l
        self.time_low = t_l

    def to_dict(self):
        d = {}
        d.update( {'id':self.id} )
        d.update( {'speed_high':self.speed_high} )
        d.update( {'time_high':self.time_high} )
        d.update( {'speed_med':self.speed_med} )
        d.update( {'time_med':self.time_med} )
        d.update( {'speed_low':self.speed_low} )
        d.update( {'time_low':self.time_low} )

        return d

    @classmethod
    def from_dict(cls, _dict):
        new_sched = cls()
        new_sched.id = _dict['id']
        new_sched.speed_high = _dict['speed_high']
        new_sched.time_high = _dict['time_high']
        new_sched.speed_med = _dict['speed_med']
        new_sched.time_med = _dict['time_med']
        new_sched.speed_low = _dict['speed_low']
        new_sched.time_low = _dict['time_low']

        return new_sched

    def check_total(self):
        total_time = self.time_high + self.time_med + self.time_low
        if total_time > 1.001 or total_time < 0.999:
            msg = "Error. The Operation times don't add up to 100%? Please correct the inputs."
            return msg
        else:
            return None

    def __str__(self):
        return unicode(self).encode('utf-8')
    def __unicode__(self):
        return u'A PHPP Ventilation Schedule Object: <{self.id}>'.format(self=self)
    def __repr__(self):
        return "{}( s_h={!r}, t_h={!r}, s_m={!r}, t_m={!r}, s_l={!r}, t_l={!r})".format(
                self.__class__.__name__,
                self.speed_high,
                self.time_high,
                self.speed_med,
                self.time_med,
                self.speed_low,
                self.time_low)
    def ToString(self):
        return str(self)


class PHPP_Sys_Ventilation(Object):
    def __init__(self,
                _ghenv=None,
                _system_type='1-Balanced PH ventilation with HR',
                _systemName='Vent-1',
                _unit=PHPP_Sys_VentUnit(),
                _d01=PHPP_Sys_Duct(),
                _d02=PHPP_Sys_Duct(),
                _exhaustObjs=[]):
        
        self.system_id = random.randint(1000,9999)
        self.ghenv = _ghenv
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
        return self.system_id == other.system_id
    
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
        if self.exhaust_vent_objs:
            d.update( {'exhaust_vent_objs': [exhaust_obj.to_dict() for exhaust_obj in self.exhaust_vent_objs] } )

        return d

    @classmethod
    def from_dict(cls, _dict, _ghenv=None):

        exhaust_objs = []
        for exhaust_system_dict in _dict.get('exhaust_vent_objs', []):
            exhaust_objs.append( PHPP_Sys_ExhaustVent.from_dict(exhaust_system_dict) )

        new_obj = cls()
        new_obj.ghenv = _ghenv
        new_obj.system_id = _dict.get('system_id')
        new_obj.system_type = _dict.get('system_type')
        new_obj.system_name = _dict.get('system_name')
        new_obj.vent_unit = PHPP_Sys_VentUnit.from_dict(_dict.get('vent_unit') )
        new_obj.duct_01 = PHPP_Sys_Duct.from_dict( _dict.get('duct_01') )
        new_obj.duct_02 = PHPP_Sys_Duct.from_dict( _dict.get('duct_02') )
        new_obj.exhaust_vent_objs = exhaust_objs
        
        return new_obj

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
    def ToString(self):
        return str(self)


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
    roomFlowrate_People_High = (room_sched_from_hb.speed_high * roomFlowrate_People_Peak) 
    roomFlowrate_People_Med = (room_sched_from_hb.speed_med * roomFlowrate_People_Peak) 
    roomFlowrate_People_Low = (room_sched_from_hb.speed_low * roomFlowrate_People_Peak) 
    
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