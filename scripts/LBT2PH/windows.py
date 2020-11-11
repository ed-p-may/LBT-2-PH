import rhinoscriptsyntax as rs
import Rhino
import json
import LBT2PH.helpers
from collections import namedtuple


class PHPP_Shading_Dimensions:
    def __init__(self):
        pass
    
    @property
    def has_values(self):
        if self.h_hori and self.d_hori:
            if self.o_reveal and self.d_reveal:
                if self.o_over and self.d_over:
                    return True
        
        return False

    @property
    def h_hori(self):
        
        return None

    @property
    def d_hori(self):
        
        return None

    @property
    def o_reveal(self):
        
        return None

    @property
    def d_reveal(self):
        
        return None

    @property
    def o_over(self):
        
        return None

    @property
    def d_over(self):
        
        return None


class PHPP_Window:
    '''  Class to organize data for a 'window'.
    Args:
        _aperture: A LadybugTools 'aperture' object
        _params: <dict> A dict with a 'phpp' key and parameter values
        _rh_doc_library: The Rhino document window library from the document UserText
    Properties:
        * quantity
        * _tolerance
        * aperture
        * params
        * rh_library
    '''
    
    def __init__(self, _aperture=None, _params=None, _rh_doc_library=None):
        self.quantity = 1
        self._tolerance = 0.01
        self.aperture = _aperture
        self.params = _params
        self.rh_library = _rh_doc_library
        self._shading_dimensions = None
        self._shading_factor_winter = None
        self._shading_factor_summer = None
    
    @property
    def name(self):
        nm = self.params.get('Object Name', None)
        if nm is None:
            nm = self.aperture.display_name 
        return nm

    @property
    def frame(self):      
        # 1) Try and create glazing from user_data params
        # 2) Try and create glazing from UserText params
        # 3) If all fails, return a default Frame object
        
        frame_val = (self.params.get('FrameType', None))
        try:
            d = json.loads( frame_val )
            nm = d['_nm']
            uValues = d['_uValues']
            frameWidths = d['_frameWidths']
            psiGlazings = d['_psiGlazings']
            psiInstalls = d['_psiInstalls']
            chiGlassCarrier = d['_chiGlassCarrier']

            frame_object = PHPP_Frame(nm, uValues, frameWidths, psiGlazings, psiInstalls, chiGlassCarrier)
            return frame_object
        except:
            frame_object = self.rh_library['lib_FrameTypes'].get(frame_val, None )
            
            if frame_object:
                return frame_object
            else:
                # Since no PHPP params, use the EP/HB Construction values
                nm = self.aperture.properties.energy.construction.display_name
                uVal = self.aperture.properties.energy.construction.u_factor

            if nm and uVal:
                frame =  PHPP_Frame(_nm=nm, _uValues=[uVal]*4, _frameWidths=[0.1]*4,
                                    _psiGlazings=[0]*4, _psiInstalls=[0]*4)
                return frame
            else:
                return PHPP_Frame()

    @property
    def glazing(self):
        # 1) Try and create glazing from user_data params
        # 2) Try and create glazing from UserText params
        # 3) If all fails, return a default Glazing object

        glazing_val = (self.params.get('GlazingType', None))
        try:
            d = json.loads( glazing_val )
            nm = d['_nm']
            gVal = d['_gValue']
            uVal = d['_uValue']
            
            glazing_object = PHPP_Glazing(nm, gVal, uVal)
            return glazing_object
        except:
            glazing_object = self.rh_library['lib_GlazingTypes'].get(glazing_val, None )
            
            if glazing_object:
                return glazing_object
            else:
                # Since no PHPP params, use the EP/HB Construction values
                nm = self.aperture.properties.energy.construction.display_name
                uVal = self.aperture.properties.energy.construction.u_factor

                if nm and uVal:
                    return PHPP_Glazing(_nm=nm, _gValue=0.4, _uValue=uVal)        
                else:
                    return PHPP_Glazing()
  
    @property
    def window_edges(self):
        window_left, window_right = self.aperture.geometry.get_left_right_vertical_edges(self._tolerance)
        window_top, window_bottom = self.aperture.geometry.get_top_bottom_horizontal_edges(self._tolerance)
        
        Output = namedtuple('Output', ['Left', 'Right', 'Bottom', 'Top'])
        return Output(window_left, window_right, window_bottom, window_top)

    @property
    def glazing_edge_lengths(self):
        glazing_Left = self.window_edges.Left.length - self.frame.fTop - self.frame.fBottom
        glazing_Right = self.window_edges.Right.length - self.frame.fTop - self.frame.fBottom
        glazing_Bottom = self.window_edges.Bottom.length - self.frame.fLeft - self.frame.fRight
        glazing_Top = self.window_edges.Top.length - self.frame.fLeft - self.frame.fRight
        
        Output = namedtuple('Output', ['Left', 'Right', 'Bottom', 'Top'])
        return Output(glazing_Left, glazing_Right, glazing_Bottom, glazing_Top)

    @property
    def installs(self):
        def _str_to_bool(_):
            try:
                return int(_)
            except:
                if 'FALSE' == str(_).upper():
                    return 0
                return 1

        left = _str_to_bool(self.params.get('InstallLeft', 1))
        right = _str_to_bool(self.params.get('InstallRight', 1))
        bottom = _str_to_bool(self.params.get('InstallBottom', 1))
        top = _str_to_bool(self.params.get('InstallTop', 1))
        
        Output = namedtuple('Output', ['Left', 'Right', 'Bottom', 'Top'])
        return Output(left, right, bottom, top)

    @property
    def u_w_installed(self):
        frame = self.frame
        glazing_edge_lens = self.glazing_edge_lengths
        window_edges = self.window_edges
        window_area = self.aperture.area
        glazing_area = glazing_edge_lens.Left * glazing_edge_lens.Bottom
        
        # Correct for the corner overlap
        corner_areas = []
        corner_areas.append(frame.fLeft * frame.fTop + frame.fLeft * frame.fBottom)
        corner_areas.append(frame.fRight* frame.fTop + frame.fRight * frame.fBottom)
        corner_areas.append(frame.fLeft * frame.fBottom + frame.fRight * frame.fBottom)
        corner_areas.append(frame.fLeft* frame.fTop + frame.fRight * frame.fTop)
        frame_areas = [(e.length*w)-(0.5*ca) for e, w, ca in zip(window_edges, frame.frameWidths, corner_areas)]

        # Calc the heat-loss values for all the elements
        hl_glazing = glazing_area * self.glazing.uValue
        hl_frames = sum([a*u for a, u in zip(frame_areas, frame.uValues)])
        hl_glazing_edge = sum([e_len*psi_g for e_len, psi_g in zip(glazing_edge_lens, frame.PsiGVals)])
        hl_install_edge = sum([e.length*psi_i*i for e, psi_i, i in zip(window_edges, frame.PsiInstalls, self.installs)])
        
        u_w_installed = (hl_glazing + hl_frames + hl_glazing_edge + hl_install_edge) / window_area
        
        return u_w_installed
    
    @property
    def host_surface(self):
        return self.aperture.parent.display_name.replace('EXT_', '')

    @property
    def height(self):
        left, right = self.aperture.geometry.get_left_right_vertical_edges(self._tolerance)
        return left.length

    @property
    def width(self):
        top, bottom = self.aperture.geometry.get_top_bottom_horizontal_edges(self._tolerance)
        return top.length

    @property
    def shading_dimension_simple(self):
        if self._shading_dimensions:
            return self._shading_dimensions
        else:
            return PHPP_Shading_Dimensions()

    @property
    def shading_factor_winter(self):
        try:
            return float(self._shading_factor_winter)
        except Exception as e:
            return 0.75

    @property
    def shading_factor_summer(self):
        try:
            return float(self._shading_factor_winter)
        except Exception as e:
            return 0.75

    @property
    def reveal_geometry(self):
        #
        #
        # TODO
        #
        #


        return [-1]

    @property
    def inset_window_surface(self):
        #
        #
        # TODO
        #
        #
        return -1

    def to_dict(self):
        d = {}
        d.update( {'quantity':self.quantity} )
        d.update( {'_tolerance':self._tolerance} )
        d.update( {'aperture':self.aperture} )
        d.update( {'params':self.params} )
        d.update( {'rh_library':self.rh_library} )
        d.update( {'_shading_dimensions':self._shading_dimensions} )
        d.update( {'_shading_factor_winter':self._shading_factor_winter } )
        d.update( {'_shading_factor_summer':self._shading_factor_summer} )
        
        return d

    @classmethod
    def from_dict(cls, _dict):
        
        new_obj = cls()
        new_obj.quantity = _dict['quantity']
        new_obj._tolerance = _dict['_tolerance']
        new_obj.aperture= _dict['aperture']
        new_obj.params = _dict['params']
        new_obj.rh_library =_dict['rh_library']
        new_obj._shading_dimensions =_dict['_shading_dimensions']
        new_obj._shading_factor_winter =_dict['_shading_factor_winter']
        new_obj._shading_factor_summer =_dict['_shading_factor_summer']
        
        return new_obj

    def __unicode__(self):
        return u'A PHPP-Style Window Object: < {} >'.format(self.name)
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
       return "{}( _aperture={!r}, _params={!r}, _rh_doc_library={!r})".format(
            self.__class__.__name__,
            self.aperture,
            self.params,
            self.rh_library)

