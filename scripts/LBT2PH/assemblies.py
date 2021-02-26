import helpers
import json
import rhinoscriptsyntax as rs
import Grasshopper.Kernel as ghK
import scriptcontext as sc
from collections import namedtuple

try:  # import the honeybee dependencies
    from honeybee.typing import clean_and_id_ep_string
    from honeybee_energy.material.opaque import EnergyMaterial
    from honeybee_energy.material.opaque import EnergyMaterialNoMass
    from honeybee_energy.construction.opaque import OpaqueConstruction
#    from honeybee_energy.lib.materials import opaque_material_by_identifier
except ImportError as e:
    raise ImportError('\nFailed to import honeybee_energy:\n\t{}'.format(e))

class PHPP_Construction:
    Layer = namedtuple('Layer', ['layer_number', 'layer_name'])
    
    def __init__(self, _hb_const):
        self.hb_const = _hb_const

    @property
    def u_value(self):
        return self.hb_const.u_value

    @property
    def hb_display_name(self):
        return self.hb_const.display_name

    @property
    def identifier(self):
        return self.hb_const.identifier

    @property
    def IntInsul(self):
        if '__Int__' in self.hb_const.identifier:
            return 'x'
        else:
            return None

    @property
    def phpp_name(self):
        nm = self.hb_const.display_name
        nm = nm.replace('__Int__', '')
        nm = nm.replace('PHPP_CONST_', '')
        nm = nm.replace(' ', '_')

        return nm

    @property
    def Layers(self):
        layers = []
        for i, layer in enumerate(self.hb_const.layers):
            mat = self.hb_const.materials[i]
            layers.append( self.Layer(i, mat.display_name )  )

        return layers
    
    def __unicode__(self):
        return u'A PHPP-Style Construction Object: < {} >'.format(self.phpp_name)
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
       return "{}(_hb_const={!r})".format(self.__class__.__name__, self.hb_const)

def get_constructions_from_rh(_ghdoc):
    ''' Returns a dict with all the assemblies found in the Rhino UserText'''
    
    constructions_ = {}
    
    with helpers.context_rh_doc(_ghdoc):
        if not rs.IsDocumentUserText():
            return constructions_
        
        for key in rs.GetDocumentUserText():
            if 'PHPP_lib_Assmbly_' in key:
                value_as_str = rs.GetDocumentUserText(key)
                value_as_dict = json.loads(value_as_str)
                assembly_name = value_as_dict.get('Name')
                constructions_[assembly_name] = value_as_dict
        
        return constructions_

def generate_all_HB_constructions(_rh_doc_constructions, _ghenv):
    ''' Returns a list of HB Construction Objects. One for each Construction found in the Rhino UserText '''
    
    assert type(_rh_doc_constructions) is dict, '"create_HB_construction" input should be type: dict'
    
    constructions = {}
    for nm, construction in _rh_doc_constructions.items():
        #---------------------------------------------------------------------------------------------------
        # Get the construction parameters
        try:
            nm = construction.get('Name', 'NO_NAME').upper()
            uval = float(construction.get('uValue', 1.0))
            rval = float(1/uval)
            intInsul = construction.get('intInsulation', None)
            if intInsul:
                intInsul = 1
            else:
                intInsul = 0
        except Exception as e:
            print(e)
            nm = construction.get('Name', 'NO_NAME').upper()
            uval = 1.0
            rval = 1.0
            intInsul = 0
            warning = 'Something went wrong getting the Construction Assembly info for the Assembly type: "{}" from the Rhino Library?\n'\
            'No assembly by that name, or a non-numeric entry found in the Library? Please check the Library File inputs.\n'\
            'For now, I will assign a U-Value of 1.0 W/m2k to this assembly as a default value.'.format(nm.upper())
            _ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, warning)

        #---------------------------------------------------------------------------------------------------
        # Clean up the names
        name_construction = "PHPP_CONST_{}".format(nm).upper().replace(" ", "_")
        name_material = "PHPP_MAT_{}".format(nm).upper().replace(" ", "_")

        #---------------------------------------------------------------------------------------------------
        # Add the tag to the name if Interior Insulated
        intInsulFlag = '__Int__'
        if intInsul == 1:
            name_construction = name_construction + intInsulFlag
            name_material = name_material + intInsulFlag
        
        #---------------------------------------------------------------------------------------------------
        # Build the Materials
        # So that we don't end up with lots of MassLayers, check if there is already one in the Sticky first
        if 'LBT2PH_std_mass_material' in sc.sticky:
            hb_mass_layer = sc.sticky.get('LBT2PH_std_mass_material')
        else:
            hb_mass_layer = create_std_mass_material()
            sc.sticky['LBT2PH_std_mass_material'] = hb_mass_layer
        hb_no_mass_materal = create_HB_material_no_mass(name_material, rval)

        #---------------------------------------------------------------------------------------------------
        # Build the Construction
        construction_layers = [hb_mass_layer, hb_no_mass_materal, hb_mass_layer]
        new_EP_Construction = create_HB_construction(name_construction, construction_layers)
        k = name_construction.replace(intInsulFlag, '') # Scrub the flag for the dict only
        constructions[k] = new_EP_Construction

    return constructions

def create_std_mass_material():
    ''' Simple 'Mass' Layer for inside/outside of simple constuctions '''

    try:
        # Set the default material properties
        roughness = 'MediumRough'
        therm_absp = 0.9
        sol_absp = 0.7
        vis_absp = 0.7
        name = 'MASSLAYER'
        thickness = 0.0254
        conductivity = 2
        density = 2500
        spec_heat = 460
        
        # Create the material
        mat = EnergyMaterial(
            clean_and_id_ep_string(name), thickness, conductivity, density,
            spec_heat, roughness, therm_absp, sol_absp, vis_absp)
        mat.display_name = name
        
        return mat
    except Exception as e:
        print('Error creating HB Material', e)
        return None

def create_HB_material_no_mass(_material_name, _material_r_value):   
    """ Creates an HB Style "No-Mass" Material """

    try:
        # set the default material properties
        name = _material_name
        r_value = _material_r_value
        roughness = 'MediumRough'
        therm_absp = 0.9
        sol_absp = 0.7
        vis_absp = 0.7
        
        # create the NoMass material
        mat = EnergyMaterialNoMass(
            clean_and_id_ep_string(name), r_value, roughness, therm_absp,
            sol_absp, vis_absp)
        mat.display_name = name

        return mat
    except Exception as e:
        print('Error creating HB Material', e)
        return None

def create_HB_construction(_name, _layers):
    ''' Builds a HB Style Construction Object from a list of HB-Material layers'''

    try:       
        constr = OpaqueConstruction(clean_and_id_ep_string(_name), _layers)
        constr.display_name = _name
        return constr
    except Exception as e:
        print('Error creating Construction', e)
        return None