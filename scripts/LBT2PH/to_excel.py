from System import Object
from Grasshopper import DataTree
from Grasshopper.Kernel.Data import GH_Path
import statistics

import LBT2PH
import LBT2PH.dhw

reload( LBT2PH )
reload( LBT2PH.dhw )

class PHPP_XL_Obj:
    """ A holder for an Excel writable datapoint with a worksheet, range and value """
    
    # {Unit You have: {Unit you Want}, {...}, ...}
    conversionSchema = {
            'C'    : {'SI':'*1', 'C':'*1', 'F':'*(9/5)+32'},
            'LITER': {'SI':'*1', 'LITER':'*1', 'GALLON':'*0.264172'},
            'MM'   : {'SI':'*1', 'MM':'*1', 'FT':'*0.00328084', 'IN':'*0.0394'},
            'M'    : {'SI':'*1', 'M':'*1', 'FT':'*3.280839895', 'IN':'*39.3701'},
            'M/DAY': {'SI':'*1', 'M/DAY':'*1', 'FT/DAY':'*3.280839895'},
            'M2'   : {'SI':'*1', 'M2':'*1', 'FT2':'*10.76391042'},
            'M3'   : {'SI':'*1', 'M3':'*1', 'FT3':'*35.31466672'},
            'M3/H' : {'SI':'*1', 'M3/H':'*1', 'CFM':'*0.588577779'},
            'WH/M3': {'SI':'*1', 'WH/M3':'*1', 'W/CFM':'*1.699010796'},
            'WH/KM2':{'SI':'*1', 'WH/KM2':'*1', 'BTU/FT2':'*0.176110159'},
            'MJ/M3K':{'SI':'*1', 'MJ/M3K':'*1', 'BTU/FT3-F':'*14.91066014'},
            'W/M2K': {'SI':'*1', 'W/M2K':'*1', 'BTU/HR-FT2-F':'*0.176110159','HR-FT2-F/BTU':'**-1*5.678264134' },
            'M2K/W': {'SI':'*1', 'M2K/W':'*1', 'HR-FT2-F/BTU':'*5.678264134'},
            'W/MK' : {'SI':'*1', 'W/MK':'*1', 'HR-FT2-F/BTU-IN':'**-1*0.144227909', 'BTU/HR-FT-F':'*0.577789236'},
            'W/K'  : {'SI':'*1', 'W/K':'*1', 'BTU/HR-F':'*1.895633976'},
            'KW'   : {'SI':'*1', 'KW':'*1','BTU/H':'*3412.141156'},
            'W/W'  : {'SI':'*1', 'W/W':'*1', 'BTU/HW':'*3.412141156'} # SEER
            }
    
    def __init__(self, _shtNm, _rangeAddress, _val, _unitSI=None, _unitIP='SI'):
        """
        Args:
            _shtNm (str): The Name of the Worksheet to write to
            _rangeAddress (str): The Cell Range (A1, B12, etc...) to write to on the Worksheet
            _val (str): The Value to write to the Cell Range (Value2)
            _unitSI: (str) The SI unit for the item
            _unitIP: (str) The IP unit for the item
        """
        self.Worksheet = _shtNm
        self.Range = _rangeAddress
        self.Value = _val
        self.Unit_SI = _unitSI
        self.Unit_IP = _unitIP
    
    def getWorksheet(self, _units='SI'):
        if _units == 'SI':
            return self.Worksheet
        
        if self.Worksheet == 'U-Values':
            return 'R-Values'
        elif self.Worksheet == 'Additional Vent':
            return 'Addl vent'
        else:
            return self.Worksheet
    
    def getValue(self, _targetUnit='SI'):
        """ Get the Item Value properly. Allows for unit conversion.
        
        For instance calling "obj.getValue(obj.Unit_IP)" will return the 
        converted value into Inch-Pound units. Pass 'SI' or leave 
        input blank for no conversion (return = self.Value x 1.0)
        
        Args:
            _targetUnit: (str) The unit to convert the value to. 'SI' or 'IP'
        Returns:
            value converted into the right units
        """
        
        if not self.Unit_SI:
            return self.Value
        
        if _targetUnit == 'IP':
            targetUnit = self.Unit_IP
        elif _targetUnit == 'SI':
            targetUnit = self.Unit_SI
        else:
            targetUnit = _targetUnit
        
        try:
            schema = self.conversionSchema.get(self.Unit_SI, {'SI':1})
            conversionFactor = schema.get(targetUnit, 1)
            return eval( str(self.Value)+str(conversionFactor))
        except:
            return self.Value
    
    def __unicode__(self):
        return u"PHPP Obj | Worksheet: {self.Worksheet}  |  Cell: {self.Range}  |  Value: {self.Value}".format(self=self)
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
       return "{}( _nm={!r}, _shtNm={!r}, _rangeAddress={!r}, _val={!r}, _unitSI={!r}, _unitIP={!r}".format(
               self.__class__.__name__,
               self.Worksheet,
               self.Range,
               self.Value,
               self.Unit_SI,
               self.Unit_IP)

def get_u_values(_inputBranch, _branch_materials):
    uID_Count = 1
    uValueUID_Names = []
    uValuesConstructorStartRow = 10
    uValuesList = []
    print('Creating the U-Values Objects...')
    for eachConst in _inputBranch:
        # for each Construction Assembly in the model....
        
        # Get the Construction's Name and the Materal Layers in the EP Model
        construcionNameEP = getattr(eachConst, 'Name')
        layers = sorted(getattr(eachConst, 'Layers'))
        intInsuFlag = eachConst.IntInsul if eachConst.IntInsul != None else ''
        
        # Filter out any of the Window Constructions
        isWindow = False
        opaqueMaterialNames = []
        for eachMat in _branch_materials:
            opaqueMaterialNames.append(eachMat.name) # Get all the Opaque Construction Material Names
        
        # Check if the material matches any of the Opaque ones
        for eachLayer in layers:
            if eachLayer[1] in opaqueMaterialNames:
                eachLayer[1]
                break
            else:
                # If not... it must be a window (maybe?)
                isWindow = True
        
        if isWindow == True:
            pass
        else:
            # Fix the name to remove 'PHPP_CONST_'
            if 'PHPP_CONST_' in construcionNameEP:
                constName_clean = construcionNameEP.split('PHPP_CONST_')[1].replace('_', ' ')
            else:
                constName_clean = construcionNameEP.replace('_', ' ')
            
            # Create the list of User-ID Constructions to match PHPP
            uValueUID_Names.append('{:02d}ud-{}'.format(uID_Count, constName_clean) )
            
            # Create the Objects for the Header Piece (Name, Rsi, Rse)
            nameAddress = '{}{}'.format('M', uValuesConstructorStartRow + 1) # Construction Name
            rSi = '{}{}'.format('M', uValuesConstructorStartRow + 3) # R-surface-int
            rSe = '{}{}'.format('M', uValuesConstructorStartRow + 4) # R-surface-ext
            intIns = '{}{}'.format('S', uValuesConstructorStartRow + 1) # Interior Insulation Flag
            
            uValuesList.append( PHPP_XL_Obj('U-Values', nameAddress, constName_clean))
            uValuesList.append( PHPP_XL_Obj('U-Values', rSi, 0, 'M2K/W', 'HR-FT2-F/BTU'))
            uValuesList.append( PHPP_XL_Obj('U-Values', rSe, 0, 'M2K/W', 'HR-FT2-F/BTU')) # For now, zero out
            if eachConst.IntInsul != None:
                uValuesList.append( PHPP_XL_Obj('U-Values', intIns, 'x'))
            
            # Create the actual Material Layers for PHPP U-Value
            layerCount = 0
            for layer in layers:
                # For each layer in the Construction Assembly...
                for eachMatLayer in  _branch_materials:
                    # See if the Construction's Layer material name matches one in the Materials list....
                    # If so, use those parameters from the Material Layer
                    if layer[1] == eachMatLayer.name:
                        # Filter out any MASSLAYERs
                        if layer[1] != 'MASSLAYER':
                            
                            # Clean the name
                            if 'PHPP_MAT_' in layer[1]:
                                layerMatName = layer[1].split('PHPP_MAT_')[1].replace('_', ' ')
                            else:
                                layerMatName = layer[1].replace('_', ' ')
                            
                            layerNum = layer[0]
                            layerMatCond = getattr(eachMatLayer, 'LayerConductivity')
                            layerThickness = getattr(eachMatLayer, 'LayerThickness')*1000 # Cus PHPP uses mm for thickness
                            
                            # Set up the Range tagets
                            layer1Address_L = '{}{}'.format('L', uValuesConstructorStartRow + 7 + layerCount) # Material Name
                            layer1Address_M = '{}{}'.format('M', uValuesConstructorStartRow + 7 + layerCount) # Conductivity
                            layer1Address_S = '{}{}'.format('S', uValuesConstructorStartRow + 7 + layerCount) # Thickness
                            
                            # Create the Layer Objects
                            uValuesList.append( PHPP_XL_Obj('U-Values', layer1Address_L, layerMatName))# Material Name
                            uValuesList.append( PHPP_XL_Obj('U-Values', layer1Address_M, layerMatCond, 'W/MK', 'HR-FT2-F/BTU-IN')) # Conductivity
                            uValuesList.append( PHPP_XL_Obj('U-Values', layer1Address_S, layerThickness, 'MM', 'IN')) # Thickness
                            
                            layerCount+=1
            
            uID_Count += 1
            uValuesConstructorStartRow += 21
    
    return uValuesList, uValueUID_Names