class PHPP_Frame:
    ''' For Storing PHPP Style Frame Parameters       
     Args:
        _nm (str): The name of the Frame Type
        _uValues (list): A list of the 4 U-Values (W/m2k) for the frame sides (Left, Right, Bottom, Top)
        _frameWidths (list): A list of the 4 U-Values (W/m2k) for the frame sides (Left, Right, Bottom, Top)
        _psiGlazings (list): A list of the 4 Psi-Values (W/mk) for the glazing spacers (Left, Right, Bottom, Top)
        _psiInstalls (list): A list of the 4 Psi-Values (W/mk) for the frame Installations (Left, Right, Bottom, Top)
        _chiGlassCarrier (list): A value for the Chi-Value (W/k) of the glass carrier for curtain walls
    '''
    
    def __init__(self, 
                _nm='Default Frame',
                _uValues=[1.0]*4,
                _frameWidths=[0.1]*4,
                _psiGlazings=[0.04]*4,
                _psiInstalls=[0.04]*4,
                _chiGlassCarrier=None):

        self.name = _nm
        self._uValues = _uValues
        self.frameWidths = _frameWidths
        self.PsiGVals = _psiGlazings
        self.PsiInstalls = _psiInstalls
        self.chiGlassCarrier = _chiGlassCarrier
        
        self.cleanAttrSet(['uLeft', 'uRight', 'uBottom', 'uTop'], self.uValues)
        self.cleanAttrSet(['fLeft', 'fRight', 'fBottom', 'fTop'], self.frameWidths)
        self.cleanAttrSet(['psigLeft', 'psigRight', 'psigBottom', 'psigTop'], self.PsiGVals)
        self.cleanAttrSet(['psiInstLeft', 'psiInstRight', 'psiInstBottom', 'psiInstTop'], self.PsiInstalls)
    
    @property
    def uValues(self):
        if self._uValues is None:
            return [0.1]*4
        
        if len(self._uValues) == 4:
            return self._uValues
        else:
            return [self._uValues]*4

    @property
    def display_name(self):
        nm = self.name
        nm = nm.replace('PHPP_CONST_', '')
        nm = nm.replace('PHPP_MAT_', '')
        return nm

    def cleanAttrSet(self, _inList, _attrList):
        # In case the input len != 4 and convert to float values
        if len(_attrList) != 4:
            try:
                val = float(_attrList[0])
            except:
                val = _attrList[0]
            
            for each in _inList:
                setattr(self, each, val)
        else:
            for i, each in enumerate(_inList):
                try:
                    val = float(_attrList[i])
                except:
                    val = _attrList[i]
                
                setattr(self, _inList[i], val)
    
    def to_dict(self):
        d = {}
        d['class'] = self.__class__.__name__
        d['_nm'] = self.name
        d['_uValues'] = self._uValues
        d['_frameWidths'] = self.frameWidths
        d['_psiGlazings'] = self.PsiGVals
        d['_psiInstalls'] = self.PsiInstalls
        d['_chiGlassCarrier'] = self.chiGlassCarrier
        
        return d
    
    def __unicode__(self):
        return u'A PHPP Style Frame Object: < {self.name} >'.format(self=self)
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
       return "{}( _nm={!r}, _uValues={!r}, _frameWidths={!r}, _psiGlazings={!r}, "\
              "_psiInstalls={!r}, _chiGlassCarrier={!r} )".format(
               self.__class__.__name__,
               self.name,
               self.uValues,
               self.frameWidths,
               self.PsiGVals,
               self.PsiInstalls,
               self.chiGlassCarrier )

