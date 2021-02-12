from contextlib import contextmanager
from copy import deepcopy
import scriptcontext as sc
import Rhino
from copy import deepcopy
import re
import Grasshopper.Kernel as ghK
import rhinoscriptsyntax as rs
from timeit import default_timer

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
    except Exception as e:
        sc.doc = _ghdoc
        print(e)
        raise Exception
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
    
    codes = {
        'FT':'FT', "'":'FT',
        'IN':'IN', '"':'IN',
        'MM':'MM',
        'CM':'CM',
        'M':'M:',
        'IP':'IP',
        'FT3':'FT3',
        'M3':'M3',
        'F':'F', 'DEG F':'F',
        'C':'C', 'DEG C':'C',
        'CFM':'CFM', 'FT3/M':'CFM', 'FT3M':'CFM',
        'CFH':'CFH', 'FT3/H':'CFH', 'FT3H':'CFH',
        'L':'L',
        'GA':'GA', 'GALLON':'GA',
        'BTU/H':'BTUH', 'BTUH':'BTUH',
        'KBTU/H':'KBTUH', 'KBTUH':'KBTUH', 
        'TON':'TON',
        'W':'W',
        'WH':'WH',
        'KW':'KW',
        'KWH':'KWH',
        'W/M2K':'W/M2K', 'WM2K':'WM2K',
        'W/MK':'W/MK',
        'W/K':'W/K',
        'M3/H':'M3/H', 'M3H':'M3/H', 'CMH':'M3/H',
        'W/W':'W/W',
        'BTU/WH':'BTU/WH', 'BTUH/W':'BTU/WH', 'BTU/W':'BTU/WH',
        'R/IN':'R/IN', 'R-IN':'R/IN'
    }
    # Note: BTU/W conversion isnt really right, but I think many folks use that 
    # when they mean Btu/Wh (or Btu-h/W)

    _input_string = str(_in).upper()
    input_unit = codes.get(_input_string, 'SI')
   
    return input_unit

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
                'W/MK': {'SI':1, 'W/MK':1, 'IP':1.730734908, 'BTU/HR-FT-F':1.730734908, 'R/IN':'**-1*0.144227909'},
                'W/K':  {'SI':1, 'W/K':1, 'BTU/HR-F':1.895633976, 'IP':1.895633976},
                'M3':   {'SI':1, 'FT3':0.028316847},
                '-' :   {'SI':1, '-':1},
                'M3/H': {'SI':1, 'CFM':1.699010796, 'IP':1.699010796, 'CFH':101.9406477},
                'L':    {'SI':1, 'L':1, 'GALLON':3.78541, "GA":3.78541},
                'KW':   {'SI':1, 'KW':1, 'W':1000, 'BTUH':3412.141156, 'KBTUH':3.412141156, 'TON':0.284345096},
                'W':    {'SI':1, 'W':1, 'KW':0.001, 'BTUH':3.412141156, 'KBTUH':0.003412141, 'TON':0.000284345},
                'W/W':  {'SI':1, 'BTU/WH':0.293071111, 'IP':0.293071111}
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

class code_timer:
    """ helper function for figuring out why its all so slow.... """
    
    __slots__ = ('display_type', 'count', 'timer')

    def __init__(self, _display_type='time'):
        self.display_type = _display_type
        self.count = 1
        self.time = default_timer()
        
    def mark(self, pos_name):
        new_time = default_timer()
        elapsed_time = new_time - self.time
        
        if self.display_type == 'off':
            return
        elif self.display_type == 'time':
            print('{:.012f}'.format(elapsed_time))
        elif self.display_type == 'position':
            print('{} {}'.format(self.count, pos_name))
        
        self.count += 1
        self.time = new_time
 
def get_rh_obj_UserText_dict(_ghdoc, _rh_obj_guid):
    """ Get any Rhino-side parameter data for the Object/Element

    Note: this only works in Rhino v6.0+ I believe...
    
    Args:
        _ghdoc (ghdoc): The 'ghdoc' object from the Grasshopper document.
        _rh_obj_guid (Rhino Guid): The Rhino Guid of the Object/Element.
    Returns:
        object_rh_UserText_dict (dict): A dictionary of all the data found
            in the Rhino object's UserText library.
    """
    
    def is_gh_guid(_guid):
        """If its GH generated geom, will have this GUID always """

        return str(_guid) == '00000000-0000-0000-0000-000000000000'

    if not _rh_obj_guid:
        return {}

    if is_gh_guid(_rh_obj_guid):
        return {}

    with context_rh_doc(_ghdoc):
        rh_obj = Rhino.RhinoDoc.ActiveDoc.Objects.Find( _rh_obj_guid )
        object_rh_UserText_dict = {k:rs.GetUserText(rh_obj, k) for k in rs.GetUserText(rh_obj)}
        
        # Fix the name
        object_name = rs.ObjectName(_rh_obj_guid)
        object_rh_UserText_dict['Object Name'] = object_name

    return object_rh_UserText_dict
