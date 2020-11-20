import ghpythonlib.components as ghc
import rhinoscriptsyntax as rs
import json
import Grasshopper.Kernel as ghK
import random
from ladybug_rhino.fromgeometry import from_face3d 

class PHPP_Ground_Floor_Element:
    """ A 'Floor' surface element for a ground object """

    def __init__(self, _ghenv):
        self.default_perim_psi = 0.5 #W/mk
        self.ghenv = _ghenv
        self.id = random.randint(1000,9999)
        self.hb_host_room_name = None
        self.floor_area = None
        self.floor_U_value = None
        self.perim_len = None
        self.perim_psi_X_len = None
    
    def set_values_by_hb_room(self, _hb_room ):
        """ Finds the Floor-Type face(s) in a Honeybee Room and gets Params
        
        Resets self.floor_area and self.floor_U_value based on the values found in
        the Honeybee Zone. If more than one Floor face is found, creates a 
        weighted U-Value average of all the faces.
        
        Args:
            self:
            _hb_room: A Single Honeybee Room object
        Returns:
            None
        """
        def is_floor(_face):
            if str(face.type) != 'Floor':
                return False
            if str(face.boundary_condition) != 'Ground' and str(face.boundary_condition) != 'Outdoors':
                return False
            return True
        
        #-----------------------------------------------------------------------
        # Get all the data from the HB-Room Floor surfaces
        floor_areas = []
        area_weighted_u_values = []
        perim_curve_lengths = []
        for face in _hb_room:
            if not is_floor(face):
                continue
            
            u_floor =  face.properties.energy.construction.u_factor
            floor_areas.append( face.area )
            area_weighted_u_values.append( u_floor * face.area )
            
            face_surface = from_face3d( face.geometry )
            perim_curve = ghc.JoinCurves(list(face_surface.DuplicateEdgeCurves()), False)
            perim_curve_lengths.append( ghc.Length( perim_curve ) )

        #-----------------------------------------------------------------------
        # Set the Floor Element params
        if floor_areas and area_weighted_u_values:
            self.floor_area = sum(floor_areas)
            self.floor_U_value = sum(area_weighted_u_values) / sum(floor_areas)
            self.perim_len = sum( perim_curve_lengths )

    def set_surface_values(self, _srfc_guids):
        """Pulls Rhino Scene parameters for a list of Surface Object Guids
        
        Takes in a list of surface GUIDs and goes to Rhino. Looks in their
        UserText to get any user applied parameter data. Will also find the
        surface area of each surface in the list. 
        
        Calculates the total surface area of all surfaces in the list, as well as
        the area-weighted U-Value of the total.
        
        Will return tuple(0, 0) on any trouble getting parameter values or any fails
        
        Args:
            self:
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
        
        Args:
            self:
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
                psi = self.default_perim_psi
        
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
                    crvPsiValue = self.default_perim_psi # Default 0.05 W/mk
                    warning = 'Note: You passed in a surface without any Psi-Values applied.\n'\
                    'I will apply a default {} W/mk Psi-Value to ALL the edges of the\n'\
                    'surface passed in.'.format( self.default_perim_psi )
                    self.ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, warning)
                
                totalLen += crvLen
                psiXlen += (crvLen * crvPsiValue)
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
        
        Args:
            self:
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
                crvPsiValue = psiValParams.get('psiValue', self.default_perim_psi)
                if crvPsiValue < 0:
                    warning = 'Warning: Negative Psi-Value found for type: "{}"\nApplying 0.0 W/mk for that edge.'.format(crvPsiValueName)
                    self.ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, warning)
                    crvPsiValue = 0
            else:   
                warning = ('Warning: Could not find a Psi-Value type in the',
                'Rhino Document UserText with the name "{}?"'.format(crvPsiValueName.upper()),
                'Check your Document UserText library to make sure that you have',
                'your most recent Thermal Bridge library file loaded?',
                'For now applying a Psi-Value of {} w/mk for this edge.'.format(self.default_perim_psi))
                self.ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, warning)
                crvPsiValue = self.default_perim_psi
        else:
            warning = 'Warning: could not find a Psi-Value type in the\n'\
            'UserText document library for one or more edges?\n'\
            'Check your Document UserText library to make sure that you have\n'\
            'your most recent Thermal Bridge library file loaded?\n'\
            'For now applying a Psi-Value of {} w/mk for this edge.'.format(self.default_perim_psi)
            self.ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, warning)
            crvPsiValue = self.default_perim_psi
        
        return crvPsiValue, warning
    
    def _get_surface_U_value(self, _srfcGUID):
        """Takes in a single Surface GUID and returns its U-Value Param
        
        Will look at the UserText of the surface to get the EP Construction
        Name and then the Document UserText library to get the U-Value of tha
        Construction Type. 
        
        Returns 1.0 W/m2k as default on any errors.
        
        Args:
            self:
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
    def from_dict(cls, _dict, _ghenv):
        new_obj = cls(_ghenv)

        new_obj.id = _dict.get('id')
        new_obj.hb_host_room_name = _dict.get('hb_host_room_name')
        new_obj.floor_area = _dict.get('floor_area')
        new_obj.floor_U_value = _dict.get('floor_U_value')
        new_obj.perim_len = _dict.get('perim_len')
        new_obj.perim_psi_X_len = _dict.get('perim_psi_X_len')

        return new_obj

    def __unicode__(self):
        return u'A PHPP Ground Floor Element: < {} >'.format(self.id)
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
       return "{}(_ghenv={!r})".format(
            self.__class__.__name__,
            self.ghenv)


