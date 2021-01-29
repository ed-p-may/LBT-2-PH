#
# LBT2PH: A Plugin for creating Passive House Planning Package (PHPP) models from LadybugTools. Created by blgdtyp, llc
# 
# This component is part of the PH-Tools toolkit <https://github.com/PH-Tools>.
# 
# Copyright (c) 2020, bldgtyp, llc <phtools@bldgtyp.com> 
# LBT2PH is free software; you can redistribute it and/or modify 
# it under the terms of the GNU General Public License as published 
# by the Free Software Foundation; either version 3 of the License, 
# or (at your option) any later version. 
# 
# LBT2PH is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the 
# GNU General Public License for more details.
# 
# For a copy of the GNU General Public License
# see <http://www.gnu.org/licenses/>.
# 
# @license GPL-3.0+ <http://spdx.org/licenses/GPL-3.0+>
#
"""
Use this command on a selected line(s) to add DHW Recirculation parameters to 
the curve. This includes pipe diameter, insultion, etc.. This data will be 
useful later for the GH side tools to read. This is for the RECIRCULATION pipes
only - not for the branch piping. That is all done in the GH tool only.
-
EM Aug. 19, 2020
"""

import rhinoscriptsyntax as rs
import Rhino
import Eto
import json
import re

__commandname__ = "PHPP_SetERVduct"

class Dialog_HRVduct(Eto.Forms.Dialog):
    
    schema = {
            'M':{'SI': 1, 'M':1, 'CM':0.01, 'MM':0.001, 'FT':0.3048, "'":0.3048, 'IN':0.0254, '"':0.0254},
            'CM':{'SI': 1, 'M':100, 'CM':1, 'MM':0.1, 'FT':30.48, "'":30.48, 'IN':2.54, '"':2.54},
            'MM':{'SI': 1, 'M':1000, 'CM':10, 'MM':1, 'FT':304.8, "'":304.8, 'IN':25.4, '"':25.4},
            'W/M2K':{'SI':1, 'IP':5.678264134}, # IP=Btu/hr-sf-F
            'W/MK':{'SI':1, 'IP':1.730734908}, #IP=Btu/hr-ft-F
            'M3':{'SI':1, 'FT3':0.028316847},
          }
    
    def convertValueToMetric(self, _inputString, _outputUnit):
        """ Will convert a string such as "12 FT" into the corresponding Metric unit
        
        Arguments:
            _inputString: String: The input value from the user
            _outputUnit: String: ('M', 'CM', 'MM', 'W/M2K', 'W/MK', 'M3') The desired unit
        """
        inputValue = _inputString
        
        if not _inputString:
            return None
        
        try:
            return str(float(inputValue))
        except:
            try:
                # Pull out just the decimal numeric characters, if any
                for each in re.split(r'[^\d\.]', _inputString):
                    if len(each)>0:
                        inputValue = each
                        break # so it will only take the first number found, "123 ft3" doesn't work otherwise
                
                inputUnit = self.findInputStringUnit(_inputString)
                conversionFactor = self.schema.get(_outputUnit, {}).get(inputUnit, 1)
                return str(float(inputValue) * float(conversionFactor))
            except:
                return str(inputValue)
    
    @staticmethod
    def findInputStringUnit( _in):
        """ Util func  used by the unit converter """
        
        evalString = str(_in).upper()
        
        if 'FT' in evalString or "'" in evalString:
            inputUnit = 'FT'
        elif 'IN' in evalString or '"' in evalString:
            inputUnit = 'IN'
        elif 'MM' in evalString:
            inputUnit = 'MM'
        elif 'CM' in evalString:
            inputUnit = 'CM'
        elif 'M' in evalString and 'MM' not in evalString:
            inputUnit = 'M'
        elif 'IP' in evalString:
            inputUnit = 'IP'
        elif 'FT3' in evalString:
            inputUnit = 'FT3'
        else:
            inputUnit = 'SI'
        
        return inputUnit
    
    def OnCancelButtonClick(self, sender, e):
        print('Canceled...')
        self.Update = False
        self.Close()
    
    def OnOKButtonClick(self, sender, e):
        print('Applying Attributes to the Selected Object(s)')
        self.Update = True
        self.Close()
    
    def GetUserInput(self):
        self.pipe_diam_ = self.diam_TextBox.Text
        self.insul_thickness_ = self.insul_thickness_TextBox.Text 
        self.insul_conductivity_ = self.insul_lambda_TextBox.Text
        
        return self.pipe_diam_, self.insul_thickness_, self.insul_conductivity_
    
    def evalInput(self, sender, e):
        sender.Text = self.convertValueToMetric(sender.Text, sender.Tag)
    
    def __init__(self, _exgDiam, _exgInsulThickness, _exgInsulConductivity):
        
        diam = _exgDiam if _exgDiam != None else 152.4
        insulThickness = _exgInsulThickness if _exgInsulThickness != None else 38.1
        insulLambda = _exgInsulConductivity if _exgInsulConductivity != None else 0.04
        
        # Set up the ETO Dialogue window 
        self.Title = "Set ERV Duct Parameters for Selected..."
        self.Resizable = False
        self.Padding = Eto.Drawing.Padding(10) # Overall inset from window boundary
        
        # Controls
        self.diam_Label = Eto.Forms.Label(Text = "Pipe Diameter (mm):")
        self.diam_TextBox = Eto.Forms.TextBox(Text = str(diam))
        self.diam_TextBox.LostFocus += self.evalInput
        self.diam_TextBox.Tag = 'MM'
        
        self.insul_thickness_Label = Eto.Forms.Label(Text = "Insulation Thickness (mm):")
        self.insul_thickness_TextBox = Eto.Forms.TextBox(Text = str(insulThickness))
        self.insul_thickness_TextBox.LostFocus += self.evalInput
        self.insul_thickness_TextBox.Tag = 'MM'
        
        self.insul_lambda_Label = Eto.Forms.Label(Text = "Insulation Conductivity (W/mk):")
        self.insul_lambda_TextBox = Eto.Forms.TextBox(Text = str(insulLambda) )
        self.insul_lambda_TextBox.LostFocus += self.evalInput
        self.insul_lambda_TextBox.Tag = 'W/MK'
        
        # Layout
        self.layout = Eto.Forms.DynamicLayout()
        
        # Group | Main
        self.groupbox_Main = Eto.Forms.GroupBox(Text = 'HRV Duct Parameters:')
        self.layout_Group_Main = Eto.Forms.TableLayout()
        self.layout_Group_Main.Padding = Eto.Drawing.Padding(5) # Offfset from the outside of the Group Edge
        self.layout_Group_Main.Spacing = Eto.Drawing.Size(10,5) # Spacing between elements
        
        # Cells
        self.cell_01 = Eto.Forms.TableCell( self.diam_Label, True)
        self.cell_02 = Eto.Forms.TableCell( self.diam_TextBox, True )
        self.cell_03 = Eto.Forms.TableCell( self.insul_thickness_Label, True)
        self.cell_04 = Eto.Forms.TableCell( self.insul_thickness_TextBox, True )
        self.cell_05 = Eto.Forms.TableCell( self.insul_lambda_Label, True)
        self.cell_06 = Eto.Forms.TableCell( self.insul_lambda_TextBox, True)
        
        # Rows
        self.Row01 = Eto.Forms.TableRow([self.cell_01, self.cell_02])
        self.Row02 = Eto.Forms.TableRow([self.cell_03, self.cell_04])
        self.Row03 = Eto.Forms.TableRow([self.cell_05, self.cell_06])

        self.Row01.ScaleHeight = True
        self.Row02.ScaleHeight = True
        self.Row03.ScaleHeight = True
        
        # Add Rows
        self.layout_Group_Main.Rows.Add( self.Row01 )
        self.layout_Group_Main.Rows.Add( self.Row02 )
        self.layout_Group_Main.Rows.Add( self.Row03 )
        
        # Create the OK / Cancel Buttons
        self.Button_OK = Eto.Forms.Button(Text = 'OK')
        self.Button_OK.Click += self.OnOKButtonClick
        self.Button_Cancel = Eto.Forms.Button(Text = 'Cancel')
        self.Button_Cancel.Click += self.OnCancelButtonClick
        
        # Add Groups to Layout
        self.groupbox_Main.Content = self.layout_Group_Main
        self.layout.Add(self.groupbox_Main)
        
        # Add the Buttons at the bottom
        self.vert = self.layout.BeginVertical()
        self.vert.Padding = Eto.Drawing.Padding(10)
        self.vert.Spacing = Eto.Drawing.Size(15,0)
        self.layout.AddRow(None, self.Button_Cancel, self.Button_OK, None)
        self.layout.EndVertical()
        
        # Set the dialog window Content
        self.Content = self.layout

