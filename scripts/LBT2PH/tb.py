import json
import rhinoscriptsyntax as rs
import Grasshopper.Kernel as ghK
import Rhino
import random
from collections import namedtuple

import LBT2PH.helpers

reload( LBT2PH.helpers )


class PHPP_ThermalBridge:
    def __init__(self, _nm=None, _len=1, _psi=0.01,
                _groupNo=15, _fRsi=None):
        self.id = random.randint(1000,9999)
        self.typename = _nm
        self.length = float(_len)        
        self._group_number = _groupNo
        self._fRsi = _fRsi
        self._psi_value = _psi
    
    @property
    def group_number(self):
        return str(self._group_number).split(':')[0]

    @property
    def psi_value(self):
        return self._psi_value
    
    @psi_value.setter
    def psi_value(self, _input):
        try:
            self._psi_value = float(_input)
        except ValueError as e:
            # Cus for estimated this wants to be a formula
            if '=SUM' in str(_input):
                self._psi_value = str(_input)
            else:
                print(e)
                print('Cannot set Psi-Value to "{}". Should be a number.'.format(_input))

    @property
    def fRsi(self):
        return self._fRsi
    
    @fRsi.setter
    def fRsi(self, _input):
        try:
            self._fRsi = float(_input)
        except ValueError as e:
            print('Cannot set fRsi to "{}". Should be a number.'.format(_input))

    def to_dict(self):
        d = {}

        d.update( {'id':self.id} )
        d.update( {'typename':self.typename} )
        d.update( {'length':self.length} )
        d.update( {'_group_number':self._group_number} )
        d.update( {'_fRsi':self.fRsi} )
        d.update( {'_psi_value':self.psi_value} )

        return d

    @classmethod
    def from_dict(cls, _dict):
        new_obj = cls()

        new_obj.id = _dict.get('id')
        new_obj.typename = _dict.get('typename')
        new_obj.length = _dict.get('length')
        new_obj._group_number = _dict.get('_group_number')
        new_obj._fRsi = _dict.get('_fRsi')
        new_obj._psi_value = _dict.get('_psi_value')

        return new_obj

    def __unicode__(self):
        return u'A PHPP Thermal-Bridge Object: < {}-{} >'.format(self.id, self.typename)
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
       return "{}(_nm={!r}, _len={!r}, _psi={!r},"\
           "_groupNo={!r}, _fRsi={!r})".format(
            self.__class__.__name__, self.typename, self.length,
            self.psi_value, self.group_number, self.fRsi)


def get_tb_libray_from_RH_doc( _ghenv, _ghdoc ):
    """ Goes and gets the TB library items from the Document User-Text
    Will return a dict of dicts, ie:
        {'TB_Name_01':{'Name':'example', 'fRsi':0.77, 'Psi-Value':0.1},... }
    """
    dict = {}
    
    with LBT2PH.helpers.context_rh_doc( _ghdoc ):
        if not rs.IsDocumentUserText():
            return dict
        
        keys = rs.GetDocumentUserText()
        tbKeys = [key for key in keys if 'PHPP_lib_TB_' in key]
        for key in tbKeys:
            try:
                val = json.loads( rs.GetDocumentUserText(key) )
                name = val.get('Name', 'Name Not Found')
                dict[name] = val
            except:
                msg = "Problem getting Psi-Values for '{}' from the Rhino scene? Check the\n"\
                "DocumentUserText and make sure the TBs are loaded properly.".format(name)
                _ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, msg)
    
    return dict