def get_components(_inputBranch):
    winComponentStartRow = 15
    frame_Count = 0
    glass_Count = 0
    winComponentsList = []
    glassNameDict = {}
    frameNameDict = {}
    
    print('Creating the Components:Window Objects...')
    
    for eachWin in _inputBranch:
        # ----------------------------------------------------------------------
        # Glass
        gNm = eachWin.glazing.display_name
        gV = eachWin.glazing.gValue
        uG = eachWin.glazing.uValue
        
        if gNm not in glassNameDict.keys():
            # Add the new glass type to the dict of UD Names:
            # ie: {'Ikon: SDH': '01ud-Ikon: SDH', ....}
            glassNameDict[gNm] = '{:02d}ud-{}'.format(glass_Count+1, gNm)
            
            # Set the glass range addresses
            Address_Gname = '{}{}'.format('IE', winComponentStartRow + glass_Count) # Name
            Address_Gvalue = '{}{}'.format('IF', winComponentStartRow + glass_Count) # g-Value
            Address_Uvalue = '{}{}'.format('IG', winComponentStartRow + glass_Count) # U-Value
            
            # Create the PHPP write Objects
            winComponentsList.append( PHPP_XL_Obj('Components', Address_Gname, gNm))# Glass Type Name
            winComponentsList.append( PHPP_XL_Obj('Components', Address_Gvalue, gV))# g-Value
            winComponentsList.append( PHPP_XL_Obj('Components', Address_Uvalue, uG, 'W/M2K', 'BTU/HR-FT2-F' ))# U-Value
            
            glass_Count +=1
            
        # Add the new PHPP UD Glass Name to the Window:Simple Object
        setattr(eachWin, 'UD_glass_Name', glassNameDict[gNm] )
        
        # ----------------------------------------------------------------------
        # Frames 
        fNm = eachWin.frame.display_name
        uF_L, uF_R, uF_B, uF_T  = eachWin.frame.uLeft, eachWin.frame.uRight, eachWin.frame.uBottom, eachWin.frame.uTop
        wF_L, wF_R, wF_B, wF_T  = eachWin.frame.fLeft, eachWin.frame.fRight, eachWin.frame.fBottom, eachWin.frame.fTop
        psiG_L, psiG_R, psiG_B, psiG_T  = eachWin.frame.psigLeft, eachWin.frame.psigRight, eachWin.frame.psigBottom, eachWin.frame.psigTop
        psiI_L, psiI_R, psiI_B, psiI_T  = eachWin.frame.psiInstLeft, eachWin.frame.psiInstRight, eachWin.frame.psiInstBottom, eachWin.frame.psiInstTop
        
        if fNm not in frameNameDict.keys():
            # Add the new frame type to the dict of UD Names:
            # ie: {'Ikon: SDH': '01ud-Ikon: SDH', ....}
            frameNameDict[fNm] = '{:02d}ud-{}'.format(frame_Count+1, fNm) # was glass_count????
            
            # Set the frame range address
            Address_Fname = '{}{}'.format('IL', winComponentStartRow + frame_Count)
            Address_Uf_Left = '{}{}'.format('IM', winComponentStartRow + frame_Count)
            Address_Uf_Right = '{}{}'.format('IN', winComponentStartRow + frame_Count)
            Address_Uf_Bottom = '{}{}'.format('IO', winComponentStartRow + frame_Count)
            Address_Uf_Top = '{}{}'.format('IP', winComponentStartRow + frame_Count)
            Address_W_Left = '{}{}'.format('IQ', winComponentStartRow + frame_Count)
            Address_W_Right = '{}{}'.format('IR', winComponentStartRow + frame_Count)
            Address_W_Bottom = '{}{}'.format('IS', winComponentStartRow + frame_Count)
            Address_W_Top = '{}{}'.format('IT', winComponentStartRow + frame_Count)
            Address_Psi_g_Left = '{}{}'.format('IU', winComponentStartRow + frame_Count)
            Address_Psi_g_Right = '{}{}'.format('IV', winComponentStartRow + frame_Count)
            Address_Psi_g_Bottom = '{}{}'.format('IW', winComponentStartRow + frame_Count)
            Address_Psi_g_Top = '{}{}'.format('IX', winComponentStartRow + frame_Count)
            Address_Psi_I_Left = '{}{}'.format('IY', winComponentStartRow + frame_Count)
            Address_Psi_I_Right = '{}{}'.format('IZ', winComponentStartRow + frame_Count)
            Address_Psi_I_Bottom = '{}{}'.format('JA', winComponentStartRow + frame_Count)
            Address_Psi_I_Top = '{}{}'.format('JB', winComponentStartRow + frame_Count)
            
            # Create the PHPP Objects for the Frames
            winComponentsList.append( PHPP_XL_Obj('Components', Address_Fname, fNm))# Frame Type Name
            
            winComponentsList.append( PHPP_XL_Obj('Components', Address_Uf_Left, uF_L, 'W/M2K', 'BTU/HR-FT2-F')) # Frame Type U-Values
            winComponentsList.append( PHPP_XL_Obj('Components', Address_Uf_Right, uF_R, 'W/M2K', 'BTU/HR-FT2-F'))
            winComponentsList.append( PHPP_XL_Obj('Components', Address_Uf_Bottom, uF_B, 'W/M2K', 'BTU/HR-FT2-F'))
            winComponentsList.append( PHPP_XL_Obj('Components', Address_Uf_Top, uF_T, 'W/M2K', 'BTU/HR-FT2-F'))
            
            winComponentsList.append( PHPP_XL_Obj('Components', Address_W_Left, wF_L, 'M', 'IN')) # Frame Type Widths
            winComponentsList.append( PHPP_XL_Obj('Components', Address_W_Right, wF_R, 'M', 'IN'))
            winComponentsList.append( PHPP_XL_Obj('Components', Address_W_Bottom, wF_B, 'M', 'IN'))
            winComponentsList.append( PHPP_XL_Obj('Components', Address_W_Top, wF_T, 'M', 'IN'))
            
            winComponentsList.append( PHPP_XL_Obj('Components', Address_Psi_g_Left, psiG_L, 'W/MK', 'BTU/HR-FT-F')) # Frame Type Psi-Glazing
            winComponentsList.append( PHPP_XL_Obj('Components', Address_Psi_g_Right, psiG_R, 'W/MK', 'BTU/HR-FT-F'))
            winComponentsList.append( PHPP_XL_Obj('Components', Address_Psi_g_Bottom, psiG_B, 'W/MK', 'BTU/HR-FT-F'))
            winComponentsList.append( PHPP_XL_Obj('Components', Address_Psi_g_Top, psiG_T, 'W/MK', 'BTU/HR-FT-F'))
            
            winComponentsList.append( PHPP_XL_Obj('Components', Address_Psi_I_Left, psiI_L, 'W/MK', 'BTU/HR-FT-F')) # Frame Type Psi-Installs
            winComponentsList.append( PHPP_XL_Obj('Components', Address_Psi_I_Right, psiI_R, 'W/MK', 'BTU/HR-FT-F'))
            winComponentsList.append( PHPP_XL_Obj('Components', Address_Psi_I_Bottom, psiI_B, 'W/MK', 'BTU/HR-FT-F'))
            winComponentsList.append( PHPP_XL_Obj('Components', Address_Psi_I_Top, psiI_T, 'W/MK', 'BTU/HR-FT-F'))
            
            frame_Count +=1
            
        # Add the PHPP UD Frame Name to the Window:Simple Object
        setattr(eachWin, 'UD_frame_Name', frameNameDict[fNm] )
    
    return winComponentsList