class PHPP_Glazing:
    """ For storing PHPP Style Glazing Parameters """
    
    def __init__(self, _nm='Default Glazing', _gValue=0.4, _uValue=1.0):
        """
        Args:
            _nm (str): The name of the glass type
            _gValue (float): The g-Value (SHGC) value of the glass only as per EN 410 (%)
            _uValue (float): The Thermal Trasmittance value of the center of glass (W/m2k) as per EN 673
        """

        self.name = _nm
        self._gValue = _gValue
        self._uValue = _uValue
    
    @property
    def gValue(self):
        try:
            return float(self._gValue)
        except:
            return None
    
    @property
    def uValue(self):
        try:
            return float(self._uValue)
        except:
            return None
    
    @property
    def display_name(self):
        nm = self.name
        nm = nm.replace('PHPP_CONST_', '')
        nm = nm.replace('PHPP_MAT_', '')
        return nm

    def to_dict(self):
        d = {}
        d['class'] = self.__class__.__name__
        d['_nm'] = self.display_name
        d['_gValue'] = self.gValue
        d['_uValue'] = self.uValue
        
        return d

    def __unicode__(self):
        return u'A PHPP Style Glazing Object: < {} >'.format(self.display_name)
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
       return "{}( _nm={!r}, _gValue={!r}, _uValue={!r} )".format(
               self.__class__.__name__,
               self.display_name,
               self.gValue,
               self.uValue)