class PHPP_Ground():
    """ General 'getters' common to all Ground classes """
    
    @property
    def host_room_name(self):
        return self.floor_element.hb_host_room_name

    @property
    def floor_area(self):
        return self.floor_element.floor_area

    @property
    def floor_U_value(self):
        return self.floor_element.floor_U_value

    @property
    def perim_len(self):
        return self.floor_element.perim_len

    @property
    def perim_psi(self):
        try: 
            return float(self.PerimPsiVal)
        except:
            if self.perim_len:
                return float(self.floor_element.default_perim_psi)
            else:
                return None

    @property
    def perim_psi_X_len(self):
        try:
            return float( self.perim_len * self.perim_psi)
        except TypeError as e:
            return None
    
    def __unicode__(self):
        return u'A PHPP Ground Element: < {} >'.format(self.id)
    def __str__(self):
        return unicode(self).encode('utf-8')


class PHPP_Ground_Slab_on_Grade( PHPP_Ground ):
    def __init__(self, _floor_element=None, _perimPsi=0.5, _depth=1.0, 
                        _thick=0.1, _cond=0.04, _orient='Vertical'):
        
        self.id = random.randint(1000,9999)
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

    def to_dict(self):
        d ={}
        
        d.update( {'id':self.id} )
        d.update( {'type': self.Type} )
        d.update( {'floor_element':self.floor_element.to_dict() } )
        d.update( {'PerimPsiVal':self.PerimPsiVal } )
        d.update( {'perimInsulDepth':self.perimInsulDepth } )
        d.update( {'perimInsulThick':self.perimInsulThick } )
        d.update( {'perimInsulConductivity':self.perimInsulConductivity } )
        d.update( {'perimInsulOrientation':self.perimInsulOrientation } )
        
        return d

    @classmethod
    def from_dict(cls, _dict, _ghenv):
        new_obj = cls()
        
        new_obj.id = _dict.get('id')
        floor_element = PHPP_Ground_Floor_Element.from_dict(_dict.get('floor_element'), _ghenv)
        new_obj.floor_element = floor_element
        new_obj.PerimPsiVal = _dict.get('PerimPsiVal')
        new_obj.perimInsulDepth = _dict.get('perimInsulDepth')
        new_obj.perimInsulThick = _dict.get('perimInsulThick')
        new_obj.perimInsulConductivity = _dict.get('perimInsulConductivity')
        new_obj.perimInsulOrientation = _dict.get('perimInsulOrientation')

        return new_obj

    def __unicode__(self):
        return u'A PHPP Ground Slab-On-Grade Object: < {} >'.format(self.id)
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
       return "{}(_floor_element={!r}, _perimPsi={!r},, _depth={!r},"\
                        "_thick={!r},, _cond={!r}, _orient={!r},)".format(
            self.__class__.__name__,
            self.floor_element,
            self.PerimPsiVal,
            self.perimInsulDepth,
            self.perimInsulThick,
            self.perimInsulConductivity,
            self.perimInsulOrientation)