def get_areas(_inputBranch, _zones, _uValueUID_Names):
    areasRowStart = 41
    areaCount = 0
    uID_Count = 1
    areasList = []
    surfacesIncluded = []
    print("Creating the 'Areas' Objects...")
    for surface in _inputBranch:
        # for each Opaque Surface in the model....
        
        # First, see if the Surface should be included in the output
        for eachZoneName in _zones:
            if surface.HostZoneName == eachZoneName:
                includeSurface = True
                break
            else:
                includeSurface = False
        
        if includeSurface:
            # Get the Surface Parameters
            nm = getattr(surface, 'Name')
            groupNum = getattr(surface, 'GroupNum')
            quantity = 1
            surfaceArea = getattr(surface, 'SurfaceArea')
            assemblyName = getattr(surface, 'AssemblyName').replace('_', ' ') 
            angleFromNorth = getattr(surface, 'AngleFromNorth')
            angleFromHoriz = getattr(surface, 'AngleFromHoriz')
            shading = getattr(surface, 'Factor_Shading')
            abs = getattr(surface, 'Factor_Absorptivity')
            emmis = getattr(surface, 'Factor_Emissivity')
            
            # Find the right UID name (with the numeric prefix)
            for uIDName in _uValueUID_Names:
                if assemblyName in uIDName[5:] or uIDName[5:] in assemblyName: # compare to slice without prefix
                    assemblyName = uIDName
            
            # Setup the Excel Address Locations
            Address_Name = '{}{}'.format('L', areasRowStart + areaCount)
            Address_GroupNum = '{}{}'.format('M', areasRowStart + areaCount)
            Address_Quantity = '{}{}'.format('P', areasRowStart + areaCount)
            Address_Area = '{}{}'.format('V', areasRowStart + areaCount)
            Address_Assembly = '{}{}'.format('AC', areasRowStart + areaCount)
            Address_AngleNorth = '{}{}'.format('AG', areasRowStart + areaCount)
            Address_AngleHoriz = '{}{}'.format('AH', areasRowStart + areaCount)
            Address_ShadingFac = '{}{}'.format('AJ', areasRowStart + areaCount)
            Address_Abs = '{}{}'.format('AK', areasRowStart + areaCount)
            Address_Emmis = '{}{}'.format('AL', areasRowStart + areaCount)
            
            areasList.append( PHPP_XL_Obj('Areas', Address_Name, nm))# Surface Name
            areasList.append( PHPP_XL_Obj('Areas', Address_GroupNum, groupNum))# Surface Group Number
            areasList.append( PHPP_XL_Obj('Areas', Address_Quantity, quantity))# Surface Quantity
            areasList.append( PHPP_XL_Obj('Areas', Address_Area, surfaceArea, 'M2', 'FT2'))# Surface Area (m2)
            areasList.append( PHPP_XL_Obj('Areas', Address_Assembly, assemblyName))# Assembly Type Name
            areasList.append( PHPP_XL_Obj('Areas', Address_AngleNorth, angleFromNorth))# Orientation Off North
            areasList.append( PHPP_XL_Obj('Areas', Address_AngleHoriz, angleFromHoriz))# Orientation Off Horizontal
            areasList.append( PHPP_XL_Obj('Areas', Address_ShadingFac, shading))# Shading Factor
            areasList.append( PHPP_XL_Obj('Areas', Address_Abs, abs))# Absorptivity
            areasList.append( PHPP_XL_Obj('Areas', Address_Emmis, emmis))# Emmissivity
            
            # Add the PHPP UD Surface Name to the Surface Object
            setattr(surface, 'UD_Srfc_Name', '{:d}-{}'.format(uID_Count, nm) )
            
            # Keep track of which Surfaces are included in the output
            surfacesIncluded.append(nm)
            
            uID_Count += 1
            areaCount += 1
    
    areasList.append( PHPP_XL_Obj('Areas', 'L19', 'Suspended Floor') )
    return areasList, surfacesIncluded

def get_windows(_inputBranch, _surfacesIncluded, _srfcBranch):
    windowsRowStart = 24
    windowsCount = 0
    winSurfacesList = []

    print("Creating the 'Windows' Objects...")
    for window in _inputBranch:
        # for each Window Surface Object in the model....
        # Get the window's basic params
        quant = window.quantity
        nm = window.name
        w = window.width
        h = window.height
        host = window.host_surface
        glassType = window.glazing
        frameType = window.frame
        glassTypeUD = getattr(window, 'UD_glass_Name')
        frameTypeUD = getattr(window, 'UD_frame_Name')
        variantType = getattr(window, 'Type_Variant', 'a')
        Inst_L, Inst_R, Inst_B, Inst_T = window.installs
        
        # See if the Window should be included in the output
        includeWindow = False
        for eachSurfaceName in _surfacesIncluded:
            if eachSurfaceName == host:
                includeWindow = True
                break
            else:
                includeWindow = False
        
        if includeWindow:
            # Find the Window's Host Surface UD
            for srfc in _srfcBranch:
                if host == srfc.Name:
                    hostUD = srfc.UD_Srfc_Name
           
           # Get the Window Range Addresses
            Address_varType = '{}{}'.format('F', windowsRowStart + windowsCount)
            Address_winQuantity = '{}{}'.format('L', windowsRowStart + windowsCount)
            Address_winName = '{}{}'.format('M', windowsRowStart + windowsCount)
            Address_w = '{}{}'.format('Q', windowsRowStart + windowsCount)
            Address_h = '{}{}'.format('R', windowsRowStart + windowsCount)
            Address_hostName = '{}{}'.format('S', windowsRowStart + windowsCount)
            Address_glassType = '{}{}'.format('T', windowsRowStart + windowsCount)
            Address_frameType = '{}{}'.format('U', windowsRowStart + windowsCount)
            Address_install_Left = '{}{}'.format('AA', windowsRowStart + windowsCount)
            Address_install_Right = '{}{}'.format('AB', windowsRowStart + windowsCount)
            Address_install_Bottom = '{}{}'.format('AC', windowsRowStart + windowsCount)
            Address_install_Top = '{}{}'.format('AD', windowsRowStart + windowsCount)
            
            # Create the PHPP Window Object
            winSurfacesList.append( PHPP_XL_Obj('Windows', Address_varType, variantType)) # Quantity
            winSurfacesList.append( PHPP_XL_Obj('Windows', Address_winQuantity, quant)) # Quantity
            winSurfacesList.append( PHPP_XL_Obj('Windows', Address_winName, nm)) # Name
            winSurfacesList.append( PHPP_XL_Obj('Windows', Address_w, w, 'M', 'FT')) # Width
            winSurfacesList.append( PHPP_XL_Obj('Windows', Address_h, h, 'M', 'FT')) # Height
            winSurfacesList.append( PHPP_XL_Obj('Windows', Address_hostName, hostUD)) # Host Name
            winSurfacesList.append( PHPP_XL_Obj('Windows', Address_glassType, glassTypeUD)) # Glass UD Name
            winSurfacesList.append( PHPP_XL_Obj('Windows', Address_frameType, frameTypeUD)) # Frame UD Name
            winSurfacesList.append( PHPP_XL_Obj('Windows', Address_install_Left, Inst_L)) # Install Condition Left
            winSurfacesList.append( PHPP_XL_Obj('Windows', Address_install_Right, Inst_R)) # Install Condition Right
            winSurfacesList.append( PHPP_XL_Obj('Windows', Address_install_Bottom, Inst_B)) # Install Condition Bottom
            winSurfacesList.append( PHPP_XL_Obj('Windows', Address_install_Top, Inst_T)) # Install Condition Top
            
            windowsCount += 1
            
    return winSurfacesList

def get_shading(_inputBranch, _surfacesIncluded):
    print("Creating the 'Shading' Objects...")
    row_start = 17
    row_count = 0
    shading_list = []
    
    #---------------------------------------------------------------------------
    # First, try and get the 'simple' shading geometry if it exists
    # Otherwise, try and get any direct shading factors applied to the window
    for window in _inputBranch:
        
        
        if window.host_surface not in _surfacesIncluded:
            continue
        
        row = row_start + row_count
        row_count += 1
        
        #-----------------------------------------------------------------------
        shading_dims = window.shading_dimensions
        if shading_dims:
            try:
                shading_list.append( PHPP_XL_Obj( 'Shading', '{}{}'.format('Z', row),  shading_dims.horizon.h_hori))
                shading_list.append( PHPP_XL_Obj( 'Shading', '{}{}'.format('AA', row), shading_dims.horizon.d_hori))
                shading_list.append( PHPP_XL_Obj( 'Shading', '{}{}'.format('AB', row), shading_dims.reveal.o_reveal))
                shading_list.append( PHPP_XL_Obj( 'Shading', '{}{}'.format('AC', row), shading_dims.reveal.d_reveal))
                shading_list.append( PHPP_XL_Obj( 'Shading', '{}{}'.format('AD', row), shading_dims.overhang.o_over))
                shading_list.append( PHPP_XL_Obj( 'Shading', '{}{}'.format('AE', row), shading_dims.overhang.d_over))
            except Exception as e:
                print('Something went wrong getting the Shading Dimension values?')
                print(e)
        else:
            shading_list.append( PHPP_XL_Obj( 'Shading', '{}{}'.format('AF', row), window.shading_factor_winter))
            shading_list.append( PHPP_XL_Obj( 'Shading', '{}{}'.format('AG', row), window.shading_factor_summer))
        
    return shading_list

