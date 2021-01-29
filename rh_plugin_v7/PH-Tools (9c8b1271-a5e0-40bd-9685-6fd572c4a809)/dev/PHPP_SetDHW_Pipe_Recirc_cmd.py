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
EM Mar. 29, 2020
"""

import rhinoscriptsyntax as rs
import Rhino
import Eto
import json

__commandname__ = "PHPP_SetDHW_Pipe_Recirc"

class Dialog_RecircPipe(Eto.Forms.Dialog):
    
    def OnCancelButtonClick(self, sender, e):
        print('Canceled...')
        self.Update = False
        self.Close()
    
    def OnOKButtonClick(self, sender, e):
        print('Applying Attributes to the Selected Object(s)')
        self.Update = True
        self.Close()
    
    def GetUserInput(self):
        self.pipe_diam_ = self.pipe_diam_ComboBox.Text
        self.insul_thickness_ = self.insul_thickness_ComboBox.Text 
        self.insul_conductivity_ = self.insul_lambda_TextBox.Text
        self.insul_reflective_ = 'Yes' if self.insul_reflective_Checkbox.Checked==True else 'No'
        
        return self.pipe_diam_, self.insul_thickness_, self.insul_conductivity_, self.insul_reflective_
    
    def __init__(self, _exgDiam, _exgInsulThickness, _exgInsulReflective, _exgInsulConductivity):
        
        # Set up the options
        self.diam_options = ["8.255 (3/8in)", "12.700 (1/2in)", "15.875 (5/8in)",  "19.050 (3/4in)", "25.400 (1in)", "31.750 (1-1/4in)", "38.100 (1-1/2)", "50.800 (2in)"]
        self.insul_options = ["8.255 (3/8in)", "12.700 (1/2in)", "15.875 (5/8in)", "19.050 (3/4in)", "25.400 (1in)", "31.750 (1-1/4in)", "38.100 (1-1/2)", "50.800 (2in)"]
        
        self.diam_options_startI = 4
        if _exgDiam != None:
            self.diam_options_startI = 0
            self.diam_options.insert(0, _exgDiam)
        
        self.insul_options_startI = 6
        if _exgInsulThickness != None:
            self.insul_options_startI = 0
            self.insul_options.insert(0, _exgInsulThickness)
        
        insulLambda = _exgInsulConductivity if _exgInsulConductivity != None else 0.04
        insulRefl = False if _exgInsulReflective=='No' else True
        
        # Set up the ETO Dialogue window 
        self.Title = "Set Recirculation Pipe Parameters for Selected..."
        self.Resizable = False
        self.Padding = Eto.Drawing.Padding(10) # Overall inset from window boundary
        
        # Controls
        self.pipe_diam_Label = Eto.Forms.Label(Text = "Pipe Diameter (mm):")
        self.pipe_diam_ComboBox = Eto.Forms.ComboBox()
        self.pipe_diam_ComboBox.DataStore = self.diam_options
        self.pipe_diam_ComboBox.SelectedIndex = self.diam_options_startI
        
        self.insul_thickness_Label = Eto.Forms.Label(Text = "Insulation Thickness (mm):")
        self.insul_thickness_ComboBox = Eto.Forms.ComboBox()
        self.insul_thickness_ComboBox.DataStore = self.insul_options
        self.insul_thickness_ComboBox.SelectedIndex = self.insul_options_startI
        
        self.insul_reflective_Label = Eto.Forms.Label(Text = "Insulation Reflective Coating?:")
        self.insul_reflective_Checkbox = Eto.Forms.CheckBox()
        self.insul_reflective_Checkbox.Checked = insulRefl
        
        self.insul_lambda_Label = Eto.Forms.Label(Text = "Insulation Conductivity (W/mk):")
        self.insul_lambda_TextBox = Eto.Forms.TextBox(Text = str(insulLambda) )
        
        # Layout
        self.layout = Eto.Forms.DynamicLayout()
        
        # Group | Main
        self.groupbox_Main = Eto.Forms.GroupBox(Text = 'PHPP Parameters:')
        self.layout_Group_Main = Eto.Forms.TableLayout()
        self.layout_Group_Main.Padding = Eto.Drawing.Padding(5) # Offfset from the outside of the Group Edge
        self.layout_Group_Main.Spacing = Eto.Drawing.Size(10,5) # Spacing between elements
        
        # Cells
        self.cell_01 = Eto.Forms.TableCell( self.pipe_diam_Label, True)
        self.cell_02 = Eto.Forms.TableCell( self.pipe_diam_ComboBox, True )
        self.cell_03 = Eto.Forms.TableCell( self.insul_thickness_Label, True)
        self.cell_04 = Eto.Forms.TableCell( self.insul_thickness_ComboBox, True )
        self.cell_05 = Eto.Forms.TableCell( self.insul_lambda_Label, True)
        self.cell_06 = Eto.Forms.TableCell( self.insul_lambda_TextBox, True)
        self.cell_07 = Eto.Forms.TableCell( self.insul_reflective_Label, True)
        self.cell_08 = Eto.Forms.TableCell( self.insul_reflective_Checkbox, True)
        
        # Rows
        self.Row01 = Eto.Forms.TableRow([self.cell_01, self.cell_02])
        self.Row02 = Eto.Forms.TableRow([self.cell_03, self.cell_04])
        self.Row03 = Eto.Forms.TableRow([self.cell_05, self.cell_06])
        self.Row04 = Eto.Forms.TableRow([self.cell_07, self.cell_08])
        self.Row01.ScaleHeight = True
        self.Row02.ScaleHeight = True
        self.Row03.ScaleHeight = True
        self.Row04.ScaleHeight = True
        
        # Add Rows
        self.layout_Group_Main.Rows.Add( self.Row01 )
        self.layout_Group_Main.Rows.Add( self.Row02 )
        self.layout_Group_Main.Rows.Add( self.Row03 )
        self.layout_Group_Main.Rows.Add( self.Row04 )
        
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
    exg_pipe_diam = getAttrs( rs.SelectedObjects(), 'pipe_diameter', _defaultVal=None)
    exg_pipe_insulThickness = getAttrs( rs.SelectedObjects(), 'insulation_thickness', _defaultVal=None)
    exg_pipe_insulConductivity = getAttrs( rs.SelectedObjects(), 'insulation_conductivity', _defaultVal=None)
    exg_pipe_insulReflective = getAttrs( rs.SelectedObjects(), 'insulation_reflective', _defaultVal=True)
    
    # Call the Dialog Window
    dialog = Dialog_RecircPipe(exg_pipe_diam, exg_pipe_insulThickness, exg_pipe_insulReflective, exg_pipe_insulConductivity)
    rc = dialog.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow)
    nw_diam, nw_thkns, nw_lambda, nw_reflec = dialog.GetUserInput()
    
    # Get the user-input data
    try:
        update = dialog.Update #True if 'OK', False if 'Cancel'
    except:
        update = False # on any error with the user input
        print('Error. Not changing any object parameters.')
    
    # Apply the User Inputs to the Object's Attributes if update==True
    if update:
        for eachObj in rs.SelectedObjects():
            if 'varies' not in [str(nw_diam),  str(nw_thkns)]:
                setAttrs(eachObj, 'pipe_diameter', str(nw_diam) )
                setAttrs(eachObj, 'insulation_thickness', str(nw_thkns) )
                setAttrs(eachObj, 'insulation_conductivity', str(nw_lambda) )
                setAttrs(eachObj, 'insulation_reflective', str(nw_reflec) )
    
    return 1

# temp for debuggin in editor
#RunCommand(True)