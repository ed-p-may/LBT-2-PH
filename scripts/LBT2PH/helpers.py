from contextlib import contextmanager
from copy import deepcopy
import scriptcontext as sc
import Rhino
from copy import deepcopy
import re
import Grasshopper.Kernel as ghK

import spaces
import occupancy
reload( spaces )
reload( occupancy )

from honeybee.typing import clean_and_id_ep_string
from honeybee_energy.schedule.ruleset import ScheduleRuleset
from honeybee_energy.lib.scheduletypelimits import schedule_type_limit_by_identifier


def add_to_HB_model( _hb_model, _key, _dict, _ghenv, _write='update' ):

    user_data = deepcopy( _hb_model.user_data )
    if not user_data:
        if _key == 'phpp':
            _hb_model.user_data = {'phpp': _dict }
            return _hb_model
        else:
            _hb_model.user_data = {'phpp': { _key: _dict} }
            return _hb_model
    
    try:
        if _write == 'update':
            user_data['phpp'][_key].update( _dict )
        elif _write == 'overwrite':
            user_data['phpp'][_key] = _dict
    except KeyError as e:
        try:
            user_data['phpp'].update( {_key:_dict } )
        except KeyError:
            try:
                user_data = {'phpp':{_key:_dict }}
            except Exception as e:
                msg = e
                msg += 'Error writing data to the model user_data?'
                _ghenv.Component.AddRuntimeMessage( ghK.GH_RuntimeMessageLevel.Error, msg )

    _hb_model.user_data = user_data
    return _hb_model

@contextmanager
def context_rh_doc(_ghdoc):
    ''' Switches the sc.doc to the Rhino Active Doc temporaily '''
    if not _ghdoc:
        return

    try:
        sc.doc = Rhino.RhinoDoc.ActiveDoc
        yield
    finally:
        sc.doc = _ghdoc

def preview_obj(_classObj):
    ''' For looking at the contents of a Class Object '''

    if not hasattr(_classObj, '__dict__'):
    	print('{} object "{}" has no "__dict__" attribute.'.format(type(_classObj), _classObj))
    	return None
    
    print('-------')
    print('CLASS:: {}'.format( _classObj.__class__.__name__) )
    for item_key, item in _classObj.__dict__.items():
        try:
            print('   > {} ::: {}'.format(item_key, item))
        except:
            pass

def find_input_string(_in):
    """ Util func  used by the unit converter """
    
    evalString = str(_in).upper()

    if 'FT' == evalString or "'" == evalString:
        inputUnit = 'FT'
    elif 'IN' == evalString or '"' == evalString:
        inputUnit = 'IN'
    elif 'MM' == evalString:
        inputUnit = 'MM'
    elif 'CM' == evalString:
        inputUnit = 'CM'
    elif 'M' == evalString and 'MM' != evalString:
        inputUnit = 'M'
    elif 'IP' == evalString:
        inputUnit = 'IP'
    elif 'FT3' == evalString:
        inputUnit = 'FT3'
    elif 'F' == evalString:
        inputUnit = 'F'
    elif 'CFM' == evalString:
        inputUnit = 'CFM'
    elif 'L' == evalString:
        inputUnit = 'L'
    elif 'GA' == evalString:
        inputUnit = 'GA'
    elif 'GALLON' == evalString:
        inputUnit = 'GA'
    else:
        inputUnit = 'SI'
    
    return inputUnit

