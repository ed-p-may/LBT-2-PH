"""Functions to manage data Grasshoppe IO related to DHW objects """

from LBT2PH.helpers import convert_value_to_metric, context_rh_doc
import rhinoscriptsyntax as rs
import Grasshopper.Kernel as ghK

def get_seg_if_number(_input): #-> [List]
    """Takes in an item from GH Component, returns if its a number, None if not

    Args:
        _input: An item from Grasshopper scene
    Returns:
        list[None] if not a number, list[float] if a valid number
    """
    
    try:
        return [ float( convert_value_to_metric(_input, 'M') ) ]
    except AttributeError:
        return []

def get_seg_if_geom(_input_node_index, _item, _geom, _ghenv, _ghdoc): #-> [List]
    """Tries to get the GH Component input as a Curve, returns a list of the curve segments 
    
    Args:
        _input_node_index: [int] The index of the GH Component input node to try and read
        _item: [int] The index num of the item to try and read from the GH Component input node
        _geom: The raw input from the GH Compontent
        _ghenv: ghenv
        _ghdoc: ghdoc
    Returns:
        segments: [list] All the segments of the input curve / geometry
    """
    
    with context_rh_doc( _ghdoc ):
        try:
            rhino_guid = _ghenv.Component.Params.Input[_input_node_index].VolatileData[0][_item].ReferenceID
            if str(rhino_guid) == '00000000-0000-0000-0000-000000000000':
                # Its a GH generated line / curve
                geom = _geom
            else:
                geom = rs.coercecurve( rhino_guid )
            
            if not geom:
                raise Exception('here')
            
            try:
                number_of_segments = geom.SegmentCount
            except:
                try:
                    geom = geom.ToPolyline()
                    number_of_segments = geom.SegmentCount
                except:
                    msg = 'Error: Cannot convert pipe_segments_ input {} to Polyline?\n'\
                        'Please input either a number, or a Curve / Polyline representing the pipe.'.format(type(geom))
                    raise Exception(msg)
            
            segments = [ geom.SegmentAt(i).Length for i in range(number_of_segments) ]
            return segments
        except:
            msg = 'Error trying to read the "pipe_segments" input?\n'\
                'Please only input either a number/list of numbers, or\n'\
                'Polyline objects representing the pipe lengths. I cannot\n'\
                'use the inputs of: {}.'.format(type(_geom))
            _ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Error, msg)

def get_rh_obj_param_dict(_input_node_index, _item, _ghenv, _ghdoc ): #->[Dict]
    """ Tries to go and get all the UserText params from the Rhino Object. Returns a Dict of all params found

    Args:
        _input_node_index: [int] The index of the GH Component input node to try and read
        _item: [int] The index num of the item to try and read from the GH Component input node
        _geom: The raw input from the GH Compontent
        _ghenv: ghenv
        _ghdoc: ghdoc
    Returns:
        obj_param_dict [dict]
    """
    
    with context_rh_doc( _ghdoc ):
        try:
            #If its a RH object...
            rhino_guid = _ghenv.Component.Params.Input[_input_node_index].VolatileData[0][_item].ReferenceID
            obj_param_dict = {k:rs.GetUserText(rhino_guid, k) for k in rs.GetUserText(rhino_guid)}
        except:
            # If its GH object....
            obj_param_dict = {}
        
        return obj_param_dict

def piping_input_values(_input_node=0, _user_input=[], _user_attr_dicts=[{}], _ghenv=None, _ghdoc=None): #-> List[Dict]
    """Gets the required inputs, organizes them all into a standardized list of dicts
    
    Args:
        _input_node: [int] The GH-Comp input node to read in segments from
        _user_input: [List] Could be a whole bunch of things. Numbers, Rhino Geometry, GH Geometry
        _user_attr_dicts: List[Dict] A list of dicts with user-determined attribute values to apply to the segments
        _ghenv: ghenv
        _ghdoc: ghdoc
    Returns:
        piping_inputs: List[Dict] The input element params in a standardized format, in a List of Dicts
            ie: [  {'length':12, 'diameter':0.023, ...}, {'length':15, 'diameter':0.4, ...}, .... ]
    """
    
    piping_inputs = []
    for i, seg in enumerate(_user_input):
        #---- Get all the attribute params for each segment input
        seg_params = get_rh_obj_param_dict(_input_node_index=_input_node, 
                                                _item=i, _ghenv=_ghenv, _ghdoc=_ghdoc)
        
        #---- Try and get the length info, handle if its numbers input, GH geom or RH geom
        seg_lengths = get_seg_if_number(seg)
        if not seg_lengths: 
            seg_lengths = get_seg_if_geom(_input_node_index=_input_node, 
                                    _item=i, _geom=seg, _ghenv=_ghenv, _ghdoc=_ghdoc)
        
        if not seg_lengths: continue

        #---- Update the seg's attr dict with the length for each seg, and any UD param attrs
        for s in seg_lengths:
            seg_params['length'] = s

        attr_dict = _user_attr_dicts[i] if i < len(_user_attr_dicts) else {}
        for k, v in attr_dict.items():
            if not seg_params.has_key(k): # or GH generated, geom, won't have any keys
                seg_params[k] = v 
            else:
                if v: # don't overwrite RH values with 'Nones'
                    seg_params[k] = v 

        piping_inputs.append( seg_params )  
    
    return piping_inputs

def clean_input(_in, _nm, _unit='-', _ghenv=None):
    """Utility function to clean input date, give useful warnings about out-of-bounds inputs """
    
    try:
        out = float(convert_value_to_metric(_in, _unit) )
        
        if _nm == "tank_standby_frac_":
            if out > 1:
                msg = r"Standby Units should be decimal fraction. ie: 30% should be entered as 0.30" 
                _ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, msg)
                return out/100
        elif _nm == "diameter_":
            if out > 1:
                unitWarning = "Check diameter units? Should be in METERS not MM." 
                _ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, unitWarning)
            
        return out

    except:
        msg = '"{}" input should be a number'.format(_nm)
        _ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, msg)
        return _in
