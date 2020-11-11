
class PHPP_Ground_Floor_Element:
    
    __warnings = None
    
    def __init__(self):
        pass
    
    def getWarnings(self):
        if self.__warnings == None:
            self.__warnings = []
        return self.__warnings
    
    def getSurfaceData(self, _flrSrfcs):
        """Pulls Rhino Scene parameters for a list of Surface Objects
        
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
        
        if _flrSrfcs == None:
            return 0,0
        
        if len(_flrSrfcs)>0:
            floorAreas = []
            weightedUvales = []
            
            sc.doc = Rhino.RhinoDoc.ActiveDoc
            for srfcGUID in _flrSrfcs:
                # Get the Surface Area Params
                srfcGeom = rs.coercebrep(srfcGUID)
                if srfcGeom:
                    srfcArea = ghc.Area(srfcGeom).area
                    floorAreas.append( srfcArea )
                    
                    # Get the Surface U-Values Params
                    srfcUvalue = self.getSrfcUvalue(srfcGUID)
                    weightedUvales.append(srfcUvalue * srfcArea )
                else:
                    floorAreas.append( 1 )
                    weightedUvales.append( 1 )
                    
                    warning = 'Error: Input into _floorSurfaces is not a Surface?\n'\
                    'Please ensure inputs are Surface Breps only.'
                    self.getWarnings().append(warning)
                
            sc.doc = ghdoc
            
            totalFloorArea = sum(floorAreas)
            floorUValue = sum(weightedUvales) / totalFloorArea
        
        else:
            totalFloorArea = 0
            floorUValue = 0
        
        return totalFloorArea, floorUValue
    
    def getExposedPerimData(self, _perimCrvs, _UDperimPsi):
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
        
        def getLengthIfNumber(_in, _psi):
            try:
                length = float(_in)
            except:
                length = None
            
            try:
                psi = float(_psi)
            except:
                psi = 0.05
        
            return length, psi
        
        if _perimCrvs == None:
            return 0, 0, None
        
        psiXlen = 0
        totalLen = 0
        warning = None
        
        if len(_perimCrvs)>0:
            sc.doc = Rhino.RhinoDoc.ActiveDoc
            for crvGUID in _perimCrvs:
                
                # See if its just Numbers passed in. If so, use them and break out
                length, crvPsiValue = getLengthIfNumber(crvGUID, _UDperimPsi)
                if length and crvPsiValue:
                    totalLen += length
                    psiXlen += (length * crvPsiValue)
                    continue
                
                isCrvGeom = rs.coercecurve(crvGUID)
                isBrepGeom = rs.coercebrep(crvGUID)
                
                if isCrvGeom:
                    crvLen = ghc.Length(isCrvGeom)
                    try:
                        crvPsiValue = float(_UDperimPsi)
                    except:
                        crvPsiValue, warning = self.getCurvePsiValue(crvGUID)
                    
                    totalLen += crvLen
                    psiXlen += (crvLen * crvPsiValue)
                elif isBrepGeom:
                    srfcEdges = ghc.DeconstructBrep(isBrepGeom).edges
                    srfcPerim = ghc.JoinCurves(srfcEdges, False)
                    crvLen = ghc.Length(srfcPerim)
                    
                    try:
                        crvPsiValue = float(_UDperimPsi)
                    except:
                        crvPsiValue = 0.05
                    
                    totalLen += crvLen
                    psiXlen += (crvLen * crvPsiValue) # Default 0.05 W/mk
                    warning = 'Note: You passed in a surface without any Psi-Values applied.\n'\
                    'I will apply a default 0.5 W/mk Psi-Value to ALL the edges of the\n'\
                    'surface passed in.'
                else:
                    warning = 'Error in GROUND: Input into _exposedPerimCrvs is not a Curve or Surface?\n'\
                    'Please ensure inputs are Curve / Polyline or Surface only.'
            sc.doc = ghdoc
            
            return totalLen, psiXlen, warning
        else:
            return 0, 0, None
        
    def getCurvePsiValue(self, _perimCrvGUID):
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
                    self.getWarnings().append(warning)
                    crvPsiValue = 0
            else:   
                warning = ('Warning: Could not find a Psi-Value type in the',
                'Rhino Document UserText with the name "{}?"'.format(crvPsiValueName.upper()),
                'Check your Document UserText library to make sure that you have',
                'your most recent Thermal Bridge library file loaded?',
                'For now applying a Psi-Value of 0.5 w/mk for this edge.')
                self.getWarnings().append(warning)
                crvPsiValue = 0.5
        else:
            warning = 'Warning: could not find a Psi-Value type in the\n'\
            'UserText document library for one or more edges?\n'\
            'Check your Document UserText library to make sure that you have\n'\
            'your most recent Thermal Bridge library file loaded?\n'\
            'For now applying a Psi-Value of 0.5 w/mk for this edge.'
            self.getWarnings().append(warning)
            crvPsiValue = 0.5
        
        return crvPsiValue, warning
    
    def getSrfcUvalue(self, _srfcGUID):
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
                self.getWarnings().append(warning)
                #ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, "\n".join(warning))
                srfcUvalue = 1.0
        else:
            warning = 'Warning: could not find a construction type in the\n'\
            'UserText for one or more surfaces? Are you sure you assigned a\n'\
            '"EPConstruction" parameter to the Floor Surface being input?\n'\
            'For now applying a U-Value of 1.0 w/m2k for this surface.'
            self.getWarnings().append(warning)
            #ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, warning)
            srfcUvalue = 1.0
        
        return srfcUvalue
    
    def getParamsFromRH(self, _HBZoneObj, _type):
        """ Finds the Floor Type Element surfaces in a Honeybee Zone and gets Params
        
        Resets self.FloorArea and self.FloorUValue based on the values found in
        the Honeybee Zone. If more than one SlabOnGrade is found, creates a 
        weighted U-Value average of all the surfaces.
        Arguments:
            _HBZoneObj: A Single Honeybee Zone object
            _type: (str) the type name ('SlabOnGrade', 'UngergoundSlab', 'ExposedFloor') of the floor element
        Returns:
            None
        """
        
        # Try and get the floor surface data
        slabAreas = []
        slabWeightedUvalue = []
        for srfc in _HBZoneObj.surfaces:
            if srfc.srfType[srfc.type] == _type:
                cnstrName = srfc.EPConstruction
                result = hb_EPMaterialAUX.decomposeEPCnstr(str(cnstrName).upper())
                if result != -1:
                    materials, comments, UValue_SI, UValue_IP = result
                else:
                    UValue_SI = 1
                    warning = 'Warning: Can not find material "{}" in the HB Library for surface?'.format(str(cnstrName))
                    self.getWarnings().append(warning)
                    #ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, msg)
                
                slabArea = srfc.getArea()
                slabAreas.append( slabArea )
                slabWeightedUvalue.append( UValue_SI * slabArea )
    
        if len(slabAreas)>0 and len(slabWeightedUvalue)>0:
            self.FloorArea = sum(slabAreas)
            self.FloorUvalue = sum(slabWeightedUvalue) / self.FloorArea
        
        #Try and get any below grade wall U-Values (area weighted)
        wallBG_Areas = []
        wallBG_UxA = []
        for srfc in _HBZoneObj.surfaces:
            if srfc.srfType[srfc.type] == 'UndergroundWall':
                result = hb_EPMaterialAUX.decomposeEPCnstr(str(cnstrName).upper())
                if result != -1:
                    materials, comments, UValue_SI, UValue_IP = result
                else:
                    UValue_SI = 1
                    warning = 'Warning: Can not find material "{}" in the HB Library for surface?'.format(str(cnstrName))
                    self.getWarnings().append(warning)
                    #ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, msg)
                
                wallArea = srfc.getArea()
                wallBG_Areas.append( wallArea )
                wallBG_UxA.append( UValue_SI * wallArea )
        
        if len(wallBG_Areas)>0 and len(wallBG_UxA)>0:
            self.WallU_BG = sum(wallBG_UxA) / sum(wallBG_Areas)


class PHPP_Ground_Slab_on_Grade:
    def __init__(self):
        self.floor_element = None


