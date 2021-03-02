DEV_MODE = True
RELEASE_VERSION = "LBT2PH v0.1"
CATEGORY = "PH-Tools"
SUB_01_MODEL = '01 | Model'

sub_catagories = {
    1: "01 | Model",
    2: "02 | LBT2PH",
    3: "03 | Exel",
}

component_params = {
    #---------------------------------------------------------------------------
    # Section 01.1 | Geometry
    'LBT2PH PHPP Aperture':{
        'NickName':'PHPP Aperture',
        'Message': RELEASE_VERSION,
        'Category': CATEGORY,
        'SubCategory': 1,
    },
    'LBT2PH PHPP Aperture Frame':{
        'NickName':'PHPP Frame',
        'Message': RELEASE_VERSION,
        'Category': CATEGORY,
        'SubCategory': 1,
    },
    'LBT2PH PHPP Aperture Glazing':{
        'NickName':'PHPP Glazing',
        'Message': RELEASE_VERSION,
        'Category': CATEGORY,
        'SubCategory': 1,
    },
    'LBT2PH Get Surface Params':{
        'NickName':'Get Surface Params',
        'Message': RELEASE_VERSION,
        'Category': CATEGORY,
        'SubCategory': 1,
    },
    'LBT2PH Ground':{
        'NickName':'PHPP Ground Element',
        'Message': RELEASE_VERSION,
        'Category': CATEGORY,
        'SubCategory': 1,
    },
    'LBT2PH Thermal Bridges':{
        'NickName':'PHPP Thermal Bridges',
        'Message': RELEASE_VERSION,
        'Category': CATEGORY,
        'SubCategory': 1,
    },
    'LBT2PH Surface Attributes':{
        'NickName':'PHPP Surface Attrs.',
        'Message': RELEASE_VERSION,
        'Category': CATEGORY,
        'SubCategory': 1,
    },
    #---------------------------------------------------------------------------
    # Section 01.2 | Airflow
    'LBT2PH Airtightness':{
        'NickName':'Airtightness',
        'Message': RELEASE_VERSION,
        'Category': CATEGORY,
        'SubCategory': 1,
    },
    'LBT2PH Create PHPP Spaces':{
        'NickName':'PHPP Spaces',
        'Message': RELEASE_VERSION,
        'Category': CATEGORY,
        'SubCategory': 1,
    },
    'LBT2PH Summer Ventilation':{
        'NickName':'Summer Vent.',
        'Message': RELEASE_VERSION,
        'Category': CATEGORY,
        'SubCategory': 1,
    },
    #---------------------------------------------------------------------------
    # Section 01.3 | Ventilation System
    'LBT2PH Vent Exhaust Unit':{
        'NickName':'Exhaust Vent.',
        'Message': RELEASE_VERSION,
        'Category': CATEGORY,
        'SubCategory': 1,
    },
    'LBT2PH Vent Duct':{
        'NickName':'Vent. Duct',
        'Message': RELEASE_VERSION,
        'Category': CATEGORY,
        'SubCategory': 1,
    },
    'LBT2PH Vent System':{
        'NickName':'Vent. System',
        'Message': RELEASE_VERSION,
        'Category': CATEGORY,
        'SubCategory': 1,
    },
    'LBT2PH Vent Unit':{
        'NickName':'HRV/ERV Unit',
        'Message': RELEASE_VERSION,
        'Category': CATEGORY,
        'SubCategory': 1,
    },
    'LBT2PH Vent Schedule':{
        'NickName':'Vent Schedule',
        'Message': RELEASE_VERSION,
        'Category': CATEGORY,
        'SubCategory': 1,
    }, 
    #---------------------------------------------------------------------------
    # Section 01.4 | Shading
    'LBT2PH Shading Apply Factors':{
        'NickName':'Apply Shading Factors',
        'Message': RELEASE_VERSION,
        'Category': CATEGORY,
        'SubCategory': 1,
    }, 
    'LBT2PH Shading Dimensions':{
        'NickName':'Shading Dimensions',
        'Message': RELEASE_VERSION,
        'Category': CATEGORY,
        'SubCategory': 1,
    }, 
    'LBT2PH Shading Window Reveals':{
        'NickName':'Window Reveals',
        'Message': RELEASE_VERSION,
        'Category': CATEGORY,
        'SubCategory': 1,
    }, 
    'LBT2PH Shading Seasonal Radiation':{
        'NickName':'Calc. Seasonal Radiation',
        'Message': RELEASE_VERSION,
        'Category': CATEGORY,
        'SubCategory': 1,
    }, 
    #---------------------------------------------------------------------------
    # Section 01.5 | DHW
    'LBT2PH DHW Piping Branches':{
        'NickName':'Piping | Branches',
        'Message': RELEASE_VERSION,
        'Category': CATEGORY,
        'SubCategory': 1,
    }, 
    'LBT2PH DHW Piping Recirc':{
        'NickName':'Piping | Recirc.',
        'Message': RELEASE_VERSION,
        'Category': CATEGORY,
        'SubCategory': 1,
    }, 
    'LBT2PH DHW Solar Thermal':{
        'NickName':'Solar Thermal System',
        'Message': RELEASE_VERSION,
        'Category': CATEGORY,
        'SubCategory': 1,
    }, 
    'LBT2PH DHW System':{
        'NickName':'DHW System',
        'Message': RELEASE_VERSION,
        'Category': CATEGORY,
        'SubCategory': 1,
    }, 
    'LBT2PH DHW Tank':{
        'NickName':'DHW Tank',
        'Message': RELEASE_VERSION,
        'Category': CATEGORY,
        'SubCategory': 1,
    }, 
    'LBT2PH DHW Usage':{
        'NickName':'DHW Usage',
        'Message': RELEASE_VERSION,
        'Category': CATEGORY,
        'SubCategory': 1,
    }, 
    #---------------------------------------------------------------------------
    # Section 01.6 | Residential Loads
    'LBT2PH Loads by PNNL':{
        'NickName':'Loads by PNNL',
        'Message': RELEASE_VERSION,
        'Category': CATEGORY,
        'SubCategory': 1,
    },
    'LBT2PH Loads by PHPP Occupancy':{
        'NickName':'PHPP Occupancy',
        'Message': RELEASE_VERSION,
        'Category': CATEGORY,
        'SubCategory': 1,
    },
    'LBT2PH Loads by PHPP Appliances':{
        'NickName':'PHPP Appliances',
        'Message': RELEASE_VERSION,
        'Category': CATEGORY,
        'SubCategory': 1,
    },
    #---------------------------------------------------------------------------
    # Section 01.7 | Heating & Cooling
    'LBT2PH Cooling Dehumid':{
        'NickName':'Cooling | Dehumid',
        'Message': RELEASE_VERSION,
        'Category': CATEGORY,
        'SubCategory': 1,
    },
    'LBT2PH Cooling Panel':{
        'NickName':'Cooling | Panel',
        'Message': RELEASE_VERSION,
        'Category': CATEGORY,
        'SubCategory': 1,
    },
    'LBT2PH Cooling Recirc':{
        'NickName':'Cooling | Recirc',
        'Message': RELEASE_VERSION,
        'Category': CATEGORY,
        'SubCategory': 1,
    },
    'LBT2PH Cooling Supply Air':{
        'NickName':'Cooling | Supply Air',
        'Message': RELEASE_VERSION,
        'Category': CATEGORY,
        'SubCategory': 1,
    },
    'LBT2PH Heating Boiler':{
        'NickName':'Heating | Boiler',
        'Message': RELEASE_VERSION,
        'Category': CATEGORY,
        'SubCategory': 1,
    },
    'LBT2PH Heating HP':{
        'NickName':'Heating | HP',
        'Message': RELEASE_VERSION,
        'Category': CATEGORY,
        'SubCategory': 1,
    },
    'LBT2PH Heating HP Options':{
        'NickName':'Heating | HP Options',
        'Message': RELEASE_VERSION,
        'Category': CATEGORY,
        'SubCategory': 1,
    },
    'LBT2PH Heating Systems':{
        'NickName':'Heating / Cooling Systems',
        'Message': RELEASE_VERSION,
        'Category': CATEGORY,
        'SubCategory': 1,
    },
    #---------------------------------------------------------------------------
    # Section 02.1 | LBT--->PHPP
    'LBT2PH 2PHPP Convert LBT Model':{
        'NickName':'LBT--->PHPP',
        'Message': RELEASE_VERSION,
        'Category': CATEGORY,
        'SubCategory': 2,
    },
    'LBT2PH 2PHPP User Determined XL Obj':{
        'NickName':'PHPP UD Obj.',
        'Message': RELEASE_VERSION,
        'Category': CATEGORY,
        'SubCategory': 2,
    },
    'LBT2PH 2PHPP Setup':{
        'NickName':'PHPP Setup',
        'Message': RELEASE_VERSION,
        'Category': CATEGORY,
        'SubCategory': 2,
    },
    'LBT2PH 2PHPP Variants':{
        'NickName':'PHPP Variants',
        'Message': RELEASE_VERSION,
        'Category': CATEGORY,
        'SubCategory': 2,
    },
    #---------------------------------------------------------------------------
    # Section 03.1 | To Excel
    'LBT2PH XL Open Workbook':{
        'NickName':'Open Excel Workbook',
        'Message': RELEASE_VERSION,
        'Category': CATEGORY,
        'SubCategory': 3,
    },
    'LBT2PH XL Write to Workbook':{
        'NickName':'Write to Excel Workbook',
        'Message': RELEASE_VERSION,
        'Category': CATEGORY,
        'SubCategory': 3,
    },
    'LBT2PH XL Read from Workbook':{
        'NickName':'Read from Excel Workbook',
        'Message': RELEASE_VERSION,
        'Category': CATEGORY,
        'SubCategory': 3,
    },
}

def set_component_params(ghenv, dev=False):
    """
    Args:
        ghenv: The ghenv variable from the Component
        dev: (Default=False) If False, will use the RELEASE_VERSION value as the 
            'message' shown on the bottom of the component in the Grasshopper
            scene. If a string is passed in, will use that for the 'message'
            shown instead.
    Returns:
    """

    compo_name = ghenv.Component.Name
    sub_cat_num = component_params.get(compo_name).get('SubCategory')
    sub_cat_name = sub_catagories.get(sub_cat_num)

    #------ Set the visible message
    if dev:
        msg = 'DEV | {}'.format(str(dev))
    else:
        msg = component_params.get(compo_name).get('Message')

    ghenv.Component.Message = msg
    
    #------ Set the othere stuff
    ghenv.Component.NickName = component_params.get(compo_name).get('NickName')
    ghenv.Component.Category = CATEGORY
    ghenv.Component.SubCategory = sub_cat_name
    ghenv.Component.IconDisplayMode = ghenv.Component.IconDisplayMode.application
