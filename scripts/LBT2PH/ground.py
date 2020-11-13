import ghpythonlib.components as ghc
import rhinoscriptsyntax as rs
import json
import Grasshopper.Kernel as ghK
import random

class PHPP_Ground_Floor_Element:
      
    def __init__(self, _ghenv):
        self.ghenv = _ghenv
        self.id = random.randint(1000,9999)
        self.hb_host_room_name = None
        self.floor_area = None
        self.floor_U_value = None
        self.perim_len = None
        self.perim_psi_X_len = None
    
    def set_surface_values(self, _srfc_guids):
        """Pulls Rhino Scene parameters for a list of Surface Object Guids
        
        Takes in a list of surface GUIDs and goes to Rhino. Looks in their
        UserText to get any user applied parameter data. Will also find the
        surface area of each surface in the list. 
        
        Calculates the total surface area of all surfaces in the list, as well as
        the area-weighted U-Value of the total.
        
        Will return tuple(0, 0) on any trouble getting parameter values or any fails
        
        Parameters:
        _flrSrfcs (list): A list of Surface GUIDs to look at in the Rhino Scene
        
        Returns:
        totalFloorArea, floorUValue (tuple): The total floor area (m2) and the area weighted U-Value
        """
        
        if _srfc_guids == None:
            return 0, 0
        
        if len(_srfc_guids) > 0:
            floorAreas = []
            weightedUvales = []
            
            for srfcGUID in _srfc_guids:
                # Get the Surface Area Params
                srfcGeom = rs.coercebrep(srfcGUID)
                if srfcGeom:
                    srfcArea = ghc.Area(srfcGeom).area
                    floorAreas.append( srfcArea )
                    
                    # Get the Surface U-Values Params
                    srfcUvalue = self._get_surface_U_value(srfcGUID)
                    weightedUvales.append(srfcUvalue * srfcArea )
                else:
                    floorAreas.append( 1 )
                    weightedUvales.append( 1 )
                    
                    warning = 'Error: Input into _floor_surfaces is not a Surface?\n'\
                    'Please ensure inputs are Surface Breps only.'
                    self.ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, warning)
            
            totalFloorArea = sum(floorAreas)
            floorUValue = sum(weightedUvales) / totalFloorArea
        
        else:
            totalFloorArea = 0
            floorUValue = 0
        
        self.floor_area = totalFloorArea
        self.floor_U_value = floorUValue
    
    def set_perim_edge_values(self, _crv_guids, _ud_psi):
        """Pulls Rhino Scene parameters for a list of Curve Objects
        
        Takes in a list of curve GUIDs and goes to Rhino. Looks in their
        UserText to get any user applied parameter data.
        
        Calculates the sum of all curve lengths (m) in the list, as well as
        the total Psi-Value * Length (W/m) of all curves in the list.
        
        Will return tuple(0, 0) on any trouble getting parameter values or any fails
        
        Parameters:
        _perimCrvs (list): A list of Curve GUIDs to look at in the Rhino Scene
        
        Returns:
        totalLen, psiXlen (tuple): The total length of all curves in the list (m) and the total Psi*Len value (W/m)
        """
        
        def _getLengthIfNumber(_in, _psi):
            try:
                length = float(_in)
            except:
                length = None
            
            try:
                psi = float(_psi)
            except:
                psi = 0.05
        
            return length, psi
        
        if _crv_guids == None:
            return None

        if len(_crv_guids)==0:
            return None
        
        psiXlen = 0
        totalLen = 0
        for crvGUID in _crv_guids:                
            # See if its just Numbers passed in. If so, use them and break out
            length, crvPsiValue = _getLengthIfNumber(crvGUID, _ud_psi)
            if length and crvPsiValue:
                totalLen += length
                psiXlen += (length * crvPsiValue)
                continue
            
            isCrvGeom = rs.coercecurve(crvGUID)
            isBrepGeom = rs.coercebrep(crvGUID)
            
            if isCrvGeom:
                crvLen = ghc.Length(isCrvGeom)
                try:
                    crvPsiValue = float(_ud_psi)
                except:
                    crvPsiValue, warning = self._get_curve_psi_value(crvGUID)
                
                totalLen += crvLen
                psiXlen += (crvLen * crvPsiValue)
            elif isBrepGeom:
                srfcEdges = ghc.DeconstructBrep(isBrepGeom).edges
                srfcPerim = ghc.JoinCurves(srfcEdges, False)
                crvLen = ghc.Length(srfcPerim)
                
                try:
                    crvPsiValue = float(_ud_psi)
                except:
                    crvPsiValue = 0.05
                
                totalLen += crvLen
                psiXlen += (crvLen * crvPsiValue) # Default 0.05 W/mk
                warning = 'Note: You passed in a surface without any Psi-Values applied.\n'\
                'I will apply a default 0.5 W/mk Psi-Value to ALL the edges of the\n'\
                'surface passed in.'
                self.ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, warning)
            else:
                warning = 'Error in GROUND: Input into _exposedPerimCrvs is not a Curve or Surface?\n'\
                'Please ensure inputs are Curve / Polyline or Surface only.'
                self.ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, warning)
        
        self.perim_len = totalLen
        self.perim_psi_X_len = psiXlen
            
    def _get_curve_psi_value(self, _perimCrvGUID):
        """Takes in a single Curve GUID and returns its length and Psi*Len
        
        Will look at the UserText of the curve to get the Psi Value Type
        Name and then the Document UserText library to get the Psi-Value of the
        Type. 
        
        Returns 0.5 W/mk as default on any errors.
        
        Parameters:
        _perimCrvGUID (GUID): A single GUID 
        
        Returns:
        crvPsiValue (float): The Curve's UserText Param for 'Psi-Value' if found.
        """
        
        warning = None
        crvPsiValueName = rs.GetUserText(_perimCrvGUID, 'Typename')
        if crvPsiValueName:
            for k in rs.GetDocumentUserText():
                if 'PHPP_lib_TB' not in k:
                    continue
                
                try:
                    d = json.loads(rs.GetDocumentUserText(k))
                    if d.get('Name', None) == crvPsiValueName:
                        psiValParams = rs.GetDocumentUserText(k)
                        break
                except:
                    psiValParams = None
            else:
                psiValParams = None
            
            if psiValParams:
                psiValParams = json.loads(psiValParams)
                crvPsiValue = psiValParams.get('psiValue', 0.5)
                if crvPsiValue < 0:
                    warning = 'Warning: Negative Psi-Value found for type: "{}"\nApplying 0.0 W/mk for that edge.'.format(crvPsiValueName)
                    self.ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, warning)
                    crvPsiValue = 0
            else:   
                warning = ('Warning: Could not find a Psi-Value type in the',
                'Rhino Document UserText with the name "{}?"'.format(crvPsiValueName.upper()),
                'Check your Document UserText library to make sure that you have',
                'your most recent Thermal Bridge library file loaded?',
                'For now applying a Psi-Value of 0.5 w/mk for this edge.')
                self.ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, warning)
                crvPsiValue = 0.5
        else:
            warning = 'Warning: could not find a Psi-Value type in the\n'\
            'UserText document library for one or more edges?\n'\
            'Check your Document UserText library to make sure that you have\n'\
            'your most recent Thermal Bridge library file loaded?\n'\
            'For now applying a Psi-Value of 0.5 w/mk for this edge.'
            self.ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, warning)
            crvPsiValue = 0.5
        
        return crvPsiValue, warning
    
    def _get_surface_U_value(self, _srfcGUID):
        """Takes in a single Surface GUID and returns its U-Value Param
        
        Will look at the UserText of the surface to get the EP Construction
        Name and then the Document UserText library to get the U-Value of tha
        Construction Type. 
        
        Returns 1.0 W/m2k as default on any errors.
        
        Parameters:
        _srfcGUID (GUID): A single GUID value
        
        Returns:
        srfcUvalue (float): The Surface's UserText Param for 'U-Value' if found
        """
        
        srfcConstructionName = rs.GetUserText(_srfcGUID, 'EPConstruction')
        if srfcConstructionName:
            constParams = rs.GetDocumentUserText('PHPP_lib_Assmbly_' + srfcConstructionName)
            
            for k in rs.GetDocumentUserText():
                if 'PHPP_lib_Assmbly' not in k:
                    continue
                try:
                    d = json.loads(rs.GetDocumentUserText(k))
                    if d.get('Name', None) == srfcConstructionName:
                        constParams = rs.GetDocumentUserText(k)
                        break
                except:
                    constParams = None
            else:
                constParams = None
            
            if constParams:
                constParams = json.loads(constParams)
                srfcUvalue = constParams.get('uValue', 1)
            else:
                warning = ('Warning: Could not find a construction type in the',
                'Rhino Document UserText with the name "{}?"'.format(srfcConstructionName.upper()),
                'Check your Document UserText library to make sure that you have',
                'your most recent assembly library file loaded?',
                'For now applying a U-Value of 1.0 w/m2k for this surface.')
                self.ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, warning)
                srfcUvalue = 1.0
        else:
            warning = 'Warning: could not find a construction type in the\n'\
            'UserText for one or more surfaces? Are you sure you assigned a\n'\
            '"EPConstruction" parameter to the Floor Surface being input?\n'\
            'For now applying a U-Value of 1.0 w/m2k for this surface.'
            self.ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, warning)
            srfcUvalue = 1.0
        
        return srfcUvalue

    def to_dict(self):
        d = {}
        
        d.update( {'id':self.id} )
        d.update( {'hb_host_room_name':self.hb_host_room_name} )
        d.update( {'floor_area': self.floor_area} )
        d.update( {'floor_U_value': self.floor_U_value} )
        d.update( {'perim_len': self.perim_len} )
        d.update( {'perim_psi_X_len': self.perim_psi_X_len} )

        return d

    @classmethod
    def from_dict(cls, _dict):
        new_obj = cls()

        new_obj.id = _dict['id']
        new_obj.hb_host_room_name = _dict['hb_host_room_name']
        new_obj.floor_area = _dict['floor_area']
        new_obj.floor_U_value = _dict['floor_U_value']
        new_obj.perim_len = _dict['perim_len']
        new_obj.perim_psi_X_len = _dict['perim_psi_X_len']

        return new_obj

    def __unicode__(self):
        return u'A PHPP Ground Object: < {} >'.format(self.id)
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
       return "{}(_ghenv={!r})".format(
            self.__class__.__name__,
            self.ghenv)


