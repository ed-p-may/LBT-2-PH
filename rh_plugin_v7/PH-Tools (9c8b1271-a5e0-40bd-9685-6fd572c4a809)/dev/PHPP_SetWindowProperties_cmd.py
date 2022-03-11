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
Used to Set the User Attribute Text values of Rhino window objects. Select an object or set of objects and run. You'll be prompted
to enter values for Frame Type, Glass Type and Install condition (0|1) for the edges of the window. 
The Frame and Glass Type values come from a PHPP-Style Excel file with a 'Components' worksheet to read from
Frames will read from 'Components[IL15:JC113]'. Glazing will read from 'Components[ID15:IG113]'
-
EM Mar. 11, 2022
"""

# Reference:
# https://developer.rhino3d.com/guides/rhinopython/eto-forms-python/https://developer.rhino3d.com/guides/rhinopython/eto-forms-python/
# http://api.etoforms.picoe.ca/html/R_Project_EtoForms.htm

from copy import deepcopy
import rhinoscriptsyntax as rs
import Rhino
import Eto
import json
from collections import defaultdict
import re

__commandname__ = "PHPP_SetWindowProperties"

class Model:
    def __init__(self, selObjs):
        self.selectedObjects = selObjs
    
    def _str2Bool(self, _input):
        # Cus' comes in as text...
        input = str(_input)
        if 'False' in _input:
            return False
        elif 'True' in _input:
            return True
        elif 'Null' in _input:
            return None
    
    def _getObjUserText(self, _obj, _val, _default):
        keys = rs.GetUserText(_obj)
        if _val in keys:
            return rs.GetUserText(_obj, _val)
        else:
            return _default
    
    def _getValsForSelectedObjs(self):
        existingFrameTypes = []
        existingGlazingTypes = []
        exgVarTypes = []
        exgPsiTypes = []
        exgInstDepths = []
        
        if len(self.selectedObjects)==0:
            return [''], [''], [''], [''], ['']
            
        for eachObj in self.selectedObjects:
            existingFrameTypes.append(self._getObjUserText(eachObj, 'FrameType', ''))
            existingGlazingTypes.append(self._getObjUserText(eachObj, 'GlazingType', ''))
            exgVarTypes.append(self._getObjUserText(eachObj, 'VariantType', ''))
            exgPsiTypes.append(self._getObjUserText(eachObj, 'PsiInstallType', ''))
            exgInstDepths.append(self._getObjUserText(eachObj, 'InstallDepth', 0.10))
        
        return existingFrameTypes, existingGlazingTypes, exgVarTypes, exgPsiTypes, exgInstDepths
    
    def _getInstallValuesForSelectedObjs(self):
        exgInstalls_Left = []
        exgInstalls_Right = []
        exgInstalls_Bottom = []
        exgInstalls_Top = []
        
        if len(self.selectedObjects)==0:
            return 'False', 'False', 'False', 'False'
        
        for eachObj in self.selectedObjects:
            exgInstalls_Left.append(self._getObjUserText(eachObj, 'InstallLeft', 'True'))
            exgInstalls_Right.append(self._getObjUserText(eachObj, 'InstallRight', 'True'))
            exgInstalls_Bottom.append(self._getObjUserText(eachObj, 'InstallBottom', 'True'))
            exgInstalls_Top.append(self._getObjUserText(eachObj, 'InstallTop', 'True'))
        
        return exgInstalls_Left, exgInstalls_Right, exgInstalls_Bottom, exgInstalls_Top
    
    def getObjAttrs_Exg(self):
        existingFrameTypes, existingGlazingTypes, exgVarTypes, exgPsiTypes, exgInstDepths = self._getValsForSelectedObjs()
        
        # Check if the existing properties are all the same frame/glass types, or more than one kind present in the selection?
        existingFrameType = '<varies>' if len(set(existingFrameTypes))>1 else existingFrameTypes[0] 
        existingGlazingType = '<varies>' if len(set(existingGlazingTypes))>1 else existingGlazingTypes[0] 
        exgVarType = '<varies>' if len(set(exgVarTypes))>1 else exgVarTypes[0]
        exgPsiType = '<varies>' if len(set(exgPsiTypes))>1 else exgPsiTypes[0]
        exgInstDepth = '<varies>' if len(set(exgInstDepths))>1 else exgInstDepths[0]
        
        return existingFrameType, existingGlazingType, exgVarType, exgPsiType, exgInstDepth
    
    def getLibs(self):
        """
        Looks at the Rhino DocumentUserText to see if there are window libraries, 
        if so, reads them in for use in the comboBox dropdowns
        """
        glazingLib = []
        frameLib = []
        psiLib = []
        variableTypes = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        
        print "Reading the Rhino Document's Glazing and Frame Types..."
        if rs.IsDocumentUserText():
            for eachKey in rs.GetDocumentUserText():
                if 'Glazing' in eachKey:
                    glazingLib.append( json.loads(rs.GetDocumentUserText(eachKey))['Name'] )
                elif 'Frame' in eachKey:
                    frameLib.append( json.loads(rs.GetDocumentUserText(eachKey))['Name'] )
                elif '_PsiInstall_' in eachKey:
                    psiLib.append( json.loads(rs.GetDocumentUserText(eachKey))['Typename'] )
        
        return frameLib, glazingLib, psiLib, variableTypes
    
    def getExgInstalls(self):
        exgInstalls_Left, exgInstalls_Right, exgInstalls_Bottom, exgInstalls_Top = self._getInstallValuesForSelectedObjs()
        
        exgInstalls = []
        exgInstalls.append( None if len(set(exgInstalls_Left))>1 else self._str2Bool(exgInstalls_Left[0]) )
        exgInstalls.append( None if len(set(exgInstalls_Right))>1 else self._str2Bool(exgInstalls_Right[0]) )
        exgInstalls.append( None if len(set(exgInstalls_Bottom))>1 else self._str2Bool(exgInstalls_Bottom[0]) )
        exgInstalls.append( None if len(set(exgInstalls_Top))>1 else self._str2Bool(exgInstalls_Top[0]) )
        
        return exgInstalls
    
    def setObjAttrs(self, _dialogVals):
        for eachObj in self.selectedObjects:
            rs.SetUserText(eachObj, 'Object Name', '%<ObjectName("{}")>%'.format( str(eachObj) ) )# Formula to auto-set the obj's name
            
            if _dialogVals.get('frame') != '<varies>': rs.SetUserText(eachObj, 'FrameType', _dialogVals.get('frame') )
            if _dialogVals.get('glass') != '<varies>': rs.SetUserText(eachObj, 'GlazingType', _dialogVals.get('glass') )
            if _dialogVals.get('variant') != '<varies>': rs.SetUserText(eachObj, 'VariantType', _dialogVals.get('variant') )
            if _dialogVals.get('psiInst') != '<varies>': rs.SetUserText(eachObj, 'PsiInstallType', _dialogVals.get('psiInst') )
            if _dialogVals.get('instDepth') != '<varies>': rs.SetUserText(eachObj, 'InstallDepth', _dialogVals.get('instDepth') )
            
            if str(_dialogVals.get('Left')) != 'None': rs.SetUserText(eachObj, 'InstallLeft', str(_dialogVals.get('Left')))
            if str(_dialogVals.get('Right')) != 'None': rs.SetUserText(eachObj, 'InstallRight', str(_dialogVals.get('Right')))
            if str(_dialogVals.get('Bottom')) != 'None': rs.SetUserText(eachObj, 'InstallBottom', str(_dialogVals.get('Bottom')))
            if str(_dialogVals.get('Top')) != 'None': rs.SetUserText(eachObj, 'InstallTop', str(_dialogVals.get('Top')))
    
    def convertValToMeters(self, _val, _unit):
        schema = {'M':1, 'CM':0.01, 'MM':0.001, 'IN':0.0254, 'FT':0.3048}
        factor = schema.get(_unit, 'M')
        try:
            return float(_val) * float(factor)
        except:
            return _val
    
    def _determineInputUnits(self, _inputString):
        # If its just a number, its in meters so just pass it along
        # otherwise, pull out the numerical values and the non-numeric values
        # And figure out the units in the str, if any
        
        outputVal = _inputString
        evalString = str(_inputString).upper()
        
        try:
            outputVal = float(_inputString)
            outputUnit = 'M'
        except:
            if 'FT' in evalString or "'" in evalString:
                outputUnit = 'FT'
            elif 'IN' in evalString or '"' in evalString:
                outputUnit = 'IN'
            elif 'MM' in evalString:
                outputUnit = 'MM'
            elif 'CM' in evalString:
                outputUnit = 'CM'
            else:
                outputUnit = 'M'
            
            # Pull out just the decimal numeric characters, if any
            for each in re.split(r'[^\d\.]', _inputString):
                if len(each)>0:
                    outputVal = each
            
        return (outputVal, outputUnit)


class View(Eto.Forms.Dialog):
    def __init__(self, controller):
        """
        Use the self.groupContent dict to organize all the elements to be 
        added to the dialog window. 
        """
        self.controller = controller
        frameLib, glazingLib, psiLib, variantTypes = self.controller.getRhinoDocLibraries()
        exgFrame, exgGlaz, exgPsi, exgVariant, exgInstDepth = self.controller.getExistingValues()
        exgLeft, exgRight, exgBottom, exgTop = self.controller.getExistingInstalls()
        
        try:
            self.groupContent = [
                {'groupName': 'Select Window Parameters',
                'content':[
                    {'name': 'frame', 'label':'Select Frame:', 'input':self._createComboBox(frameLib, exgFrame)},
                    {'name': 'glass', 'label':'Select Glazing:', 'input':self._createComboBox(glazingLib, exgGlaz)},
                    {'name': 'variant', 'label':'Variant Type:', 'input':self._createComboBox(variantTypes, exgPsi)},
                    {'name': 'psiInst', 'label':'Psi-Install Type:', 'input':self._createComboBox(psiLib, exgVariant)},
                    {'name': 'instDepth', 'label':'Win Install Depth (m):', 'input':  self._createTextBox(exgInstDepth) }
                    ]
                },
                {'groupName': 'Set the Installed Edges',
                'content':[
                    {'name': 'Left', 'label':'Left:', 'input':self._createCheckBox(exgLeft)},
                    {'name': 'Right', 'label':'Right:', 'input':self._createCheckBox(exgRight)},
                    {'name': 'Bottom', 'label':'Bottom:', 'input':self._createCheckBox(exgBottom)},
                    {'name': 'Top', 'label':'Top:', 'input':self._createCheckBox(exgTop)}
                    ]
                }]
        except Exception as e:
            print(e)

        self._setWindowParams()
        self._addContentToWindow()
        self._addOKCancelButtons()
    
    def _createTextBox(self, _txt):
        txtBox = Eto.Forms.TextBox( Text = str(_txt)) 
        
        # Add an input handler
        txtBox.LostFocus += self.controller.evalInput
        
        return txtBox
    
    def _createComboBox(self, _data, _exgValue):
        
        comboBoxObj = Eto.Forms.ComboBox()

        # Dev Note: DataStore.Insert() does not work on MacOS
        combobox_options = deepcopy(_data)
        combobox_options.insert(0, _exgValue)
        comboBoxObj.DataStore = combobox_options
        comboBoxObj.SelectedIndex = 0
        comboBoxObj.Size = Eto.Drawing.Size(400, -1) # This is what sets Col 2 Width

        return comboBoxObj
    
    def _createCheckBox(self, _checked):
        chckBox = Eto.Forms.CheckBox()
        chckBox.ThreeState = True
        chckBox.Checked = _checked #self.str2Bool(_installs[2])
        
        return chckBox
    
    def _setWindowParams(self):
        self.Title = "Set the PHPP Window Properties for Selected Object(s)"
        self.Padding = Eto.Drawing.Padding(15) # The outside edge of the frame
        self.Resizable = True
    
    def _addContentToWindow(self):
        self.layout = Eto.Forms.DynamicLayout()
        self.layout.Spacing = Eto.Drawing.Size(10,10)
        self.layout = Eto.Forms.DynamicLayout()
        
        for group in self.groupContent:
            groupObj = Eto.Forms.GroupBox(Text = group.get('groupName', ''))
            groupLayout = Eto.Forms.TableLayout()
            groupLayout.Padding = Eto.Drawing.Padding(5) # Offfset from the outside of the Group Edge
            groupLayout.Spacing = Eto.Drawing.Size(10,5) # Spacing between elements
            
            for tableRow in group.get('content', ''):
                groupLayout.Rows.Add(Eto.Forms.TableRow(
                        Eto.Forms.TableCell(Eto.Forms.Label(Text = tableRow.get('label', 'Label Missing'))), 
                        Eto.Forms.TableCell(tableRow.get('input'), None)    
                        ))
            
            groupObj.Content = groupLayout
            self.layout.Add(groupObj)
        
        self.Content = self.layout
    
    def _addOKCancelButtons(self):
        # Create the OK / Cancel Button
        self.Button_OK = Eto.Forms.Button(Text = 'OK')
        self.Button_OK.Click += self.controller.OnOKButtonClick
        self.Button_Cancel = Eto.Forms.Button(Text = 'Cancel')
        self.Button_Cancel.Click += self.controller.OnCancelButtonClick
        
        # Add the Buttons at the bottom
        self.vert = self.layout.BeginVertical()
        self.vert.Padding = Eto.Drawing.Padding(10)
        self.vert.Spacing = Eto.Drawing.Size(15,0)
        self.layout.AddRow(None, self.Button_Cancel, self.Button_OK, None)
        self.layout.EndVertical()
    
    def showWindow(self):
        self.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow)
    
    def getDialogValues(self):
        dialogValues = defaultdict()
        for eachEntry in self.groupContent[0]['content']:
            dialogValues[eachEntry['name']] = eachEntry['input'].Text
        
        for eachEntry in self.groupContent[1]['content']:
            dialogValues[eachEntry['name']] = eachEntry['input'].Checked
        
        return dialogValues


class Controller:
    def __init__(self, selObjs):
        self.model = Model(selObjs)
        self.view = View(self)
    
    def main(self):
        self.view.showWindow()
    
    def getRhinoDocLibraries(self):
        return self.model.getLibs()
    
    def getExistingValues(self):
        return self.model.getObjAttrs_Exg()
    
    def getExistingInstalls(self):
        return self.model.getExgInstalls()
    
    def OnOKButtonClick(self, sender, e):
        print('Applying the properties to the selected object(s)')
        self.Update = True
        dialogValues = self.view.getDialogValues()
        self.model.setObjAttrs(dialogValues)
        self.view.Close()
    
    def OnCancelButtonClick(self, sender, e):
        print('Canceled...')
        self.Update = False
        self.view.Close()
    
    def evalInput(self, sender, e):
        # Determine is the user has input any 'units' such as 'ft' or 'in'
        # If so, do the conversion to meters and reset the TextBox value
        
        #print('-'*20)
        #for attr in dir(sender):
            #print attr, '::', getattr(sender, attr)
        
        if 'Text' in dir(sender):
            txtBoxValue = getattr(sender, 'Text')
            val, unit = self.model._determineInputUnits( txtBoxValue )
            newVal = self.model.convertValToMeters(val, unit)
            sender.Text = str(newVal)


def RunCommand( is_interactive ):
    print "Applying PHPP Window Types to Selected Object(s)"
    dialog = Controller(rs.SelectedObjects())
    dialog.main()


# Use for debuging in editor
#RunCommand(True)