def convert_value_to_metric(_inputString, _outputUnit):
    """ Will convert a string such as "12 FT" into the corresponding Metric unit
    
    Arguments:
        _inputString: String: The input value from the user
        _outputUnit: String: ('M', 'CM', 'MM', 'W/M2K', 'W/MK', 'M3') The desired unit
    """

    # {Unit you want: {unit user input}, {..}, ...}
    schema = {
                'F':    {'SI':'*(9.0/5.0)+32.0', 'C':'*(9.0/5.0)+32.0', 'F':1, 'IP':1},
                'C':    {'SI':1, 'C':1, 'K':1, 'F':'-32.0)*(5.0/9.0', 'IP':'-32.0)*(5.0/9.0'},
                'M':    {'SI': 1, 'M':1, 'CM':0.01, 'MM':0.001, 'FT':0.3048, "'":0.3048, 'IN':0.0254, '"':0.0254},
                'CM':   {'SI': 1, 'M':100, 'CM':1, 'MM':0.1, 'FT':30.48, "'":30.48, 'IN':2.54, '"':2.54},
                'MM':   {'SI': 1, 'M':1000, 'CM':10, 'MM':1, 'FT':304.8, "'":304.8, 'IN':25.4, '"':25.4},
                'W/M2K':{'SI':1, 'W/M2K':1, 'IP':5.678264134, 'BTU/HR-FT2-F':5.678264134, 'HR-FT2-F/BTU':'**-1*5.678264134'},
                'W/MK': {'SI':1, 'W/MK':1, 'IP':1.730734908, 'BTU/HR-FT-F':1.730734908},
                'W/K':  {'SI':1, 'W/K':1, 'BTU/HR-F':1.895633976, 'IP':1.895633976},
                'M3':   {'SI':1, 'FT3':0.028316847},
                '-' :   {'SI':1, '-':1},
                'M3/H': {'SI':1, 'CFM':1.699010796, 'IP':1.699010796},
                'L':    {'SI':1, 'L':1, 'GALLON':0.264172, "GA":0.264172}
              }
                 
    inputValue = _inputString
    
    if _inputString is None:
        return None
    
    try:
        return float(inputValue)
    except:
        try:
            string_found, value_found = None, None

            # Pull out just the decimal numeric characters, if any
            for each in re.split(r'[^\d\.]', _inputString):
                if len(each)>0:
                    value_found = each
                    break # so it will only take the first number found, "123 ft3" doesn't work otherwise
            
            # Pull out just the NON decimal numeric characters, if any
            for each in re.split(r'[^\D\.]', _inputString):
                if each == '.':
                    continue
                
                if len(each) == 0:
                    continue
                
                string_found = each.upper().lstrip().rstrip()
                break
            
            if string_found or value_found:
                input_unit = find_input_string(string_found)
                conversion_factor = schema.get(_outputUnit, {}).get(input_unit, 1)

                try:
                    output_val = float(value_found) * float(conversion_factor)
                    print('Converting input "{}" >>> {} * {} = {} {}'.format(inputValue, value_found, conversion_factor, output_val, _outputUnit)) 
                except ValueError as e:
                    output_val = float(eval('({}{})'.format(value_found, conversion_factor)))   
                    print('Converting input "{}" >>> ({}{}) = {} {}'.format(inputValue, value_found, conversion_factor, output_val, _outputUnit))
                                     
                return output_val
            else:
                return _inputString
        except:
            return inputValue

def create_hb_constant_schedule(_name, _type_limit='Fractional'):
    type_limit = schedule_type_limit_by_identifier( _type_limit )

    schedule = ScheduleRuleset.from_constant_value(
        clean_and_id_ep_string(_name), 1, type_limit)

    schedule.display_name = _name

    return schedule

def get_model_tfa(_model):
    tfa = 0
    for room in _model.rooms:
        for space in room.user_data.get('phpp', {}).get('spaces').values():
            space_obj = spaces.Space.from_dict( space )
            tfa += space_obj.space_tfa
    
    return tfa
 
def get_model_occupancy(_model, _ghenv):
    try:
        occ_dict = _model.user_data.get('phpp', {}).get('occupancy', None)
        
        if not occ_dict:
            raise ValueError
        
        occ_obj = occupancy.Occupancy.from_dict( occ_dict )
        
        return occ_obj
    except ValueError:
        msg = "Error getting Occupancy from the Honeybee Model? Please use an LBT2PH 'Occupancy'\n"\
        "component before using this one in order to set the number of units and the occupancy level of the\n"\
        "building. For now, I will assume 1-Unit and calculate the occupancy based on the model's gross floor area"
        _ghenv.Component.AddRuntimeMessage( ghK.GH_RuntimeMessageLevel.Warning, msg  )
        
        occ_obj = occupancy.Occupancy( _tfa=_model.floor_area  )
        return occ_obj