def getAttrs(_in, _key, _defaultVal):
    # Takes in a list of Objects (_in) and the key to search for in 
    # User-Text. Returns '<varies>' if more than one value is found for the key
    results = []
    for each in _in:
        if _key == 'Object Name':
            results.append(rs.ObjectName(each))
            # Get the objects Name
        else:
            # Get the User text info
            if rs.IsUserText(each):
                for eachKey in rs.GetUserText(each):
                    if _key in eachKey:
                        results.append(rs.GetUserText(each, _key) )
                        break
    
    if len(set(results))>1:
        return '<varies>'
    else:
        try:
            return results[0]
        except:
            return _defaultVal

def setAttrs(_obj, _key, _val):
    if _val != '<varies>':
        rs.SetUserText(_obj, _key, _val)

def RunCommand( is_interactive ):
    # First, get any properties of the existing object(s) selected
    exg_diam = getAttrs( rs.SelectedObjects(), 'ductWidth', _defaultVal=None)
    exg_insulThickness = getAttrs( rs.SelectedObjects(), 'insulThickness', _defaultVal=None)
    exg_insulConductivity = getAttrs( rs.SelectedObjects(), 'insulConductivity', _defaultVal=None)
    
    # Call the Dialog Window
    dialog = Dialog_HRVduct(exg_diam, exg_insulThickness, exg_insulConductivity)
    rc = dialog.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow)
    nw_width, nw_thkns, nw_lambda = dialog.GetUserInput()
    
    # Get the user-input data
    try:
        update = dialog.Update #True if 'OK', False if 'Cancel'
    except:
        update = False # on any error with the user input
        print('Error. Not changing any object parameters.')
    
    # Apply the User Inputs to the Object's Attributes if update==True
    if update:
        for eachObj in rs.SelectedObjects():
            if 'varies' not in str(nw_width):
                setAttrs(eachObj, 'ductWidth', str(nw_width) )
            if 'varies' not in str(nw_thkns):
                setAttrs(eachObj, 'insulThickness', str(nw_thkns) )
            if 'varies' not in str(nw_lambda):
                setAttrs(eachObj, 'insulConductivity', str(nw_lambda) )
    
    return 1

# Turn on for debugging in editor
#RunCommand(True)