def get_TFA( spaces_branch, _zones):
    tfa = []
    
    # --------------------------------------------------------------------------
    # Otherwise, find the values from the model
    print("Trying to find any Honeybee Zone Room TFA info...")
    try:
        tfaSurfaceAreas = [ 0 ]
        for space in spaces_branch:
            # First, see if the Surface should be included in the output
            for zoneName in _zones:
                if space.host_room_name == zoneName:
                    includeRoom = True
                    break
                else:
                    includeRoom = False
            
            if includeRoom:
                # Get the room's TFA info
                roomTFA = space.FloorArea_TFA
                tfaSurfaceAreas.append( roomTFA )
        # Total up the TFA Areas for output
        tfaTotal = sum(tfaSurfaceAreas)
        tfa.append( PHPP_XL_Obj('Areas', 'V34', tfaTotal, 'M2', 'FT2' )) # TFA (m2)
    except:
        pass
    
    return tfa

def get_addnl_vent_rooms(_inputBranch, _vent_systems, _zones, _startRows):
    print("Creating 'Additional Ventilation' Rooms... ")
    addnlVentRooms = []
    ventUnitsUsed = []
    roomRowStart = _startRows.get('Additional Ventilation').get('Rooms', 57)
    ventUnitRowStart = _startRows.get('Additional Ventilation').get('Vent Unit Selection', 97)
    included_vent_system_ids = set()
    i = 0
    
    for i, phpp_space in enumerate(_inputBranch):
        # ----------------------------------------------------------------------
        # find the right ventilation system to use
        for s in _vent_systems:
            if phpp_space.phpp_vent_system_id == s.system_id:
                vent_system = s
                break
        
        if phpp_space.host_room_name in _zones:
            # ------------------------------------------------------------------
            # Try and sort out the Room's Ventilation airflow and schedule if there is any
            included_vent_system_ids.add(vent_system.system_id)
            roomAirFlow_sup = phpp_space.space_vent_supply_air
            roomAirFlow_eta = phpp_space.space_vent_extract_air
            roomAirFlow_trans = phpp_space.space_vent_transfer_air
            ventUnitName = vent_system.vent_unit.name
            ventSystemName = vent_system.system_name
            
            # ------------------------------------------------------------------
            # Get the Ventilation Schedule from the room if it has any
            try:
                speed_high = phpp_space.vent_sched._speed_high
                time_high  = phpp_space.vent_sched._time_high
                speed_med  = phpp_space.vent_sched._speed_med
                time_med   = phpp_space.vent_sched._time_med
                speed_low  = phpp_space.vent_sched._speed_low
                time_low   = phpp_space.vent_sched._time_low
            except:
                speed_high = 1
                time_high = 1
                speed_med = None
                time_med = None
                speed_low = None
                time_low = None
            
            # ------------------------------------------------------------------
            # Build the Excel Objects
            address_Amount = '{}{}'.format('D', roomRowStart + i)
            address_Name = '{}{}'.format('E', roomRowStart + i)
            address_VentAllocation = '{}{}'.format('F', roomRowStart + i)
            address_Area = '{}{}'.format('G', roomRowStart + i)
            address_RoomHeight = '{}{}'.format('H', roomRowStart + i)
            address_SupplyAirFlow = '{}{}'.format('J', roomRowStart + i)
            address_ExractAirFlow = '{}{}'.format('K', roomRowStart + i)
            address_TransferAirFlow = '{}{}'.format('L', roomRowStart + i)
            address_Util_hrs = '{}{}'.format('N', roomRowStart + i)
            address_Util_days = '{}{}'.format('O', roomRowStart + i)
            address_Holidays = '{}{}'.format('P', roomRowStart + i)
            
            address_ventSpeed_high = '{}{}'.format('Q', roomRowStart + i)
            address_ventTime_high = '{}{}'.format('R', roomRowStart + i) 
            address_ventSpeed_med = '{}{}'.format('S', roomRowStart + i)
            address_ventTime_med = '{}{}'.format('T', roomRowStart + i)
            address_ventSpeed_low = '{}{}'.format('U', roomRowStart + i)
            address_ventTime_low = '{}{}'.format('V', roomRowStart + i)
            
            ventMatchFormula = '=MATCH("{}",E{}:E{},0)'.format(ventSystemName, ventUnitRowStart, ventUnitRowStart+9)
            
            addnlVentRooms.append( PHPP_XL_Obj('Additional Vent', address_Amount, 1 ))
            addnlVentRooms.append( PHPP_XL_Obj('Additional Vent', address_Name, '{}-{}'.format(phpp_space.space_number, phpp_space.space_name )))
            addnlVentRooms.append( PHPP_XL_Obj('Additional Vent', address_VentAllocation, ventMatchFormula ))
            addnlVentRooms.append( PHPP_XL_Obj('Additional Vent', address_Area, phpp_space.space_tfa, 'M2', 'FT2'))
            addnlVentRooms.append( PHPP_XL_Obj('Additional Vent', address_RoomHeight, phpp_space.space_avg_clear_ceiling_height, 'M2', 'FT2'))
            
            addnlVentRooms.append( PHPP_XL_Obj('Additional Vent', address_SupplyAirFlow, roomAirFlow_sup, 'M3/H', 'CFM'))
            addnlVentRooms.append( PHPP_XL_Obj('Additional Vent', address_ExractAirFlow, roomAirFlow_eta, 'M3/H', 'CFM'))
            addnlVentRooms.append( PHPP_XL_Obj('Additional Vent', address_TransferAirFlow, roomAirFlow_trans, 'M3/H', 'CFM'))
            
            addnlVentRooms.append( PHPP_XL_Obj('Additional Vent', address_Util_hrs, '24'))
            addnlVentRooms.append( PHPP_XL_Obj('Additional Vent', address_Util_days, '7'))
            addnlVentRooms.append( PHPP_XL_Obj('Additional Vent', address_Holidays,'0'))
            
            addnlVentRooms.append( PHPP_XL_Obj('Additional Vent', address_ventSpeed_high, speed_high if speed_high else 1))
            addnlVentRooms.append( PHPP_XL_Obj('Additional Vent', address_ventTime_high, time_high if time_high else 1))
            addnlVentRooms.append( PHPP_XL_Obj('Additional Vent', address_ventSpeed_med,speed_med if speed_med else 1))
            addnlVentRooms.append( PHPP_XL_Obj('Additional Vent', address_ventTime_med, time_med if time_med else 0))
            addnlVentRooms.append( PHPP_XL_Obj('Additional Vent', address_ventSpeed_low,speed_low if speed_low else 0))
            addnlVentRooms.append( PHPP_XL_Obj('Additional Vent', address_ventTime_low, time_low if time_low else 0))
            
            # Keep track of the names of the Vent units used
            ventUnitsUsed.append( ventUnitName )
    
    # --------------------------------------------------------------------------
    # Include any Exhaust Ventilation Objects that are found in any of the included Vent Systems
    rowCount = i+1
    for vent_system in _vent_systems:
        if vent_system.system_id not in included_vent_system_ids:
            break
        
        for exhaust_vent_obj in vent_system.exhaust_vent_objs:
            for mode in ['on', 'off']:
                address_Amount = '{}{}'.format('D', roomRowStart + rowCount)
                address_Name = '{}{}'.format('E', roomRowStart + rowCount)
                address_VentAllocation = '{}{}'.format('F', roomRowStart + rowCount)
                address_Area = '{}{}'.format('G', roomRowStart + rowCount)
                address_RoomHeight = '{}{}'.format('H', roomRowStart + rowCount)
                address_SupplyAirFlow = '{}{}'.format('J', roomRowStart + rowCount)
                address_ExractAirFlow = '{}{}'.format('K', roomRowStart + rowCount)
                address_TransferAirFlow = '{}{}'.format('L', roomRowStart + rowCount)
                address_Util_hrs = '{}{}'.format('N', roomRowStart + rowCount)
                address_Util_days = '{}{}'.format('O', roomRowStart + rowCount)
                address_Holidays = '{}{}'.format('P', roomRowStart + rowCount)
                    
                address_ventSpeed_high = '{}{}'.format('Q', roomRowStart + rowCount)
                address_ventTime_high = '{}{}'.format('R', roomRowStart + rowCount) 
                address_ventSpeed_med = '{}{}'.format('S', roomRowStart + rowCount)
                address_ventTime_med = '{}{}'.format('T', roomRowStart + rowCount)
                address_ventSpeed_low = '{}{}'.format('U', roomRowStart + rowCount)
                address_ventTime_low = '{}{}'.format('V', roomRowStart + rowCount)
                
                ventMatchFormula = '=MATCH("{}",E{}:E{},0)'.format(exhaust_vent_obj.name, ventUnitRowStart, ventUnitRowStart+9)
                
                addnlVentRooms.append( PHPP_XL_Obj('Additional Vent', address_Amount, 1 ))
                addnlVentRooms.append( PHPP_XL_Obj('Additional Vent', address_Name, exhaust_vent_obj.name +' [ON]' if mode=='on' else exhaust_vent_obj.name +' [OFF]'))
                addnlVentRooms.append( PHPP_XL_Obj('Additional Vent', address_VentAllocation, ventMatchFormula ))
                addnlVentRooms.append( PHPP_XL_Obj('Additional Vent', address_Area, '10', 'M', 'FT'))
                addnlVentRooms.append( PHPP_XL_Obj('Additional Vent', address_RoomHeight, '2.5', 'M', 'FT' ))
                
                addnlVentRooms.append( PHPP_XL_Obj('Additional Vent', address_SupplyAirFlow, exhaust_vent_obj.flow_rate_on if mode=='on' else exhaust_vent_obj.flow_rate_off, 'M3/H', 'CFM'))
                addnlVentRooms.append( PHPP_XL_Obj('Additional Vent', address_ExractAirFlow, exhaust_vent_obj.flow_rate_on if mode=='on' else exhaust_vent_obj.flow_rate_off, 'M3/H', 'CFM'))
                addnlVentRooms.append( PHPP_XL_Obj('Additional Vent', address_TransferAirFlow, '0', 'M3/H', 'CFM' ))
                
                addnlVentRooms.append( PHPP_XL_Obj('Additional Vent', address_Util_hrs, exhaust_vent_obj.hours_per_day_on if mode=='on' else 24 - float(exhaust_vent_obj.hours_per_day_on)))
                addnlVentRooms.append( PHPP_XL_Obj('Additional Vent', address_Util_days, exhaust_vent_obj.days_per_week_on if mode=='on' else 7))
                addnlVentRooms.append( PHPP_XL_Obj('Additional Vent', address_Holidays, exhaust_vent_obj.holidays))
                
                addnlVentRooms.append( PHPP_XL_Obj('Additional Vent', address_ventSpeed_high, 1))
                addnlVentRooms.append( PHPP_XL_Obj('Additional Vent', address_ventTime_high, 1))
                addnlVentRooms.append( PHPP_XL_Obj('Additional Vent', address_ventSpeed_med,0))
                addnlVentRooms.append( PHPP_XL_Obj('Additional Vent', address_ventTime_med, 0))
                addnlVentRooms.append( PHPP_XL_Obj('Additional Vent', address_ventSpeed_low, 0))
                addnlVentRooms.append( PHPP_XL_Obj('Additional Vent', address_ventTime_low, 0))
                
                rowCount += 1
    
    return addnlVentRooms, ventUnitsUsed