class PHPP_Ground_Heated_Basement( PHPP_Ground ):
    def __init__(self, _floor_element=None, _perimPsi=0.5,
                        _wallHeight_BG=1.0, _wallU_BG=1.0):
        
        self.id = random.randint(1000,9999)
        self.Type = '02_HeatedBasement'
        self.soilThermalConductivity = 2.0 # MJ/m3-K
        self.soilHeatCapacity = 2.0 # W/mk
        self.groundWaterDepth = 3.0 # m
        self.groundWaterFlowrate = 0.05 # m/d 
        
        self.floor_element = _floor_element
        self.PerimPsiVal = _perimPsi
        self.WallHeight_BG = _wallHeight_BG
        self.WallU_BG = _wallU_BG

    def to_dict(self):
        d = {}

        d.update( {'id':self.id} )
        d.update( {'type': self.Type} )
        d.update( {'floor_element':self.floor_element.to_dict() } )
        d.update( {'PerimPsiVal':self.PerimPsiVal } )
        d.update( {'WallHeight_BG':self.WallHeight_BG } )
        d.update( {'WallU_BG':self.WallU_BG } )
        
        return d

    @classmethod
    def from_dict(cls, _dict, _ghenv):
        new_obj = cls()
        
        new_obj.id = _dict.get('id')
        floor_element = PHPP_Ground_Floor_Element.from_dict(_dict.get('floor_element'), _ghenv)
        new_obj.floor_element = floor_element
        new_obj.PerimPsiVal = _dict.get('PerimPsiVal')
        new_obj.WallHeight_BG = _dict.get('WallHeight_BG')
        new_obj.WallU_BG = _dict.get('WallU_BG')

        return new_obj

    def __unicode__(self):
        return u'A PHPP Ground Heated Basement Object: < {} >'.format(self.id)
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
       return "{}(_floor_element={!r}, _perimPsi={!r},"\
                        "_wallHeight_BG={!r}, _wallU_BG={!r})".format(
            self.__class__.__name__,
            self.floor_element,
            self.PerimPsiVal,
            self.WallHeight_BG,
            self.WallU_BG)


class PHPP_Ground_Unheated_Basement( PHPP_Ground ):
    def __init__(self, _floor_element=None, _perimPsi=0.5, _wallHeight_AG=1.0,
                        _wallU_AG=1.0, _wallHeight_BG=1.0, _wallU_BG=1.0, 
                        _flrU=1.0, _ach=1.0, _vol=1.0):
        
        self.id = random.randint(1000,9999)
        self.Type = '03_UnheatedBasement'
        self.soilThermalConductivity = 2.0 # MJ/m3-K
        self.soilHeatCapacity = 2.0 # W/mk
        self.groundWaterDepth = 3.0 # m
        self.groundWaterFlowrate = 0.05 # m/d 
        
        self.floor_element = _floor_element        
        self.PerimPsiVal = _perimPsi
        self.WallHeight_AG = _wallHeight_AG
        self.WallU_AG = _wallU_AG  
        self.WallHeight_BG = _wallHeight_BG
        self.WallU_BG = _wallU_BG
        self.FloorU = _flrU
        self.ACH = _ach
        self.Volume = _vol

    def to_dict(self):
        d = {}

        d.update( {'id':self.id} )
        d.update( {'type': self.Type} )
        d.update( {'floor_element':self.floor_element.to_dict() } )
        d.update( {'PerimPsiVal':self.PerimPsiVal } )
        d.update( {'WallHeight_BG':self.WallHeight_BG } )
        d.update( {'WallU_BG':self.WallU_BG } )
        d.update( {'WallHeight_AG':self.WallHeight_AG } )
        d.update( {'WallU_AG':self.WallU_AG } )
        d.update( {'FloorU':self.FloorU } )
        d.update( {'ACH':self.ACH } )
        d.update( {'Volume':self.Volume } )

        return d

    @classmethod
    def from_dict(cls, _dict, _ghenv):
        new_obj = cls()

        new_obj.id = _dict.get('id')
        floor_element = PHPP_Ground_Floor_Element.from_dict(_dict.get('floor_element'), _ghenv)
        new_obj.floor_element = floor_element
        new_obj.PerimPsiVal = _dict.get('PerimPsiVal')
        new_obj.WallHeight_BG = _dict.get('WallHeight_BG')
        new_obj.WallU_BG = _dict.get('WallU_BG')
        new_obj.WallHeight_AG = _dict.get('WallHeight_AG')
        new_obj.WallU_AG = _dict.get('WallU_AG')
        new_obj.FloorU = _dict.get('FloorU')
        new_obj.ACH = _dict.get('ACH')
        new_obj.Volume = _dict.get('Volume')

        return new_obj
    
    def __unicode__(self):
        return u'A PHPP Ground Un-heated Basement Object: < {} >'.format(self.id)
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
       return "{}( _floor_element={!r}, _perimPsi={!r}, _wallHeight_AG={!r},"\
                        "_wallU_AG={!r}, _wallHeight_BG={!r}, _wallU_BG={!r},"\
                        "_flrU={!r}, _ach={!r}, _vol={!r})".format(
                self.__class__.__name__,
                self.floor_element,        
                self.PerimPsiVal,
                self.WallHeight_AG,
                self.WallU_AG,
                self.WallHeight_BG,
                self.WallU_BG,
                self.FloorU,
                self.ACH,
                self.Volume)


