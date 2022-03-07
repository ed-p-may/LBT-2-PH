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
Used to Set the User Attribute Text values of Rhino Surface objects. Select an
object or set of objects and run. You'll be prompted to enter values for 
Assembly Type (Wall, Floor, etc..), Boundary Conditions and Material Assemblies
The Assembly values come from a PHPP-Style Excel file with a 'Components' 
worksheet to read from Assembly names will read from 'Components[D15:H113]'.
-
EM Mar. 7, 2022
"""

import rhinoscriptsyntax as rs
import Eto
import Rhino
import json
from collections import defaultdict
from copy import deepcopy

__commandname__ = "PHPP_SetSurfaceParams"

class Model:
    
    def __init__(self, selObjs):
        self.selectedObjects = selObjs
    
    def _setAttrIfNotVaries(self, _obj, _key, _val):
        if _val != '<varies>':
            rs.SetUserText(_obj, _key, _val)
    
    def setObjAttrs(self, _dialogVals):
        for eachObj in self.selectedObjects:
            # Formula to auto-set the obj's name in the User Text = '%<ObjectName("{}")>%'
            rs.SetUserText(eachObj, 'Object Name', '%<ObjectName("{}")>%'.format( str(eachObj) ) )            
            
            if 'varies' not in str(_dialogVals.get('srfcName')):
                rs.ObjectName(eachObj, str(_dialogVals.get('srfcName')))
            
            self._setAttrIfNotVaries(eachObj, 'srfType', _dialogVals.get('srfcType'))
            self._setAttrIfNotVaries(eachObj, 'EPBC', _dialogVals.get('srfcEPBC'))
            self._setAttrIfNotVaries(eachObj, 'EPConstruction', _dialogVals.get('srfcAssmbly'))
    
    def getObjAttrs_Exg(self):
        exgNames, exgTypes, exgEPBCs , exgAssmblies = self._getValsForSelectedObjs()
        
        # Check if the existing properties are all the same frame/glass types, or more than one kind present in the selection?
        exgName = '<varies>' if len(set(exgNames))>1 else exgNames[0] 
        exgType = '<varies>' if len(set(exgTypes))>1 else exgTypes[0] 
        exgEPBC = '<varies>' if len(set(exgEPBCs))>1 else exgEPBCs[0]
        exgAssmbly = '<varies>' if len(set(exgAssmblies))>1 else exgAssmblies[0]
        
        return exgName, exgType, exgEPBC, exgAssmbly
    
    def getAssmblyLib(self):
        assmblyLib = []
        
        print("Reading the Rhino Document's Assembly Types...")
        if rs.IsDocumentUserText():
            for eachKey in rs.GetDocumentUserText():
                if 'PHPP_lib_Assmbly' in eachKey:
                    assmblyLib.append( json.loads(rs.GetDocumentUserText(eachKey))['Name'] )
        return assmblyLib
    
    
    def _getObjUserText(self, _obj, _val, _default):
        keys = rs.GetUserText(_obj)
        if _val in keys:
            return rs.GetUserText(_obj, _val)
        else:
            return _default
    
    def _getValsForSelectedObjs(self):
        nms = []
        srf_types = []
        epbcs = []
        assemblies = []
        
        if len(self.selectedObjects)==0:
            return [''], [''], [''], ['']
            
        for eachObj in self.selectedObjects:
            nms.append(rs.ObjectName(eachObj))
            srf_types.append(self._getObjUserText(eachObj, 'srfType', ''))
            epbcs.append(self._getObjUserText(eachObj, 'EPBC', ''))
            assemblies.append(self._getObjUserText(eachObj, 'EPConstruction', ''))
        
        return nms, srf_types, epbcs, assemblies

class View(Eto.Forms.Dialog):
    
    def __init__(self, controller):
        self.controller = controller
        assmblyLib = self.controller.getAssemblyLib()
        exgName, exgType, exgEPBC, exgAssmbly = self.controller.getExistingValues()
        self.groupContent = self.createContent(exgName, exgType, exgEPBC, exgAssmbly, assmblyLib)
        self._setWindowParams()
        self._addContentToWindow()
        self._addOKCancelButtons()
    
    def _getSrfcTypeList(self):
         return ['WALL',
            'UndergroundWall',
            'ROOF',
            'UndergroundCeiling',
            'FLOOR',
            'UndergroundSlab',
            'SlabOnGrade',
            'ExposedFloor',
            'CEILING',
            'AIRWALL',
            'WINDOW',
            'SHADING']
    
    def _getEPBClist(self):
        return ['Ground', 'Adiabatic', 'Outdoors']
    
    def createContent(self, _nm, _type, _epbc, _assm, _assmblyLib):
        groupContent = [
            {'groupName': 'Select:',
            'content':[
                {'name': 'srfcName', 'label':'Surface Name:', 'input':Eto.Forms.TextBox( Text = str(_nm))},
                {'name': 'srfcType', 'label':'Surface Type:', 'input': self._createDropDown(self._getSrfcTypeList(), _type)},
                {'name': 'srfcEPBC', 'label':'EPBC:', 'input': self._createDropDown(self._getEPBClist(), _epbc)},
                {'name': 'srfcAssmbly', 'label':'Select Assembly:', 'input': self._createDropDown(_assmblyLib, _assm)}
                ]
            }]
        
        return groupContent
    
    def _createDropDown(self, _data, _exgValue):
        # type: (list, Any) -> Eto.Forms.DropDown
        """Create a new Eto.Forms.DropDown item based on the input parameters.
        
        Arguments:
            * _data (list): A list of the options to display in the DropDown.
            * _exgValue (Any): The existing value (if any) of the object for the attribute in question.
        
        Returns:
            * Eto.Forms.Dropdown: The new Eto DropDown item
        """
        
        # Prepare the options. Dev Note: Cannot used DataStore.Insert() on MacOS. So have to prepare the list ahead of time.
        dropdown_options = deepcopy(_data)
        dropdown_options.insert(0, _exgValue)
        
        # Build the Dropdown Intem
        dropDownObj = Eto.Forms.DropDown()
        dropDownObj.DataStore = dropdown_options
        dropDownObj.SelectedIndex = 0
        dropDownObj.Size = Eto.Drawing.Size(200, -1)
        
        return dropDownObj
        
    def _setWindowParams(self):
        self.Title = "Set Parameters for the Surface(s) Selected"
        self.Padding = Eto.Drawing.Padding(15)
        self.Resizable = True
    
    def _addContentToWindow(self):
        self.layout = Eto.Forms.DynamicLayout()
        self.layout.Spacing = Eto.Drawing.Size(10,10)
        self.layout = Eto.Forms.DynamicLayout()
        
        for group in self.groupContent:
            groupObj = Eto.Forms.GroupBox(Text = group.get('groupName', ''))
            groupLayout = Eto.Forms.TableLayout()
            groupLayout.Padding = Eto.Drawing.Padding(5) # Offfset from the outside of the Group Edge
            groupLayout.Spacing = Eto.Drawing.Size(15,10) # Spacing between elements
            
            for tableRow in group.get('content', ''):
                try:
                    print "tableRow.get('input')=", tableRow.get('input').DataStore
                except:
                    pass
                
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
        dialogValues = dict()
        for eachEntry in self.groupContent[0]['content']:
            input_attribute_name = eachEntry['name']
            
            try:
                input_index = eachEntry['input'].SelectedIndex
                input_val = eachEntry['input'].DataStore[input_index]
                dialogValues[input_attribute_name] = input_val
            except AttributeError:
                dialogValues[input_attribute_name] = eachEntry['input'].Text
            
        return dialogValues

class Controller:
    
    def __init__(self, selObjs):
        self.model = Model(selObjs)
        self.view = View(self)
    
    def main(self):
        self.view.showWindow()
    
    def OnOKButtonClick(self, sender, e):
        print('Applying the New Properites to Selected')
        dialogValues = self.view.getDialogValues()
        self.model.setObjAttrs(dialogValues)
        self.Update = True
        self.view.Close()
    
    def OnCancelButtonClick(self, sender, e):
        print('Canceled...')
        self.Update = False
        self.view.Close()
    
    def getExistingValues(self):
        return self.model.getObjAttrs_Exg()
    
    def getAssemblyLib(self):
        return self.model.getAssmblyLib()

def RunCommand( is_interactive ):
    print "Setting the name(s) for the selected object(s)"
    dialog = Controller(rs.SelectedObjects())
    dialog.main()

# Use for debuging in editor
#RunCommand(True)