class PHPP_Installs:
    """ For storing the install conditions (0|1) of each edge in a window component """
    
    def __init__(self, _installs=[1]*4):
        """
        Args:
            _installs (list): A list of four 'install' types (Left, Right, Bottom, Top)
        """
        self.Installs = _installs
        self.setInstalls()
        
    def setInstalls(self):
        # In case the number of installs passed != 4, use the first one for all of them
        if len(self.Installs) != 4:
            self.Inst_L = float(self.Installs[0]) if self.Installs[0] != None else 'Auto'
            self.Inst_R = float(self.Installs[0]) if self.Installs[0] != None else 'Auto'
            self.Inst_B = float(self.Installs[0]) if self.Installs[0] != None else 'Auto'
            self.Inst_T = float(self.Installs[0]) if self.Installs[0] != None else 'Auto'
        else:
            self.Inst_L = float(self.Installs[0]) if self.Installs[0] != None else 'Auto'
            self.Inst_R = float(self.Installs[1]) if self.Installs[1] != None else 'Auto'
            self.Inst_B = float(self.Installs[2]) if self.Installs[2] != None else 'Auto'
            self.Inst_T = float(self.Installs[3]) if self.Installs[3] != None else 'Auto'
    
    @property
    def values_as_list(self):
        return [int(self.Inst_L), int(self.Inst_R), int(self.Inst_B), int(self.Inst_T)]
    
    @property
    def values(self):
        Output = namedtuple('Output', ['Left', 'Right', 'Bottom', 'Top'])
        return Output(self.Inst_L, self.Inst_R, self.Inst_B, self.Inst_T)

    def __unicode__(self):
        return u'A PHPP Style Window Install Object: < L={self.Inst_L} | R={self.Inst_R} | T={self.Inst_T} | B={self.Inst_B} >'.format(self=self)
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
       return "{}( _installs={!r} )".format(
               self.__class__.__name__, self.Installs)

def create_EP_window_mat(_win_obj):
    """ Creates an E+ style material for the window based on the PHPP U-W-Installed

    Args:
        _win_obj (): The PHPP-Style window object
    Returns:
        mat: The window E+ Material
    
    """
    try:  # import the core honeybee dependencies
        from honeybee.typing import clean_and_id_ep_string
    except ImportError as e:
        raise ImportError('\nFailed to import honeybee:\n\t{}'.format(e))

    try:  # import the honeybee-energy dependencies
        from honeybee_energy.material.glazing import EnergyWindowMaterialSimpleGlazSys
    except ImportError as e:
        raise ImportError('\nFailed to import honeybee_energy:\n\t{}'.format(e))

    # Material properties
    name = 'PHPP_MAT_{}'.format(_win_obj.name)
    u_factor = _win_obj.u_w_installed
    shgc = _win_obj.glazing.gValue
    t_vis = 0.6

    # Create the material
    mat = EnergyWindowMaterialSimpleGlazSys(
        clean_and_id_ep_string(name), u_factor, shgc, t_vis)
    mat.display_name = name

    return mat

def create_EP_const(_win_EP_material):
    """ Creates an 'E+' style construction for the window

    Args:
        _win_EP_material (): The E+ Material for the window
    Returns:
        constr (): The new E+ Construction for the window
    """

    try:  # import the core honeybee dependencies
        from honeybee.typing import clean_and_id_ep_string
    except ImportError as e:
        raise ImportError('\nFailed to import honeybee:\n\t{}'.format(e))

    try:  # import the honeybee-energy dependencies
        from honeybee_energy.construction.window import WindowConstruction
        from honeybee_energy.lib.materials import window_material_by_identifier
    except ImportError as e:
        raise ImportError('\nFailed to import honeybee_energy:\n\t{}'.format(e))
    
    material_objs = []
    for material in [_win_EP_material]:
        if isinstance(material, str):
            material = window_material_by_identifier(material)
        material_objs.append(material)
    
    name = 'PHPP_CONST_{}'.format(_win_EP_material.display_name)

    constr = WindowConstruction(clean_and_id_ep_string(name), material_objs)
    constr.display_name = name

    return constr