class PHPP_Ground_Crawl_Space( PHPP_Ground ):
    def __init__(self, _floor_element=None, _perimPsi=0.5, _wallHeight=1.0, _wallU=1.0,
                    _crawlU=1.0, _ventOpen=1.0, _windVel=4.0, _windFac=0.05):
        
        self.id = random.randint(1000,9999)
        self.Type = '04_SuspenedFlrOverCrawl'
        self.soilThermalConductivity = 2.0 # MJ/m3-K
        self.soilHeatCapacity = 2.0 # W/mk
        self.groundWaterDepth = 3.0 # m
        self.groundWaterFlowrate = 0.05 # m/d 
        
        self.floor_element = _floor_element
        self.PerimPsiVal = _perimPsi
        self.WallHeight = _wallHeight
        self.WallU = _wallU
        self.CrawlU = _crawlU
        self.VentOpeningArea = _ventOpen
        self.windVelocity = _windVel
        self.windFactor = _windFac

    def to_dict(self):
        d = {}

        d.update( {'id':self.id} )
        d.update( {'type': self.Type} )
        d.update( {'floor_element':self.floor_element.to_dict() } )
        d.update( {'PerimPsiVal':self.PerimPsiVal } )
        d.update( {'WallHeight':self.WallHeight } )
        d.update( {'WallU':self.WallU } )
        d.update( {'CrawlU':self.CrawlU } )
        d.update( {'VentOpeningArea':self.VentOpeningArea } )
        d.update( {'windVelocity':self.windVelocity } )
        d.update( {'windFactor':self.windFactor } )

        return d

    @classmethod
    def from_dict(cls, _dict, _ghenv):
        new_obj = cls()

        new_obj.id = _dict.get('id')
        floor_element = PHPP_Ground_Floor_Element.from_dict(_dict.get('floor_element'), _ghenv)
        new_obj.floor_element = floor_element
        new_obj.PerimPsiVal = _dict.get('PerimPsiVal')
        new_obj.WallHeight = _dict.get('WallHeight')
        new_obj.WallU = _dict.get('WallU')
        new_obj.CrawlU = _dict.get('CrawlU')
        new_obj.VentOpeningArea = _dict.get('VentOpeningArea')
        new_obj.windVelocity = _dict.get('windVelocity')
        new_obj.windFactor = _dict.get('windFactor')

        return new_obj
    
    def __unicode__(self):
        return u'A PHPP Ground Crawl-Space Object: < {} >'.format(self.id)
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
       return "{}( _floor_element={!r}, _perimPsi={!r}, _wallHeight={!r}, _wallU={!r},"\
                    "_crawlU={!r}, _ventOpen={!r}, _windVel={!r}, _windFac={!r})".format(
                self.__class__.__name__,
                self.floor_element,
                self.PerimPsiVal,
                self.WallHeight,
                self.WallU,
                self.CrawlU,
                self.VentOpeningArea,
                self.windVelocity,
                self.windFactor)