def get_addnl_vent_systems(_inputBranch, _ventUnitsUsed, _startRows):
    # Go through each Ventilation System passed in
    
    if not _inputBranch:
        return []
    
    #---------------------------------------------------------------------------
    vent = []
    ventCompoRowStart = _startRows.get('Components').get('Ventilator')
    ventUnitRowStart = _startRows.get('Additional Ventilation').get('Vent Unit Selection')
    ventDuctsRowStart = _startRows.get('Additional Ventilation').get('Vent Ducts')
    ventCount = 0
    ductsCount = 0
    ductColCount = ord('Q')
    
    print("Creating 'Additional Ventilation' Systems...")
    vent.append( PHPP_XL_Obj('Ventilation', 'H42', 'x') ) # Turn on Additional Vent
    vent.append( PHPP_XL_Obj('Additional Vent', 'F'+str(ventDuctsRowStart-11) , "=AVERAGE(Climate!E24, Climate!F24, Climate!N24, Climate!O24, Climate!P24") ) # External Average Temp
    
    #---------------------------------------------------------------------------
    #for key in _inputBranch[0].keys():
    for vent_system in _inputBranch:
        
        if vent_system.vent_unit.name not in _ventUnitsUsed:
            continue
        
        #-----------------------------------------------------------------------
        # Basic Ventialtion
        # Create the Vent Unit in the Components Worksheet
        # Set the UD name for access in 'Addnl-Vent' dropdown list
        row = ventCompoRowStart + ventCount
        vent_system.phpp_ud_name = '{:02d}ud-{}'.format(ventCount+1, vent_system.vent_unit.name)
        
        vent.append( PHPP_XL_Obj('Components', 'JH{}'.format(row), vent_system.vent_unit.name ))
        vent.append( PHPP_XL_Obj('Components', 'JI{}'.format(row), vent_system.vent_unit.HR_eff ))
        vent.append( PHPP_XL_Obj('Components', 'JJ{}'.format(row), vent_system.vent_unit.MR_eff ))
        vent.append( PHPP_XL_Obj('Components', 'JK{}'.format(row), vent_system.vent_unit.elec_eff, 'WH/M3', 'W/CFM'))
        vent.append( PHPP_XL_Obj('Components', 'JL{}'.format(row), 1, 'M3/H', 'CFM'))
        vent.append( PHPP_XL_Obj('Components', 'JM{}'.format(row), 10000, 'M3/H', 'CFM' ))
        vent.append( PHPP_XL_Obj('Ventilation', 'L12', vent_system.system_type) ) 
        
        # Build the Vent Unit
        vent.append(  PHPP_XL_Obj('Additional Vent',  'D{}'.format(row),  1) ) # Quantity
        vent.append(  PHPP_XL_Obj('Additional Vent',  'E{}'.format(row),  vent_system.system_name) )
        vent.append(  PHPP_XL_Obj('Additional Vent',  'F{}'.format(row),  vent_system.phpp_ud_name) )
        vent.append(  PHPP_XL_Obj('Additional Vent',  'Q{}'.format(row),  vent_system.vent_unit.exterior) )
        vent.append(  PHPP_XL_Obj('Additional Vent',  'X{}'.format(row),  '2-Elec.') )
        vent.append(  PHPP_XL_Obj('Additional Vent',  'Y{}'.format(row),  vent_system.vent_unit.frost_temp, 'C', 'F') )
        
        # Build the Vent Unit Ducting
        row_ducts = ventDuctsRowStart + ductsCount
        vent.append( PHPP_XL_Obj('Additional Vent',  'D{}'.format(row_ducts), 1)) # Quantity
        vent.append( PHPP_XL_Obj('Additional Vent',  'E{}'.format(row_ducts), vent_system.duct_01.duct_width, 'MM', 'IN'))
        vent.append( PHPP_XL_Obj('Additional Vent',  'H{}'.format(row_ducts), vent_system.duct_01.insulation_thickness, 'MM', 'IN'))
        vent.append( PHPP_XL_Obj('Additional Vent',  'I{}'.format(row_ducts), vent_system.duct_01.insulation_lambda, 'W/MK', 'HR-FT2-F/BTU-IN'))
        vent.append( PHPP_XL_Obj('Additional Vent',  'J{}'.format(row_ducts), 'x' ))# Reflective
        vent.append( PHPP_XL_Obj('Additional Vent',  'L{}'.format(row_ducts), vent_system.duct_01.duct_length, 'M', 'FT' ))
        vent.append( PHPP_XL_Obj('Additional Vent',  'M{}'.format(row_ducts), '1'))
        
        vent.append( PHPP_XL_Obj('Additional Vent',  'D{}'.format(row_ducts+1), 1)) # Quantity
        vent.append( PHPP_XL_Obj('Additional Vent',  'E{}'.format(row_ducts+1), vent_system.duct_02.duct_width, 'MM', 'IN'))
        vent.append( PHPP_XL_Obj('Additional Vent',  'H{}'.format(row_ducts+1), vent_system.duct_02.insulation_thickness, 'MM', 'IN'))
        vent.append( PHPP_XL_Obj('Additional Vent',  'I{}'.format(row_ducts+1), vent_system.duct_02.insulation_lambda, 'W/MK', 'HR-FT2-F/BTU-IN'))
        vent.append( PHPP_XL_Obj('Additional Vent',  'J{}'.format(row_ducts+1), 'x' ))# Reflective
        vent.append( PHPP_XL_Obj('Additional Vent',  'L{}'.format(row_ducts+1), vent_system.duct_02.duct_length, 'M', 'FT'))
        vent.append( PHPP_XL_Obj('Additional Vent',  'N{}'.format(row_ducts+1), '1'))
        
        vent.append( PHPP_XL_Obj('Additional Vent',  '{}{}'.format(chr(ductColCount), row_ducts) , 1)) # Assign Duct to Vent
        vent.append( PHPP_XL_Obj('Additional Vent',  '{}{}'.format(chr(ductColCount), row_ducts+1) , 1)) # Assign Duct to Vent
        
        ductColCount+=1
        ductsCount+=2
        ventCount+=1
        
        #-----------------------------------------------------------------------
        # Exhaust Ventilation Objects
        # Add in any 'Exhaust Only' ventilation objects (kitchen hoods, etc...)
        for exhaust_system in vent_system.exhaust_vent_objs:
            exhaust_system.phpp_ud_name = '{:02d}ud-{}'.format(ventCount+1, exhaust_system.name)
            
            # Build the Vent in the Components Worksheet
            row = ventCompoRowStart + ventCount
            vent.append( PHPP_XL_Obj('Components', 'JH{}'.format(row), exhaust_system.name ))
            vent.append( PHPP_XL_Obj('Components', 'JI{}'.format(row), 0 )) #  Vent Heat Recovery
            vent.append( PHPP_XL_Obj('Components', 'JJ{}'.format(row), 0 )) #  Vent Moisture Recovery
            vent.append( PHPP_XL_Obj('Components', 'JK{}'.format(row), 0.25, 'WH/M3', 'W/CFM' )) #  Vent Elec Efficiency
            vent.append( PHPP_XL_Obj('Components', 'JL{}'.format(row), 1, 'M3/H', 'CFM')) #  DEFAULT MIN FLOW
            vent.append( PHPP_XL_Obj('Components', 'JM{}'.format(row), 10000, 'M3/H', 'CFM' )) #  DEFAULT MAX FLOW
            
            # Build the Vent Unit
            row = ventUnitRowStart + ventCount
            vent.append(  PHPP_XL_Obj('Additional Vent',  'D{}'.format(row),  1) ) # Quantity
            vent.append(  PHPP_XL_Obj('Additional Vent',  'E{}'.format(row),  exhaust_system.name ) )
            vent.append(  PHPP_XL_Obj('Additional Vent',  'F{}'.format(row),  exhaust_system.phpp_ud_name ) )
            vent.append(  PHPP_XL_Obj('Additional Vent',  'Q{}'.format(row),  '') ) # Exterior Installation?
            vent.append(  PHPP_XL_Obj('Additional Vent',  'X{}'.format(row),  '1-No') ) # Frost Protection Type
            vent.append(  PHPP_XL_Obj('Additional Vent',  'Y{}'.format(row),  '-5', 'C', 'F') ) # Frost Protection Temp
            
            # Build the Vent Unit Ducting
            row = ventDuctsRowStart + ductsCount
            vent.append( PHPP_XL_Obj('Additional Vent',  'D{}'.format(row), 1)) # Quantity
            vent.append( PHPP_XL_Obj('Additional Vent',  'E{}'.format(row), exhaust_system.duct_01.duct_width, 'MM', 'IN'))
            vent.append( PHPP_XL_Obj('Additional Vent',  'H{}'.format(row), exhaust_system.duct_01.insulation_thickness, 'MM', 'IN'))
            vent.append( PHPP_XL_Obj('Additional Vent',  'I{}'.format(row), exhaust_system.duct_01.insulation_lambda, 'W/MK', 'HR-FT2-F/BTU-IN'))
            vent.append( PHPP_XL_Obj('Additional Vent',  'J{}'.format(row), 'x' ))# Reflective
            vent.append( PHPP_XL_Obj('Additional Vent',  'L{}'.format(row), exhaust_system.duct_01.duct_length if exhaust_system else 5, 'M', 'FT'))
            vent.append( PHPP_XL_Obj('Additional Vent',  'M{}'.format(row), '1'))
            
            vent.append( PHPP_XL_Obj('Additional Vent',  'D{}'.format(row+1), 1)) # Quantity
            vent.append( PHPP_XL_Obj('Additional Vent',  'E{}'.format(row+1), exhaust_system.duct_02.duct_width, 'MM', 'IN'))
            vent.append( PHPP_XL_Obj('Additional Vent',  'H{}'.format(row+1), exhaust_system.duct_02.insulation_thickness, 'MM', 'IN'))
            vent.append( PHPP_XL_Obj('Additional Vent',  'I{}'.format(row+1), exhaust_system.duct_02.insulation_lambda, 'W/MK', 'HR-FT2-F/BTU-IN'))
            vent.append( PHPP_XL_Obj('Additional Vent',  'J{}'.format(row+1), 'x' ))# Reflective
            vent.append( PHPP_XL_Obj('Additional Vent',  'L{}'.format(row+1), exhaust_system.duct_02.duct_length, 'M', 'FT'))
            vent.append( PHPP_XL_Obj('Additional Vent',  'N{}'.format(row+1), '1'))
            
            vent.append( PHPP_XL_Obj('Additional Vent',  '{}{}'.format(chr(ductColCount), row) , 1)) # Assign Duct to Vent
            vent.append( PHPP_XL_Obj('Additional Vent',  '{}{}'.format(chr(ductColCount), row+1) , 1)) # Assign Duct to Vent
            
            
            
            ductColCount+=1
            ductsCount+=2
            ventCount+=1

    return vent

