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
Used to set the Treated Floor Area properties of a floor surface. Use on a room
or set of room floor surfaces to designate them as 'room's in the PHPP model. Room
data such as name, number and fresh-air flor rates can also be entered here. This 
data will be read later by the GH side tools in order to establish total zone floor
areas, airflow rates and volumes. Note: Use this to tag *only* the 'floor' surface
for a room, not the entire enclosing volume/shape of the room.
-
EM Jul. 10 2020
"""

import rhinoscriptsyntax as rs
import Eto
import Rhino
import re

__commandname__ = "PHPP_SetSurfaceTFAFactor"

class Dialog_WindowProperties(Eto.Forms.Dialog):
    
    def getRoomCategories(self):
        return [
                '-',
                '21-Single office',
                '22-Group office',
                '23-Open-plan office',
                '24-Meeting',
                '25-Counter area',
                '26-Retail',
                '27-Classroom',
                '28-University auditorium',
                '29-Bedroom',
                '30-Hotel room',
                '31-Canteen',
                '32-Restaurant',
                '33-Kitchen non-residential',
                '34-Kitchen, Storage, Preparation',
                '35-WC, Sanitary',
                '36-Other habitable rooms',
                '37-Secondary areas',
                '38-Circulation area',
                '39-Storage, Services',
                '40-Server room',
                '41-Workshop',
                '42-Theatre auditorium',
                '43-Theatre foyer',
                '44-Theatre stage',
                '45-Fair, Congress',
                '46-Exhibition',
                '47-Library reading room',
                '48-Open access library',
                '49-Library repository',
                '50-Gymnasium',
                '51-Parking garage',
                '52-Public parking garage']
    
    def getLightingControlTypes(self):
        return ['-',
                '1-manual',
                '2-automatic, dimming, permanently on',
                '3-automatic, dimming, not permanently on',
                '4-by bus system']
    
    def __init__(self, _exgTFA, _exgName, _exgNum, _vSup, _vEta, _vTrans, _exgUse, _exgLighting, _exgMotion, _flowType='Boost' ):
        self.tfaFactors = [1.0, 0.6, 0.5, 0]  # Factors for Dropdown List
        self.flowTypes = ['Boost', 'Normal', 'Away']
        self.flowType = _flowType
        self.MotionControls = ['-', 'Yes', 'No']
        self.roomCategories = self.getRoomCategories()
        self.lightingControls = self.getLightingControlTypes()
        
        
        # Setup the Basic Eto Dialog
        self.Title = "Set the Room Information for the Floor Surface(s) Selected"
        self.Resizable = False
        
        # Create the Controls for the Dialog
        self.roomNumberLabel = Eto.Forms.Label(Text = 'Room Number:')
        self.roomNameLabel = Eto.Forms.Label(Text = 'Room Name:')
        self.tfaLabel = Eto.Forms.Label(Text = 'TFA Factor:')
        self.Label_vent = Eto.Forms.Label(Text = 'Fresh Air Ventilation Flow Rates:')
        self.Label_ventType = Eto.Forms.Label(Text = 'Show/Enter Flow Rates for:')
        self.Label_vSup = Eto.Forms.Label(Text = 'Supply:')
        self.Label_vEta = Eto.Forms.Label(Text = 'Extract:')
        self.Label_vTran = Eto.Forms.Label(Text = 'Transfer:')
        self.Label_RoomCategory = Eto.Forms.Label(Text = 'PHPP Room Category:')
        self.Label_LightingControl = Eto.Forms.Label(Text = 'Lighting Control Type:')
        self.Label_MotionDetector = Eto.Forms.Label(Text = 'Motion Detector Used?:')
        
        self.tfaDropDownBox = Eto.Forms.DropDown()
        self.tfaDropDownBox.DataStore = self.tfaFactors
        self.tfaDropDownBox.DataStore.Insert(0, _exgTFA) # For the default
        self.tfaDropDownBox.SelectedIndex = 0
        
        self.roomNumberTextBox = Eto.Forms.TextBox( Text = str(_exgNum) )
        self.roomNameTextBox = Eto.Forms.TextBox( Text = str(_exgName) )
        self.ventTypeDropDown = Eto.Forms.DropDown()
        self.ventTypeDropDown.DataStore = self.flowTypes
        self.ventTypeDropDown.DataStore.Insert(0, _flowType)
        self.ventTypeDropDown.SelectedIndex = 0
        self.txtBox_Vsup = Eto.Forms.TextBox( Text = self.displayFlowValue(_vSup) )
        self.txtBox_Veta = Eto.Forms.TextBox( Text = self.displayFlowValue(_vEta) )
        self.txtBox_Vtran = Eto.Forms.TextBox( Text = self.displayFlowValue(_vTrans) )
        
        self.RoomCategoryDropDownBox = Eto.Forms.DropDown()
        self.RoomCategoryDropDownBox.DataStore = self.roomCategories
        self.RoomCategoryDropDownBox.DataStore.Insert(0, _exgUse) # For the default
        self.RoomCategoryDropDownBox.SelectedIndex = 0
        
        self.LightingDropDownBox = Eto.Forms.DropDown()
        self.LightingDropDownBox.DataStore = self.lightingControls
        self.LightingDropDownBox.DataStore.Insert(0, _exgLighting) # For the default
        self.LightingDropDownBox.SelectedIndex = 0
        
        self.MotionControl = Eto.Forms.DropDown()
        self.MotionControl.DataStore = self.MotionControls
        self.MotionControl.DataStore.Insert(0, _exgMotion) # For the default
        self.MotionControl.SelectedIndex = 0
        
        # Add the Handlers for Unit (cfm  or m3/h) eval
        self.txtBox_Vsup.LostFocus += self.evaluateUnits
        self.txtBox_Veta.LostFocus += self.evaluateUnits
        self.txtBox_Vtran.LostFocus += self.evaluateUnits
        
        self.txtBox_Vsup.Size = Eto.Drawing.Size(50, 25)
        self.txtBox_Veta.Size = Eto.Drawing.Size(50, 25)
        self.txtBox_Vtran.Size = Eto.Drawing.Size(50, 25)
        
        # Add the Handlers for the 'Vent Type' selection (boost, normal, away)
        self.ventTypeDropDown.DropDownClosed += self.evaluateFlowRates
        
        # Create the OK / Cancel Button
        self.Button_OK = Eto.Forms.Button(Text = 'OK')
        self.Button_OK.Click += self.OnOKButtonClick
        self.Button_Cancel = Eto.Forms.Button(Text = 'Cancel')
        self.Button_Cancel.Click += self.OnCancelButtonClick
        
        ## Layout
        self.layout = Eto.Forms.DynamicLayout()
        #layout.Size = Eto.Drawing.Size(500,500) # Width / Height of the window
        self.layout.Spacing = Eto.Drawing.Size(10,10) # Spacing (hori, vert) of the elements in the window
        self.layout.Padding = Eto.Drawing.Padding(15) # Inset from the outer edges of the window
        
        #####################
        # Group: Main
        self.groupbox_Main = Eto.Forms.GroupBox(Text = 'Room Information')
        self.layout_Group_Main = Eto.Forms.DynamicLayout()
        
        self.layout_Group_Main.Padding = Eto.Drawing.Padding(20) # Offfset from the outside of the winddow
        self.layout_Group_Main.Spacing = Eto.Drawing.Size(10,10) # Spacing between elements
        self.layout_Group_Main.AddRow(self.roomNumberLabel, self.roomNumberTextBox)
        self.layout_Group_Main.AddRow(self.roomNameLabel, self.roomNameTextBox)
        self.layout_Group_Main.AddRow(self.tfaLabel, self.tfaDropDownBox)
        
        self.groupbox_Main.Content = self.layout_Group_Main
        self.layout.Add(self.groupbox_Main)
        
        #####################
        # Group: Ventilation
        self.groupbox_Vent = Eto.Forms.GroupBox(Text = 'Fresh Air Flow-Rates (m3/h)')
        self.layout_Group_Vent = Eto.Forms.TableLayout()
        self.layout_Group_Vent.Padding = Eto.Drawing.Padding(5) # Offfset from the outside of the Group Edge
        self.layout_Group_Vent.Spacing = Eto.Drawing.Size(10,5) # Spacing between elements
        
        # Cells
        self.cell_ventType1 = Eto.Forms.TableCell( self.Label_ventType, True)
        self.cell_ventType2 = Eto.Forms.TableCell( self.ventTypeDropDown, True)
        self.cell_02 = Eto.Forms.TableCell( self.Label_vSup, True)
        self.cell_03 = Eto.Forms.TableCell( self.txtBox_Vsup, True)
        self.cell_04 = Eto.Forms.TableCell( self.Label_vEta, True)
        self.cell_05 = Eto.Forms.TableCell( self.txtBox_Veta, True)
        self.cell_06 = Eto.Forms.TableCell( self.Label_vTran, True)
        self.cell_07 = Eto.Forms.TableCell( self.txtBox_Vtran, True)
        
        # Rows
        self.Row_ventType = Eto.Forms.TableRow([self.cell_ventType1, self.cell_ventType2])
        self.Row01 = Eto.Forms.TableRow([self.cell_02, self.cell_03, self.cell_04, self.cell_05, self.cell_06, self.cell_07])
        self.Row01.ScaleHeight = True
        
        # Add Rows
        self.layout_Group_Vent.Rows.Add( self.Row_ventType )
        self.layout_Group_Vent.Rows.Add( self.Row01 )
        
        # Add Layout to the Group
        self.groupbox_Vent.Content = self.layout_Group_Vent
        
        # Add the Group to the Layout
        self.layout.Add(self.groupbox_Vent)
        
        #####################
        # Group: Use Non-Res
        self.groupbox_NonRes = Eto.Forms.GroupBox(Text = 'PHPP Non-Residential Usage Data')
        self.layout_Group_NonRes = Eto.Forms.TableLayout()
        self.layout_Group_NonRes.Padding = Eto.Drawing.Padding(5) # Offfset from the outside of the Group Edge
        self.layout_Group_NonRes.Spacing = Eto.Drawing.Size(10,5) # Spacing between elements
        
        # Cells
        self.cell_08 = Eto.Forms.TableCell( self.Label_RoomCategory, True)
        self.cell_09 = Eto.Forms.TableCell( self.Label_LightingControl, True)
        self.cell_10 = Eto.Forms.TableCell( self.Label_MotionDetector, True)
        self.cell_11 = Eto.Forms.TableCell( self.RoomCategoryDropDownBox, True)
        self.cell_12 = Eto.Forms.TableCell( self.LightingDropDownBox, True)
        self.cell_13 = Eto.Forms.TableCell( self.MotionControl, True)
        
        # Rows
        self.Row02 = Eto.Forms.TableRow([self.cell_08, self.cell_11])
        self.Row03 = Eto.Forms.TableRow([self.cell_09, self.cell_12])
        self.Row04 = Eto.Forms.TableRow([self.cell_10, self.cell_13])
        
        self.Row02.ScaleHeight = True
        self.Row03.ScaleHeight = True
        self.Row04.ScaleHeight = True
        
        # Add Rows
        self.layout_Group_NonRes.Rows.Add( self.Row02 )
        self.layout_Group_NonRes.Rows.Add( self.Row03 )
        self.layout_Group_NonRes.Rows.Add( self.Row04 )
        
        # Add Layout to the Group
        self.groupbox_NonRes.Content = self.layout_Group_NonRes
        
        # Add the Group to the Layout
        self.layout.Add(self.groupbox_NonRes)
        
        #####################
        # Buttons
        self.layout.BeginVertical()
        self.layout.AddRow(None, self.Button_Cancel, self.Button_OK, None)
        self.layout.EndVertical()
        
        # Set the dialog window Content
        self.Content = self.layout
    
    def displayFlowValue(self, _val):
        """In case <varies> or some other string pops up"""
        
        try:
            return '{:.1f}'.format(float(_val))
        except:
            return str(_val)
    
    def evaluateUnits(self, sender, e):
        """If values are passed including a 'cfm' tag, will
        set the TextBox value to the m3/h equivalent"""
        inputVal = sender.Text.replace(' ', '')
        
        try:
            outputVal = float(inputVal)
        except:
            # Pull out just the decimal characters
            for each in re.split(r'[^\d\.]', inputVal):
                if len(each)>0:
                    outputVal = each
            
            # Convert to m3/h if necessary
            if 'cfm' in inputVal:
                outputVal = float(outputVal) * 1.699010796 #cfm--->m3/h
        
        sender.Text = '{:.1f}'.format(outputVal)
    
    def convertFlowRates(self, _oldFlowType, _newFlowType, val):
        # Coversion factors between types
        schema = {  'Boost':{
                        'Boost': 1,
                        'Normal': 1.298701299,
                        'Away': 2.5},
                    'Normal':{
                        'Boost': 0.77,
                        'Normal': 1,
                        'Away': 1.925},
                    'Away':{
                        'Boost': 0.4,
                        'Normal': 0.519480519,
                        'Away': 1}
                    }
        
        if 'varies' not in val:
            return float(val) * schema[_newFlowType][_oldFlowType]
        else:
            return val
    
    def evaluateFlowRates(self, sender, e):
        """If the user changes the flow rate type, 
        adjust the values in the text boxes. Assumes:
            Boost = 100% fan speed
            Normal = 77% fan speed
            Away = 40% fan speed
        """
        oldFlowType = self.flowType
        newFlowType = self.flowTypes[self.ventTypeDropDown.SelectedIndex]
        
        # Convert the Flow values
        self.txtBox_Vsup.Text = self.displayFlowValue(self.convertFlowRates(oldFlowType, newFlowType, self.txtBox_Vsup.Text) )
        self.txtBox_Veta.Text = self.displayFlowValue(self.convertFlowRates(oldFlowType, newFlowType, self.txtBox_Veta.Text) )
        self.txtBox_Vtran.Text = self.displayFlowValue(self.convertFlowRates(oldFlowType, newFlowType, self.txtBox_Vtran.Text) )
        
        # Reset the Object level FlowType
        self.flowType = newFlowType
        print(oldFlowType, '---->', newFlowType)
    
    def GetUserInput(self):
        num = self.roomNumberTextBox.Text
        name = self.roomNameTextBox.Text
        tfaFac = self.tfaFactors[ self.tfaDropDownBox.SelectedIndex ]# Gets the text for the index num selected
        vSup_ = self.convertFlowRates(self.flowType, 'Boost', self.txtBox_Vsup.Text)
        vEta_ = self.convertFlowRates(self.flowType, 'Boost', self.txtBox_Veta.Text)
        vTran_ = self.convertFlowRates(self.flowType, 'Boost', self.txtBox_Vtran.Text)
        
        useType_ = self.roomCategories[self.RoomCategoryDropDownBox.SelectedIndex]
        lightingControl_ = self.lightingControls[self.LightingDropDownBox.SelectedIndex]
        motionDetector_ = self.MotionControls[self.MotionControl.SelectedIndex]
        
        return num, name, tfaFac, vSup_, vEta_, vTran_, useType_, lightingControl_, motionDetector_
    
    def OnCancelButtonClick(self, sender, e):
        print 'Canceled...'
        self.Update = False
        self.Close()
    
    def OnOKButtonClick(self, sender, e):
        print 'Applying the New Properites to Selected'
        self.Update = True
        self.Close()
        
    def GetUpdateStatus(self):
        return self.Update

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
    # First, get any properties of the existing object(s)
    tfa_Exg = getAttrs( rs.SelectedObjects(), 'TFA_Factor', _defaultVal=1 )
    name_Exg = getAttrs( rs.SelectedObjects(), 'Object Name', _defaultVal=None )
    number_Exg = getAttrs( rs.SelectedObjects(), 'Room_Number', _defaultVal=None )
    v_sup_Exg = getAttrs( rs.SelectedObjects(), 'V_sup', _defaultVal=0 )
    v_eta_Exg = getAttrs( rs.SelectedObjects(), 'V_eta', _defaultVal=0 )
    v_trans_Exg = getAttrs( rs.SelectedObjects(), 'V_trans',_defaultVal=0  )
    use_Exg = getAttrs( rs.SelectedObjects(), 'useType',_defaultVal='-'  )
    lighting_Exg = getAttrs( rs.SelectedObjects(), 'lighting',_defaultVal='-'  )
    motion_Exg = getAttrs( rs.SelectedObjects(), 'motion',_defaultVal='-'  )
    
    # Call the Dialog Window
    dialog = Dialog_WindowProperties( tfa_Exg, name_Exg, number_Exg, v_sup_Exg, v_eta_Exg, v_trans_Exg, use_Exg, lighting_Exg, motion_Exg )
    rc = dialog.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow)
    number_New, name_New, tfa_New, vSup, vEta, vTrans, use, lighting, motion = dialog.GetUserInput()
    
    try:
        update = dialog.GetUpdateStatus() #True if 'OK', False if 'Cancel'
    except:
        update = False # on any error with the user input
    
    # Apply the User Inputs to the Object's Attributes if Update==True
    if update==True:
        for eachObj in  rs.SelectedObjects():
            # Sort out the name
            rs.SetUserText(eachObj, 'Object Name', '%<ObjectName("{}")>%'.format( str(eachObj) ) )# Formula to auto-set the obj's name in Attribute Inspector
            if 'varies' not in str(name_New): rs.ObjectName(eachObj, name_New)
            
            # Set the rest of the Surface Attributes
            if use != '<varies>': rs.SetUserText(eachObj, 'useType', use)
            if lighting != '<varies>': rs.SetUserText(eachObj, 'lighting', lighting)
            if motion != '<varies>': rs.SetUserText(eachObj, 'motion', motion)
            if number_New != '<varies>': rs.SetUserText(eachObj, 'Room_Number', number_New)
            if str(tfa_New) != '<varies>': rs.SetUserText(eachObj, 'TFA_Factor', str(tfa_New))
            if str(vSup) != '<varies>': rs.SetUserText(eachObj, 'V_sup', str(vSup))
            if str(vEta) != '<varies>': rs.SetUserText(eachObj, 'V_eta', str(vEta))
            if str(vTrans) != '<varies>': rs.SetUserText(eachObj, 'V_trans', str(vTrans))
            
    return 0

# temp for debuggin in editor
#RunCommand(True)