def get_values_from_rhino_obj( _count, _rh_lib, _ghenv ):
    """ Gets params from the Rhino Object UserText library """
    
    Output = namedtuple('Output', ['length', 'group', 'typename', 'psi_value', 'fRsi'])
    
    try:
        input_index = 3
        rhinoGuid = _ghenv.Component.Params.Input[input_index].VolatileData[0][_count].ReferenceID#.ToString()
        rh_obj = Rhino.RhinoDoc.ActiveDoc.Objects.Find( rhinoGuid )
        
        length = rh_obj.CurveGeometry.GetLength()
        group = rs.GetUserText(rh_obj, 'Group')
        typename = rs.GetUserText(rh_obj, 'Typename')
        psi_value = _rh_lib.get(typename, {}).get('psiValue', None)
        fRsi = _rh_lib.get(typename, {}).get('fRsi', None)
        
        return Output(length, group, typename, psi_value, fRsi)
        
    except AttributeError as e:
        print(e)
        msg = "Sorry, I am not sure what to do with the input: {} in 'linear_tb_lengths_'?\n"\
              "Please input either a Curve or a number/numbers representing the TB segments.".format(input)
        _ghenv.Component.AddRuntimeMessage( ghK.GH_RuntimeMessageLevel.Warning, msg )

def organize_input_values(_inputs, _psi_values, _fRsi_values, _ghenv, _ghdoc):
    """ Sorts out the input values to use for the TB Objects """
    
    def get_user_input(_count, _input_list=[], _name=None, _default=None ):
        output = None
        
        try:
            output = _input_list[_count]
        except IndexError as e:
            try:
                output = _input_list[0]
            except IndexError as e:
                if not output and _default:
                    msg = 'Please supply one or more {} for the TBs.'.format(_name)
                    _ghenv.Component.AddRuntimeMessage( ghK.GH_RuntimeMessageLevel.Remark, msg )
                output = _default
        
        return output

    # Get the document's TB Library data
    rhino_tb_lib = LBT2PH.tb.get_tb_libray_from_RH_doc( _ghenv, _ghdoc )
    
    lengths, groups, typenames, psi_vals, fRsis = {}, {}, {}, {}, {}
    input_param_sets_ = []
    ParamSet = namedtuple('ParamSet', ['length', 'group', 'typename', 'psi_value', 'fRsi'])
    
    #---------------------------------------------------------------------------
    # First, try and get any GH-Component Lengths
    for i, input in enumerate( _inputs ):
        try:
            lengths[i] = float( input )
            groups[i] = '15: Ambient'
            typenames[i] = None
            psi_vals[i] = get_user_input(i, _psi_values, _name='Psi-Values', _default=0.01 )
            fRsis[i] = get_user_input(i, _fRsi_values, _name='fRsi-Values', _default=0.7 )
        except AttributeError as e:
            continue
    
    # --------------------------------------------------------------------------
    # If no GH inputs, try finding Rhino inputs
    if not lengths:
        for i, input in enumerate( _inputs ):
            result = get_values_from_rhino_obj(i, rhino_tb_lib, _ghenv)
            
            lengths[i] = result.length
            groups[i] = result.group
            typenames[i] = result.typename
            
            # Allow the user to overrid the Rhino values if they want
            psi_val = get_user_input(i, _psi_values, _name='Psi-Values', _default=None )
            if psi_val:
                psi_vals[i] = psi_val
            else:
                psi_vals[i] = result.psi_value
            
            fRsi_val = get_user_input(i, _fRsi_values, _name='fRsi-Values', _default=None )
            if fRsi_val:
                fRsis[i] = fRsi_val
            else:
                fRsis[i] = result.fRsi 
    
    #---------------------------------------------------------------------------
    # Sort and organize all the input values
    lengths = (value for key,value in sorted(lengths.items(), reverse=True))
    groups = [value for key,value in sorted(groups.items(), reverse=True)]
    typenames = (value for key,value in sorted(typenames.items(), reverse=True))
    psi_vals = (value for key,value in sorted(psi_vals.items(), reverse=True))
    fRsis = (value for key,value in sorted(fRsis.items(), reverse=True))
    
    
    # Add the new data to the sets
    for l, g, t, psi, frsi in zip(lengths, groups, typenames, psi_vals, fRsis):
        input_param_sets_.append( ParamSet(l, g, t, psi, frsi) )
    
    return input_param_sets_