def get_infiltration(_inputBranch, _zones_to_include):
    #---------------------------------------------------------------------------
    # Envelope Airtightness
    
    # Defaults
    Coef_E = 0.07
    Coef_F  = 15
    bldgWeightedACH = None
    bldgVn50 = None
    
    #---------------------------------------------------------------------------
    # Find the Floor-Area Weighted Average ACH of the Zones
    space_vn50s = []
    spaces_weighted_airflows = []
    
    for phpp_space in _inputBranch:
        if phpp_space.ZoneName not in _zones_to_include:
            continue
        
        spaces_weighted_airflows.append( phpp_space.n50 * phpp_space.vn50 )
        space_vn50s.append( phpp_space.vn50 )
    
    #---------------------------------------------------------------------------
    bld_vn50 = sum(space_vn50s)
    bldg_weighted_ACH = sum(spaces_weighted_airflows) / bld_vn50
    
    #---------------------------------------------------------------------------
    airtightness = []
    print("Creating the Airtightness Objects...")
    airtightness.append(PHPP_XL_Obj('Ventilation', 'N25', Coef_E if Coef_E else float(0.07) ))                      # Wind protection E
    airtightness.append(PHPP_XL_Obj('Ventilation', 'N26', Coef_F if Coef_F else float(15) ))                        # Wind protection F
    airtightness.append(PHPP_XL_Obj('Ventilation', 'N27', bldg_weighted_ACH if bldg_weighted_ACH else float(0.6) )) # ACH50
    airtightness.append(PHPP_XL_Obj('Ventilation', 'P27', bld_vn50 if bld_vn50 else '=N9*1.2', 'M3', 'FT3' ))       #  Internal Reference Volume
    
    return airtightness