class PHPP_Ground_Slab_on_Grade:
    def __init__(self, _floor_element=None,
                        _perimPsi=0.5,
                        _depth=1.0,
                        _thick=0.101,
                        _cond=0.04,
                        _orient='Vertical'):
        
        self.id = random.randint(1000,9999)
        self.Warning = None
        self.Type = '01_SlabOnGrade'
        self.soilThermalConductivity = 2.0 # MJ/m3-K
        self.soilHeatCapacity = 2.0 # W/mk
        self.groundWaterDepth = 3.0 # m
        self.groundWaterFlowrate = 0.05 # m/d 
        

        self.floor_element = _floor_element
        self.PerimPsiVal = _perimPsi
        self.perimInsulDepth = _depth
        self.perimInsulThick = _thick
        self.perimInsulConductivity = _cond
        self.perimInsulOrientation = _orient

    @property
    def name(self):
        return self.floor_element.name

    @property
    def floor_area(self):
        return self.floor_element.surface_area( self.FloorSurface )

    @property
    def floor_U_value(self):
        return self.floor_element.surface_U_value( self.FloorSurface )

    @property
    def perim_len(self):
        return self.floor_element.exposed_perim_len( self.PerimCurves )

    @property
    def perim_psi(self):
        return self.floor_element.psi_value( self.PerimCurves )

    @property
    def perim_psi_X_len(self):
        self.perim_len * self.perim_psi


    def to_dict(self):
        d ={}
        
        d.update( {'id':self.id} )
        d.update( {'floor_element':self.floor_element.to_dict() } )
        d.update( {'PerimPsiVal':self.PerimPsiVal } )
        d.update( {'perimInsulDepth':self.perimInsulDepth } )
        d.update( {'perimInsulThick':self.perimInsulThick } )
        d.update( {'perimInsulConductivity':self.perimInsulConductivity } )
        d.update( {'perimInsulOrientation':self.perimInsulOrientation } )
        
        return d

    @classmethod
    def from_dict(cls, _dict):
        new_obj = cls()
        
        new_obj.id = _dict['id']
        new_obj.floor_element( PHPP_Ground_Floor_Element.from_dict(_dict['floor_element']) ) 
        new_obj.PerimPsiVal = _dict['PerimPsiVal']
        new_obj.perimInsulDepth = _dict['perimInsulDepth']
        new_obj.perimInsulThick = _dict['perimInsulThick']
        new_obj.perimInsulConductivity = _dict['perimInsulConductivity']
        new_obj.perimInsulOrientation = _dict['perimInsulOrientation']

        return new_obj
    
    def __unicode__(self):
        return u'A PHPP Slab-On-Grade Object: < {} >'.format(self.id)
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
       return "{}(_floor_element={!r}, _hb_room_name={!r},\
            _flrSrfcs={!r}, _perimCrvs={!r}, _perimPsi={!r},\
            _depth={!r}, _thick={!r}, _cond={!r},\
            _orient='Vertical'{!r})".format(
                self.__class__.__name__,
                self.floor_element,
                self.hb_room_name,
                self.FloorSurface,
                self.PerimCurves,
                self.PerimPsiVal,
                self.perimInsulDepth,
                self.perimInsulThick,
                self.perimInsulConductivity,
                self.perimInsulOrientation)


class PHPP_Ground_Heated_Basement:
    def __init__(self, _perimCrvs=None, _perimPsi=0.5, _wallHeight_BG=1.0, _wallU_BG=1.0):
        pass


    def to_dict(self):
        d = {}

        return d

    @classmethod
    def from_dict(cls, _dict):
        new_obj = cls()

        return new_obj


class PHPP_Ground_Unheated_Basement:
    def __init__(self, _perimCrvs=None, _perimPsi=0.5, _wallHeight_AG=1.0, _wallU_AG=1.0, _wallHeight_BG=1.0, _wallU_BG=1.0, _flrU=1.0, _ach=1.0, _vol=1.0):
        pass


    def to_dict(self):
        d = {}

        return d

    @classmethod
    def from_dict(cls, _dict):
        new_obj = cls()

        return new_obj


class PHPP_Ground_Crawl_Space:
    def __init__(self, _perimCrvs=None, _perimPsi=0.5, _wallHeight=1.0, _wallU=1.0, _crawlU=1.0, _ventOpen=1.0, _windVel=4.0, _windFac=0.05):
        pass


    def to_dict(self):
        d = {}

        return d

    @classmethod
    def from_dict(cls, _dict):
        new_obj = cls()

        return new_obj
