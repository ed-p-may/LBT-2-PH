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
This will add parameter values to lines/curves that describe the Thermal Bridge
along that line. This relies on the library imported using the 'PHPP_Library'
command and will let you 'tag' lines/curves with the exposure type and Psi-Value
type. These parameters will be read later on the GH side in order to create
thermal bridge items in the PHPP.
-
EM Mar. 29 2020
"""

import rhinoscriptsyntax as rs
import Rhino
import Eto
import json

__commandname__ = "PHPP_SetThermalBridgeParams"

class Dialog_TB_Properties(Eto.Forms.Dialog):
    
    def getTBLib(self):
        tb_name_list = []
        
        print "Reading the Rhino Document's Thermal Bridge types..."
        if rs.IsDocumentUserText():
            for eachKey in rs.GetDocumentUserText():
                if 'PHPP_lib_TB_' in eachKey:
                    dict = json.loads(rs.GetDocumentUserText(eachKey))
                    tb_name_list.append( dict.get('Name', '') )
        
        return sorted(tb_name_list)
    
    def __init__(self, _exg_edge_typeName=None, _exg_edge_group=None):
        
        self.tb_group_types = ['15: Ambient', '16: Perimeter', '17: FS/BC']
        
        # First, pull in the Assembly library data from the Document's User-Text
        self.tb_name_list = self.getTBLib()
        
        # Set up the ETO Dialogue window
        self.Title = "Thermal Bridge Parameters for Selected Edge(s)..."
        self.Resizable = False
        
        # Create the Primary Controls for the Dialog
        self.tb_TypeName_Label = Eto.Forms.Label(Text = "TB Type:")
        self.tb_TypeName_DDbox = Eto.Forms.DropDown()
        self.tb_TypeName_DDbox.DataStore = self.tb_name_list
        self.tb_TypeName_DDbox.DataStore.Insert(0, _exg_edge_typeName) # For the default
        self.tb_TypeName_DDbox.SelectedIndex = 0
        self.tb_TypeName_DDbox.Width = 250
        
        self.tb_Group_Label = Eto.Forms.Label(Text = "Group Type:")
        self.tb_Group_DDbox = Eto.Forms.DropDown()
        self.tb_Group_DDbox.DataStore = self.tb_group_types
        self.tb_Group_DDbox.DataStore.Insert(0, _exg_edge_group) # For the default
        self.tb_Group_DDbox.SelectedIndex = 0
        self.tb_Group_DDbox.Width = 250
        
        ## Layout
        layout = Eto.Forms.DynamicLayout()
        layout.Spacing = Eto.Drawing.Size(5,10) # Space between (X, Y) all objs in the main window
        layout.Padding = Eto.Drawing.Padding(10) # Overall inset from main window
        
        # Group: Main
        self.groupbox_Main = Eto.Forms.GroupBox(Text = 'Thermal Bridge Attributes:')
        layout_Group_Main = Eto.Forms.DynamicLayout()
        layout_Group_Main.Padding = Eto.Drawing.Padding(5) # Offfset from the outside of the Group Edge
        layout_Group_Main.Spacing = Eto.Drawing.Size(5,5) # Spacing between elements
        layout_Group_Main.AddRow(self.tb_TypeName_Label,self.tb_TypeName_DDbox)
        layout_Group_Main.AddRow(self.tb_Group_Label,self.tb_Group_DDbox)
        
        # Add Groups to Layout
        self.groupbox_Main.Content = layout_Group_Main
        layout.Add(self.groupbox_Main)
        
        # Create the OK / Cancel Buttons
        self.Button_OK = Eto.Forms.Button(Text = 'OK')
        self.Button_OK.Click += self.OnOKButtonClick
        self.Button_Cancel = Eto.Forms.Button(Text = 'Cancel')
        self.Button_Cancel.Click += self.OnCancelButtonClick
        
        # Buttons
        vert = layout.BeginVertical()
        vert.Spacing = Eto.Drawing.Size(10,5)
        layout.AddRow(None, self.Button_Cancel, self.Button_OK, None)
        layout.EndVertical()
        
        # Set the dialog window Content
        self.Content = layout
    
    def OnCancelButtonClick(self, sender, e):
        print('Canceled...')
        self.Update = False
        self.Close()
    
    def OnOKButtonClick(self, sender, e):
        print('Applying Attributes to the Selected Object(s)')
        self.Update = True
        self.Close()
    
    def GetUserInput(self):
        typeName = self.tb_name_list[ self.tb_TypeName_DDbox.SelectedIndex ]# Gets the text for the index num selected
        groupNum = self.tb_group_types[ self.tb_Group_DDbox.SelectedIndex ]# Gets the text for the index num selected
        
        return typeName, groupNum
"""
class Dialog_TB_Properties_Table(Eto.Forms.Dialog):
    
    def getTBLib(self):
        tb_name_list = []
        
        print "Reading the Rhino Document's Thermal Bridge types..."
        if rs.IsDocumentUserText():
            for eachKey in rs.GetDocumentUserText():
                if 'PHPP_lib_TB_' in eachKey:
                    dict = json.loads(rs.GetDocumentUserText(eachKey))
                    tb_name_list.append( dict.get('Name', '') )
        
        return sorted(tb_name_list)
    
    def OnCancelButtonClick(self, sender, e):
        print('Canceled...')
        self.Update = False
        self.Close()
    
    def OnOKButtonClick(self, sender, e):
        print('Applying Attributes to the Selected Object(s)')
        self.Update = True
        self.Close()
    
    def GetUserInput(self):
        typeName = self.tb_name_list[ self.tb_TypeName_DDbox.SelectedIndex ]# Gets the text for the index num selected
        groupNum = self.tb_group_types[ self.tb_Group_DDbox.SelectedIndex ]# Gets the text for the index num selected
        
        return typeName, groupNum
    
    def __init__(self, _exg_edge_typeName=None, _exg_edge_group=None):
        
        self.tb_group_types = ['15: Ambient', '16: Perimeter', '17: FS/BC']
        
        # First, pull in the Assembly library data from the Document's User-Text
        self.tb_name_list = self.getTBLib()
        
        # Set up the ETO Dialogue window
        self.Title = "Thermal Bridge Parameters for Selected Edge(s)..."
        self.Resizable = True
        
        self.tb_TypeName_DDbox = Eto.Forms.DropDown()
        self.tb_TypeName_DDbox.DataStore = self.tb_name_list
        self.tb_TypeName_DDbox.DataStore.Insert(0, _exg_edge_typeName) # For the default
        self.tb_TypeName_DDbox.SelectedIndex = 0
        
        self.label_01 = Eto.Forms.Label(Text = "Label 1")
        self.label_02 = Eto.Forms.Label(Text = "Label 2")
        
        ## Layout
        layout = Eto.Forms.TableLayout()
        
        # Cells
        cell_01 = Eto.Forms.TableCell( self.tb_TypeName_DDbox)
        cell_01.ScaleWidth = True
        cell_02 = Eto.Forms.TableCell( self.label_02) 
        
        # Rows
        Row01 = Eto.Forms.TableRow([cell_01, cell_02])
        
        Row01.ScaleHeight = False
        
        layout.Rows.Add( Row01 )
        #layout.Rows.Add( Eto.Forms.TableRow( cell_02  ))
        
        # Set the dialog window Content
        self.Content = layout
"""
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
    exg_edge_typeName = getAttrs( rs.SelectedObjects(), 'Typename', _defaultVal=None)
    exg_edge_group = getAttrs( rs.SelectedObjects(), 'Group', _defaultVal=None )
    
    # Call the Dialog Window
    dialog = Dialog_TB_Properties(exg_edge_typeName, exg_edge_group)
    rc = dialog.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow)
    new_typename, new_group_number = dialog.GetUserInput()
    
    # Get the user-input data
    try:
        update = dialog.Update #True if 'OK', False if 'Cancel'
    except:
        update = False # on any error with the user input
    
    # Apply the User Inputs to the Object's Attributes if update==True
    if update:
        for eachObj in rs.SelectedObjects():
            if 'varies' not in str(new_typename) or str(new_group_number):
                setAttrs(eachObj, 'Typename', str(new_typename) )
                setAttrs(eachObj, 'Group', str(new_group_number) )
    
    return 1

# temp for debuggin in editor
#RunCommand(True)