def get_rh_doc_window_library(_ghdoc):
    """ Loads window-type entries from DocumentUseText library of the Active Rhino doc.

        Note, it determines if its a 'window-type' entry by looking for the 
        string "PHPP_lib_Glazing", "PHPP_lib_Frame" or "_PsiInstall_" in the key
         
    Args:
        _ghdoc (ghdoc): The 'ghdoc' object from the Grasshopper document.
    Returns:
        PHPPLibrary_ (dict): A dictionary of all the window-type entries
            found with their parameters.
    """
    
    PHPPLibrary_ = {}
    lib_GlazingTypes = {}
    lib_FrameTypes = {}
    lib_PsiInstalls = {}

    with LBT2PH.helpers.context_rh_doc(_ghdoc):
        # First, try and pull in the Rhino Document's PHPP Library
        # And make new Frame and Glass Objects. Add all of em' to new dictionaries
        if not rs.IsDocumentUserText():
            return PHPPLibrary_
        
        for eachKey in rs.GetDocumentUserText():
            if 'PHPP_lib_Glazing' in eachKey:
                tempDict = json.loads(rs.GetDocumentUserText(eachKey))
                newGlazingObject = PHPP_Glazing(
                                tempDict['Name'],
                                tempDict['gValue'],
                                tempDict['uValue']
                                )
                lib_GlazingTypes[tempDict['Name']] = newGlazingObject
            elif '_PsiInstall_' in eachKey:
                tempDict = json.loads(rs.GetDocumentUserText(eachKey))
                newPsiInstallObject = PHPP_Installs(
                                [
                                tempDict['Left'],
                                tempDict['Right'],
                                tempDict['Bottom'],
                                tempDict['Top']
                                ]
                                )
                lib_PsiInstalls[tempDict['Typename']] = newPsiInstallObject
            elif 'PHPP_lib_Frame' in eachKey:
                tempDict = json.loads(rs.GetDocumentUserText(eachKey))
                newFrameObject = PHPP_Frame(
                                tempDict['Name'],
                                [
                                tempDict['uFrame_L'],
                                tempDict['uFrame_R'],
                                tempDict['uFrame_B'],
                                tempDict['uFrame_T']
                                ],
                                [
                                tempDict['wFrame_L'],
                                tempDict['wFrame_R'],
                                tempDict['wFrame_B'],
                                tempDict['wFrame_T']
                                ],
                                [
                                tempDict['psiG_L'],
                                tempDict['psiG_R'],
                                tempDict['psiG_B'],
                                tempDict['psiG_T']
                                ],
                                [
                                tempDict['psiInst_L'],
                                tempDict['psiInst_R'],
                                tempDict['psiInst_B'],
                                tempDict['psiInst_T']
                                ]
                                )
                lib_FrameTypes[tempDict['Name']] = newFrameObject
        
        PHPPLibrary_['lib_GlazingTypes'] = lib_GlazingTypes
        PHPPLibrary_['lib_FrameTypes'] = lib_FrameTypes
        PHPPLibrary_['lib_PsiInstalls'] = lib_PsiInstalls
    
    return PHPPLibrary_

def get_rh_obj_usertext(_guid):
    """ Get the UserText dictionary for a Rhino Object 
    
    Args:
        _guid (Guid): The Rhino Guid of the object
    Returns:
        user_text_dict (dict): A dictionary of all the key:value pairs found
            in the UserText dictionary
    """
    
    if _guid is None: return {}

    rh_obj = Rhino.RhinoDoc.ActiveDoc.Objects.Find( _guid )
    user_text_dict = {k:rs.GetUserText(rh_obj, k) for k in rs.GetUserText(rh_obj)}
    
    return user_text_dict

def get_rh_window_obj_params(_ghdoc, _window_guid):
    """ Get any Rhino-side parameter data for the Window

    Note: this only works in Rhino v6.0+ I believe...
    
    Args:
        _ghdoc (ghdoc): The 'ghdoc' object from the Grasshopper document.
        _window_guid (Rhino Guid): The Rhino Guid of the window.
    Returns:
        window_rh_params_dict (dict): A dictionary of all the data found
            in the Rhino object's UserText library.
    """
    
    with LBT2PH.helpers.context_rh_doc(_ghdoc):
        window_rh_params_dict = get_rh_obj_usertext(_window_guid)
        
        # Fix the name
        window_name = rs.ObjectName(_window_guid)
        window_rh_params_dict['Object Name'] = window_name

    return window_rh_params_dict