def get_ground(_ground_objs, _zones):
    
    ground = []
    
    colLetter = {
        0: {'col0':'C', 'col1':'H', 'col2':'P'},
        1: {'col0':'W', 'col1':'AB', 'col2':'AJ'},
        2: {'col0':'AQ', 'col1':'AV', 'col2':'BD'}
        }
    
    if len(_ground_objs) == 0:
        return ground
    
    if len(_ground_objs) > 3:
        FloorElementsWarning= 'Warning: (grndFloorElements_) PHPP accepts only up to 3 unique \n'\
        'ground contact Floor Elements. Please simplify / consolidate your Floor Elements\n'\
        'before proceeding with export. For now only the first three Floor Elements\n'\
        'will be exported to PHPP.'
        ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, FloorElementsWarning)
        _ground_objs = _ground_objs[0:3]
    
    for i, ground_obj in enumerate(_ground_objs):
        if ground_obj == None:
           continue
        
        # Filter for UD zone exclusions
        if ground_obj.host_room_name not in _zones:
            continue
        
        col0 = colLetter[i]['col0']
        col1 = colLetter[i]['col1']
        col2 = colLetter[i]['col2']
        
        ground.append(PHPP_XL_Obj('Ground', col1+'9', ground_obj.soilThermalConductivity, 'W/MK', 'HR-FT2-F/BTU-IN' ))
        ground.append(PHPP_XL_Obj('Ground', col1+'10', ground_obj.soilHeatCapacity, 'MJ/M3K', 'BTU/FT3-F' ))
        ground.append(PHPP_XL_Obj('Ground', col1+'18', ground_obj.floor_area, 'M2', 'FT2' ))
        ground.append(PHPP_XL_Obj('Ground', col1+'19', ground_obj.perim_len, 'M', 'FT' ))
        ground.append(PHPP_XL_Obj('Ground', col2+'17', ground_obj.floor_U_value, 'W/MK', 'HR-FT2-F/BTU' ))
        ground.append(PHPP_XL_Obj('Ground', col2+'18', ground_obj.perim_psi_X_len, 'W/K', 'BTU/HR-F' ))
        ground.append(PHPP_XL_Obj('Ground', col1+'49', ground_obj.groundWaterDepth, 'M', 'FT' ))
        ground.append(PHPP_XL_Obj('Ground', col1+'50', ground_obj.groundWaterFlowrate, 'M/DAY', 'FT/DAY' ))
        
        if '1' in ground_obj.Type:
            # Slab on Grade Type
            ground.append(PHPP_XL_Obj('Ground', col0+'24', 'x' ))
            ground.append(PHPP_XL_Obj('Ground', col0+'29', '' ))
            ground.append(PHPP_XL_Obj('Ground', col0+'32', '' ))
            ground.append(PHPP_XL_Obj('Ground', col0+'38', '' ))
            ground.append(PHPP_XL_Obj('Ground', col1+'25', ground_obj.perimInsulDepth, 'M', 'IN' ))
            ground.append(PHPP_XL_Obj('Ground', col1+'26', ground_obj.perimInsulThick, 'M', 'IN' ))
            ground.append(PHPP_XL_Obj('Ground', col1+'27', ground_obj.perimInsulConductivity, 'W/MK', 'HR-FT2-F/BTU-IN' ))
            if 'V' in ground_obj.perimInsulOrientation.upper():
                ground.append(PHPP_XL_Obj('Ground', col2+'25', '' ))
            else:
                ground.append(PHPP_XL_Obj('Ground', col2+'25', 'x' ))
        elif '2' in ground_obj.Type:
            # Heated Basement
            ground.append(PHPP_XL_Obj('Ground', col0+'24', '' ))
            ground.append(PHPP_XL_Obj('Ground', col0+'29', 'x' ))
            ground.append(PHPP_XL_Obj('Ground', col0+'32', '' ))
            ground.append(PHPP_XL_Obj('Ground', col0+'38', '' ))
            ground.append(PHPP_XL_Obj('Ground', col1+'30', ground_obj.WallHeight_BG, 'M', 'FT' ))
            ground.append(PHPP_XL_Obj('Ground', col2+'30', ground_obj.WallU_BG, 'W/M2K', 'HR-FT2-F/BTU'))
            
        elif '3' in ground_obj.Type:
            # Unheated Basement
            ground.append(PHPP_XL_Obj('Ground', col0+'24', '' ))
            ground.append(PHPP_XL_Obj('Ground', col0+'29', '' ))
            ground.append(PHPP_XL_Obj('Ground', col0+'32', 'x' ))
            ground.append(PHPP_XL_Obj('Ground', col0+'38', '' ))
            ground.append(PHPP_XL_Obj('Ground', col1+'33', ground_obj.WallHeight_AG, 'M', 'FT' ))
            ground.append(PHPP_XL_Obj('Ground', col2+'33', ground_obj.WallU_AG, 'W/M2K', 'HR-FT2-F/BTU' ))
            ground.append(PHPP_XL_Obj('Ground', col1+'34', ground_obj.WallHeight_BG, 'M', 'FT' ))
            ground.append(PHPP_XL_Obj('Ground', col2+'34', ground_obj.WallU_BG, 'W/M2K', 'HR-FT2-F/BTU'  ))
            ground.append(PHPP_XL_Obj('Ground', col2+'35', ground_obj.FloorU, 'W/M2K', 'HR-FT2-F/BTU' ))
            ground.append(PHPP_XL_Obj('Ground', col1+'35', ground_obj.ACH ))
            ground.append(PHPP_XL_Obj('Ground', col1+'36', ground_obj.Volume, 'M3', 'FT3' ))
            
        elif '4' in ground_obj.Type:
            # Suspended Floor overCrawlspace
            ground.append(PHPP_XL_Obj('Ground', col0+'24', '' ))
            ground.append(PHPP_XL_Obj('Ground', col0+'29', '' ))
            ground.append(PHPP_XL_Obj('Ground', col0+'32', '' ))
            ground.append(PHPP_XL_Obj('Ground', col0+'38', 'x' ))
            ground.append(PHPP_XL_Obj('Ground', col1+'39', ground_obj.CrawlU, 'W/M2K', 'HR-FT2-F/BTU'  ))
            ground.append(PHPP_XL_Obj('Ground', col1+'40', ground_obj.WallHeight, 'M', 'FT' ))
            ground.append(PHPP_XL_Obj('Ground', col1+'41', ground_obj.WallU, 'W/M2K', 'HR-FT2-F/BTU'  ))
            ground.append(PHPP_XL_Obj('Ground', col2+'39', ground_obj.VentOpeningArea, 'M2', 'FT2' ))
            ground.append(PHPP_XL_Obj('Ground', col2+'40', ground_obj.windVelocity, 'M/S', 'M/H' ))
            ground.append(PHPP_XL_Obj('Ground', col2+'41', ground_obj.windFactor ))
            
    return ground

def get_DHW_system(_dhw_systems, _hb_rooms):
    #---------------------------------------------------------------------------
    # If more that one system are to be used, combine them into a single system
    
    dhw_systems = {}
    for system in _dhw_systems:
        for room_id in system.rooms_assigned_to:
            if room_id in _hb_rooms:
                dhw_systems[system.id] = system 
    
    dhw_ = None
    if len(dhw_systems.keys())>1:
        dhw_ = combineDHWSystems( dhw_systems )
    else:
        dhw_ = dhw_systems.values()[0]
    
    #---------------------------------------------------------------------------
    # DHW System Excel Objs
    dhwSystem = []
    if dhw_:
        print("Creating the 'DHW' Objects...")
        dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'J146', dhw_.forwardTemp, 'C', 'F'))
        dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'P145', 0, 'C', 'F'))
        dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'P29', 0, 'C', 'F'))
        
        #-----------------------------------------------------------------------
        # Usage Volume
        if dhw_.usage:
            if dhw_.usage.type == 'Res':
                dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'J47', dhw_.usage.demand_showers, 'LITER', 'GALLON' ) )
                dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'J48', dhw_.usage.demand_others, 'LITER', 'GALLON' ) )
            elif dhw_.usage.type == 'NonRes':
                dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'J47', '=Q57', 'LITER', 'GALLON' ))
                dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'J48', '=Q58', 'LITER', 'GALLON' ))
                dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'J58', getattr(dhw_.usage, 'use_daysPerYear') ) )
                dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'J62', 'x' if getattr(dhw_.usage, 'useShowers') != 'False' else '' ))
                dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'J63', 'x' if getattr(dhw_.usage, 'useHandWashing') != 'False' else '' ))
                dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'J64', 'x' if getattr(dhw_.usage, 'useWashStand') != 'False' else '' ))
                dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'J65', 'x' if getattr(dhw_.usage, 'useBidets') != 'False' else '' ))
                dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'J66', 'x' if getattr(dhw_.usage, 'useBathing') != 'False' else '' ))
                dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'J67', 'x' if getattr(dhw_.usage, 'useToothBrushing') != 'False' else '' ))
                dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'J68', 'x' if getattr(dhw_.usage, 'useCooking') != 'False' else '' ))
                dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'J74', 'x' if getattr(dhw_.usage, 'useDishwashing') != 'False' else '' ))
                dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'J75', 'x' if getattr(dhw_.usage, 'useCleanKitchen') != 'False' else '' ))
                dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'J76', 'x' if getattr(dhw_.usage, 'useCleanRooms') != 'False' else '' ))
        
        #-----------------------------------------------------------------------
        # Recirc Piping
        if len(dhw_.circulation_piping)>0:
            dhwSystem.append( PHPP_XL_Obj('Aux Electricity', 'H29', 1 ) ) # Circulator Pump
            
        for colNum, recirc_line in enumerate(dhw_.circulation_piping.values()):
            col = chr(ord('J') + colNum)
            
            if ord(col) <= ord('N'):
                dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', '{}{}'.format(col, 149), recirc_line.length , 'M', 'FT'))
                dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', '{}{}'.format(col, 150), recirc_line.diameter, 'MM','IN') )
                dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', '{}{}'.format(col, 151), recirc_line.insul_thickness, 'MM', 'IN' ) )
                dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', '{}{}'.format(col, 152), recirc_line.insul_relfective ) )
                dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', '{}{}'.format(col, 153), recirc_line.insul_lambda, 'W/MK', 'HR-FT2-F/BTU-IN' ) )
                dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', '{}{}'.format(col, 155), recirc_line.quality ) )
                dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', '{}{}'.format(col, 159), recirc_line.period ) )
            else:
                dhwRecircWarning = "Too many recirculation loops. PHPP only allows up to 5 loops to be entered.\nConsolidate the loops before moving forward"
                ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, dhwRecircWarning)
        
        #-----------------------------------------------------------------------
        # Branch Piping
        for colNum, branch_line in enumerate(dhw_.branch_piping.values()):
            col = chr(ord('J') + colNum)
            
            if ord(col) <= ord('N'):
                dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', '{}{}'.format(col, 167), branch_line.diameter, 'M', 'IN'))
                dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', '{}{}'.format(col, 168), branch_line.length, 'M', 'FT'))
                dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', '{}{}'.format(col, 169), branch_line.tap_points))
                dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', '{}{}'.format(col, 171), branch_line.tap_openings))
                dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', '{}{}'.format(col, 172), branch_line.utilisation))
            else:
                dhwRecircWarning = "Too many branch piping sets. PHPP only allows up to 5 sets to be entered.\nConsolidate the piping sets before moving forward"
                ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, dhwRecircWarning)
        
        #-----------------------------------------------------------------------
        # Tanks
        if dhw_.tank1:
            dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'J186', dhw_.tank1.type))
            dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'J189', 'x' if dhw_.tank1.solar==True else ''))
            dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'J191', dhw_.tank1.hl_rate, 'W/K', 'BTU/HR-F'))
            dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'J192', dhw_.tank1.vol, 'LITER', 'GALLON'))
            dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'J193', dhw_.tank1.stndbyFrac))
            dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'J195', dhw_.tank1.loction))
            dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'J198', dhw_.tank1.locaton_t, 'C', 'F'))
        if dhw_.tank2:
            dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'M186', dhw_.tank2.type) )
            dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'M189', 'x' if dhw_.tank2.solar==True else ''))
            dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'M191', dhw_.tank2.hl_rate, 'W/K', 'BTU/HR-F'))
            dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'M192', dhw_.tank2.vol, 'LITER', 'GALLON'))
            dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'M193', dhw_.tank2.stndbyFrac))
            dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'M195', dhw_.tank2.loction))
            dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'M198', dhw_.tank2.locaton_t, 'C', 'F'))
        if dhw_.tank_buffer:
            dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'P186', dhw_.tank_buffer.type))
            dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'P191', dhw_.tank_buffer.hl_rate, 'W/K', 'BTU/HR-F'))
            dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'P192', dhw_.tank_buffer.vol, 'LITER', 'GALLON'))
            dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'P195', dhw_.tank_buffer.loction))
            dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'P198', dhw_.tank_buffer.locaton_t, 'C', 'F'))
        
    return dhwSystem

def combine_DHW_systems(_dhwSystems):
    def getBranchPipeAttr(_dhwSystems, _attrName, _branchOrRecirc, _resultType):
        # Combine Elements accross the Systems
        results = DataTree[Object]()
        for sysNum, dhwSystem in enumerate(_dhwSystems.values()):
            pipingObj = getattr(dhwSystem, _branchOrRecirc)
            
            for i in range(0, 4):
                try:
                    temp = getattr(pipingObj[i], _attrName)
                    results.Add(temp, GH_Path(i) )
                except: 
                    pass
        
        output = []
        if _resultType == 'Sum':
            for i in range(results.BranchCount):
                output.append( sum( results.Branch(i) ) )
        elif _resultType == 'Average':
            for i in range(results.BranchCount):
                output.append( statistics.mean( results.Branch(i) ) )
        
        return output
    
    def combineTank(_dhwSystems, _tankName):
        # Combine Tank 1s
        hasTank = False
        tankObj = {'type':[], 'solar':[], 'hl_rate':[], 'vol':[],
        'stndbyFrac':[], 'loction':[], 'locaton_t':[]}
        for v in _dhwSystems.values():
            vTankObj = getattr(v, _tankName)
            
            if vTankObj != None:
                hasTank = True
                tankObj['type'].append( getattr(vTankObj, 'type') )
                tankObj['solar'].append( getattr(vTankObj, 'solar') )
                tankObj['hl_rate'].append( getattr(vTankObj, 'hl_rate') )
                tankObj['vol'].append( getattr(vTankObj, 'vol') )
                tankObj['stndbyFrac'].append( getattr(vTankObj, 'stndbyFrac') )
                tankObj['loction'].append( getattr(vTankObj, 'loction') )
                tankObj['locaton_t'].append( getattr(vTankObj, 'locaton_t') )
        
        if hasTank:
            return LBT2PH.dhw.PHPP_DHW_tank(
                                _type = tankObj['type'][0] if len(tankObj['type']) != 0 else None,
                                _solar = tankObj['solar'][0] if len(tankObj['solar']) != 0 else None,
                                _hl_rate = statistics.mean(tankObj['hl_rate']) if len(tankObj['hl_rate']) != 0 else None,
                                _vol = statistics.mean(tankObj['vol']) if len(tankObj['vol']) != 0 else None,
                                _stndby_frac = statistics.mean(tankObj['stndbyFrac']) if len(tankObj['stndbyFrac']) != 0 else None,
                                _loc = tankObj['loction'][0] if len(tankObj['loction']) != 0 else None,
                                _loc_T = tankObj['locaton_t'][0] if len(tankObj['locaton_t']) != 0 else None,
                                )
        else:
            return None
    
    print('Combining together DHW Systems...')
    #Combine Usages
    showers = []
    other = []
    for v in _dhwSystems.values():
        if isinstance(v.usage, LBT2PH.dhw.PHPP_DHW_usage):
            showers.append( getattr(v.usage, 'demand_showers' ) )
            other.append( getattr(v.usage, 'demand_others' ) )
    
    dhwInputs = {'showers_demand_': sum(showers)/len(showers),
    'other_demand_': sum(other)/len(other)}
    
    combinedUsage = LBT2PH.dhw.PHPP_DHW_usage( dhwInputs )
    
    # Combine Branch Pipings
    combined_Diams = getBranchPipeAttr(_dhwSystems, 'diameter', 'branch_piping', 'Average')
    combined_Lens = getBranchPipeAttr(_dhwSystems, 'totalLength', 'branch_piping', 'Sum')
    combined_Taps =  getBranchPipeAttr(_dhwSystems, 'totalTapPoints', 'branch_piping',  'Sum')
    combined_Opens =  getBranchPipeAttr(_dhwSystems, 'tapOpenings', 'branch_piping',  'Average')
    combined_Utils =  getBranchPipeAttr(_dhwSystems, 'utilisation', 'branch_piping',  'Average')
    
    combined_BranchPipings = []
    for i in range(len(combined_Diams)):
        combinedBranchPiping = LBT2PH.dhw.PHPP_DHW_branch_piping(
                                    combined_Diams[i],
                                    combined_Lens[i],
                                    combined_Taps[i],
                                    combined_Opens[i],
                                    combined_Utils[i]
                                   )
        combined_BranchPipings.append( combinedBranchPiping )
    
    # Combine Recirculation Pipings
    hasRecircPiping = False
    recircObj = {'length':[], 'diam':[], 'insulThck':[],
    'insulCond':[], 'insulRefl':[], 'quality':[], 'period':[],}
    for v in _dhwSystems.values():
        circObjs = v.circulation_piping
        if len(circObjs) != 0:
            hasRecircPiping = True
            try:
                recircObj['length'].append( getattr(circObjs[0], 'length'  ) )
                recircObj['diam'].append( getattr(circObjs[0], 'diam'  )) 
                recircObj['insulThck'].append( getattr(circObjs[0], 'insulThck'  ) )
                recircObj['insulCond'].append( getattr(circObjs[0], 'insulCond'  ) )
                recircObj['insulRefl'].append( getattr(circObjs[0], 'insulRefl'  ) )
                recircObj['quality'].append( getattr(circObjs[0], 'quality'  ) )
                recircObj['period'].append( getattr(circObjs[0], 'period'  ) )
            except:
                pass
    
    if hasRecircPiping:
        combined_RecircPipings = [LBT2PH.dhw.PHPP_DHW_RecircPipe(
                        sum(recircObj['length']),
                        statistics.mean(recircObj['diam']) if len(recircObj['diam']) != 0 else None,
                        statistics.mean(recircObj['insulThck']) if len(recircObj['insulThck']) != 0 else None,
                        statistics.mean(recircObj['insulCond']) if len(recircObj['insulCond']) != 0 else None,
                        recircObj['insulRefl'][0] if len(recircObj['insulRefl']) != 0 else None,
                        recircObj['quality'][0] if len(recircObj['quality']) != 0 else None,
                        recircObj['period'][0] if len(recircObj['period']) != 0 else None
                        )]
    else:
        combined_RecircPipings = []
    
    # Combine the Tanks
    tank1 = combineTank(_dhwSystems, 'tank1')
    tank2 = combineTank(_dhwSystems, 'tank2')
    tank_buffer = combineTank(_dhwSystems, 'tank_buffer')
    
    # Build the combined / Averaged DHW System
    combinedDHWSys = LBT2PH.dhw.PHPP_DHW_System(
                         _name='Combined', 
                         _usage=combinedUsage,
                         _fwdT=60, 
                         _pCirc=combined_RecircPipings, 
                         _pBran=combined_BranchPipings, 
                         _t1=tank1, 
                         _t2=tank2, 
                         _tBf=tank_buffer
                         )
    
    return combinedDHWSys



