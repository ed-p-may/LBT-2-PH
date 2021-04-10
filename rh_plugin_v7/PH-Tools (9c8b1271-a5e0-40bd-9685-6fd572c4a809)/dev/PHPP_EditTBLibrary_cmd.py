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
Creates the input dialog window for all the component library information
such as windows, frames, glasss. This uses a Model-View-Controller configuration
mostly just cus' I wanted to test that out. Might be way overkill for something like
this... but was fun to build.
-
EM September 21, 2020
"""

import rhinoscriptsyntax as rs
import Eto
import Rhino
import json
from collections import defaultdict
from System import Array
from System.IO import File
import System.Windows.Forms.DialogResult
import System.Drawing.Image
import os
import random
from shutil import copyfile
import clr
clr.AddReferenceByName('Microsoft.Office.Interop.Excel, Culture=neutral, PublicKeyToken=71e9bce111e9429c')
from Microsoft.Office.Interop import Excel
import re

__commandname__ = "PHPP_EditTBLibrary"

class Model:
    
    unitsConversionSchema = {
        'W/M2K': {'SI':1, 'IP':5.678264134},
        'M': {'SI': 1, 'M':1, 'CM':0.01, 'MM':0.001, 'FT':0.3048, "'":0.3048, 'IN':0.0254, '"':0.0254},
        'W/MK': {'SI':1, 'IP':1.730734908}
        }
    
    def __init__(self, selObjs):
        self.selectedObjects = selObjs
        self.GroupContent = self.setGroupContent()
        self.setInitialGroupData()
    
    def setInitialGroupData(self):
        for gr in self.GroupContent:
            gr.getDocumentLibraryExgValues()
    
    def updateGroupData(self, _data):
        for gr in self.GroupContent:
            gr.updateGroupData( [v['Data'] for v in _data.values() if gr.LibType == v['LibType']] )
    
    def addBlankRowToGroupData(self, _grID):
        for gr in self.GroupContent:
            if gr.Name == _grID:
                gr.addBlankRowToData()
    
    def _clearDocumentLibValues(self, _keys):
        if not rs.IsDocumentUserText():
            return
            
        for eachKey in rs.GetDocumentUserText():
            for k in _keys:
                if k in eachKey:
                    rs.SetDocumentUserText(eachKey) # no second val = delete
    
    def setDocumentLibValues(self, _data):
        # First, clear out all the existing values in the dict
        keys = set()
        for v in _data.values():
            keys.add(v['LibType'])
        self._clearDocumentLibValues( list(keys) )
        
        # Now add in all the values from the GridView Window
        for k, v in _data.items():
            idNum = self._idAsInt(v['Data']['ID'])
            key = "{}_{:02d}".format( v['LibType'], idNum )
            rs.SetDocumentUserText(key, json.dumps(v['Data']) )
    
    def _idAsInt(self, _in):
        try:
            return int(_in)
        except:
            print 'ID was not an integer?!?! Enter valid Int for ID-Number'
            return 1
    
    def setGroupContent(self):
        # Set up the Content to display
        gr1 = Group()
        gr1.Name = 'Construction Thermal Bridges'
        gr1.ViewOrder = ['ID','Name', 'psiValue', 'fRsi']
        gr1.LibType = 'PHPP_lib_TB'
        gr1.Editable = [False, True, True, True]
        gr1.ColUnit = [None, None, 'w/mk', '-']
        gr1.ColType = ['int', 'str', 'float', 'float']
        gr1.getBlankRow()
        gr1.getDocumentLibraryExgValues()
        
        gr2 = Group()
        gr2.Name = 'Window Psi-Install Types (w/mk)'
        gr2.ViewOrder = ['ID','Name', 'Left', 'Right', 'Bottom', 'Top']
        gr2.LibType = 'PHPP_lib_PsiInstall'
        gr2.Editable = [False, True, True, True, True, True]
        gr2.ColUnit = [None, None, 'w/mk', 'w/mk', 'w/mk', 'w/mk']
        gr2.ColType = ['int', 'str', 'float', 'float', 'float', 'float']
        gr2.getBlankRow()
        gr2.getDocumentLibraryExgValues()
        
        return [gr1, gr2]
    
    def removeRow(self, _grID, _rowID):
        for gr in self.GroupContent:
            if gr.Name == _grID:
                gr.removeRow( _rowID )
    
    def getTBLibAddress(self):
        if rs.IsDocumentUserText():
            return rs.GetDocumentUserText('PHPP_TB_Lib')
        else:
            return '...'
    
    def setLibraryFileAddress(self):
        """ Opens a dialogue window so the use can select a file
        """
        fd = Rhino.UI.OpenFileDialog()
        fd.Filter = "Excel Files (*.xlsx;*.xls)|*.xlsx;*.xls"
        
        #-----------------------------------------------------------------------
        # Add a warning to the user before proceeding
        # https://developer.rhino3d.com/api/rhinoscript/user_interface_methods/messagebox.htm
        msg = "Loading TB parameters from a file will overwrite all "\
        "the TB and Psi-Install values in the current Rhino "\
        "file's library. Be sure you want to do this before proceeding."
        proceed = rs.MessageBox(msg, 1 | 48, 'Warning:')
        if proceed == 2:
            return fd.FileName
        
        #-----------------------------------------------------------------------
        if fd.ShowDialog()!= System.Windows.Forms.DialogResult.OK:
            print 'Load is Canceled...'
            return None
        else:
            rs.SetDocumentUserText('PHPP_TB_Lib', fd.FileName)
            return fd.FileName
    
    def readTBDataFromExcel(self):
        if rs.IsDocumentUserText():
            libPath = rs.GetDocumentUserText('PHPP_TB_Lib')
        
        try:
            if libPath != None:
                # If a Library File is set in the file...
                if os.path.exists(libPath):
                    print 'Reading the Thermal Bridge Library File....'
                    
                    # Make a Temporary copy
                    saveDir = os.path.split(libPath)[0]
                    tempFile = '{}_temp.xlsx'.format(random.randint(0,1000))
                    tempFilePath = os.path.join(saveDir, tempFile)
                    copyfile(libPath, tempFilePath) # create a copy of the file to read from
                    
                    # Open the Excel Instance and File
                    ex = Excel.ApplicationClass()   
                    ex.Visible = False  # False means excel is hidden as it works
                    ex.DisplayAlerts = False
                    workbook = ex.Workbooks.Open(tempFilePath)
                    worksheets = workbook.Worksheets
                    
                    try:
                        xlArray_TBs = None
                        ws_TBs = worksheets['Thermal Bridges']
                        xlArray_TBs = ws_TBs.Range['A2:C100'].Value2
                    except:
                        print 'Could not find a worksheet named "Thermal Bridges" in the taget file?'
                        
                    try:
                        xlArray_Psi = None
                        ws_PsiInst = worksheets['Psi-Installs']
                        xlArray_Psi = ws_PsiInst.Range['B3:F103'].Value2
                    except:
                        print 'Could not find a worksheet named "Psi-Installs" in the target file?'
                    
                    workbook.Close()  # Close the worbook itself
                    ex.Quit()  # Close out the instance of Excel
                    os.remove(tempFilePath) # Remove the temporary read-file
                    
                    # Build the Thermal Bridge Library
                    lib_TBs = []
                    if xlArray_TBs:
                        xlList_TBs = list(xlArray_TBs)
                        for i in range(0, len(xlList_TBs), 3):
                            newAssembly = [xlList_TBs[i],
                                    xlList_TBs[i+1],
                                    xlList_TBs[i+2],
                            ]
                            lib_TBs.append(newAssembly)
                    
                    # Build the Psi-Installs Library
                    lib_PsiInst = []
                    if xlArray_Psi:
                        xlList_Psi = list(xlArray_Psi)
                        for i in range(0, len(xlList_Psi), 5):
                            if xlList_Psi[i] != None:
                                newPsiInstall = [
                                        xlList_Psi[i],
                                        xlList_Psi[i+1],
                                        xlList_Psi[i+2],
                                        xlList_Psi[i+3],
                                        xlList_Psi[i+4]
                                ]
                                lib_PsiInst.append(newPsiInstall)
                    
                return lib_TBs, lib_PsiInst
        except:
            print('Woops... something went wrong reading from the Excel file?')
            return [], []
    
    def addTBDataToDocumentUserText(self, _tbs, _psiInstalls):
        self._clearDocumentLibValues(['PHPP_lib_TB_', 'PHPP_lib_PsiInstall'])
        
        print('Writing New Library elements to the Document UserText....')
        # Write the new Assemblies to the Document's User-Text
        for i, eachTB in enumerate(_tbs):
            if eachTB[0] != None and len(eachTB[0])>0: # Filter our Null values
                newTB = {"Name":eachTB[0],
                        "psiValue":eachTB[1],
                        "fRsi":eachTB[2],
                        "ID": int(i+1)
                        }
                rs.SetDocumentUserText("PHPP_lib_TB_{:02d}".format(i+1), json.dumps(newTB) )
        
        for i, eachPsiInst in enumerate(_psiInstalls):
            if eachPsiInst[0] != None and len(eachPsiInst[0])>0: # Filter our Null values
                newTB = {"Name":eachPsiInst[0],
                        "Left":eachPsiInst[1],
                        "Right":eachPsiInst[2],
                        "Bottom":eachPsiInst[3],
                        "Top":eachPsiInst[4],                        
                        "ID": int(i+1)
                        }
                rs.SetDocumentUserText("PHPP_lib_PsiInstall_{:02d}".format(i+1), json.dumps(newTB) )
    
    
    
    #TODO: Fix / Revise all this eval and read from Excel stuff
    # so that it works like the Component Dialog ones.....
    
    
    
    def _determineInputUnits(self, _inputString):
        # If its just a number, its SI so just pass it along
        # otherwise, pull out the numerical values and the non-numeric values
        # And figure out the units in the str, if any
        
        value = _inputString
        evalString = str(_inputString).upper()
        
        try:
            value = float(_inputString)
            inputUnit = 'SI'
        except:
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
            else:
                inputUnit = 'SI'
            
            # Pull out just the decimal numeric characters, if any
            for each in re.split(r'[^\d\.]', _inputString):
                if len(each)>0:
                    value = each
            
        return (value, inputUnit)
    
    def convertToOutputUnits(self, _inputVal, _inputUnit, _displayColumnUnit):
        """ Converts the user values to the right SI values for the column being edited """
        
        outputUnitFactors = self.unitsConversionSchema.get(str(_displayColumnUnit).upper(), {})
        conversionFactor = outputUnitFactors.get(_inputUnit, 1)
        
        try:
            return float(_inputVal) * float(conversionFactor)
        except:
            return _inputVal
    
    def determineDisplayVal(self, _inputVal, _displayColumnUnit):
        """ Decide how to show the value in the cell """
        
        # If it a 'name' field, don't want to do any conversions
        if _displayColumnUnit is None:
            return _inputVal
        
        try:
            val, inputUnit = self._determineInputUnits(_inputVal)
            displayValue = self.convertToOutputUnits(val, inputUnit, _displayColumnUnit)
            
            return displayValue
        except:
            print 'Something went wrong converting the input value?'
            return _inputVal



class Group:
    """Data Class to hold info about each Group setup"""
    def __init__(self, _nm=None, _vo=None, _lt=None):
        self.Name = _nm
        self.ViewOrder = _vo
        self.LibType = _lt
        self.Layout = None
        self.BlankRow = {}
        self.Data = []
    
    def getDocumentLibraryExgValues(self):
        assmblyLib = {}
        
        if rs.IsDocumentUserText():
            for eachKey in rs.GetDocumentUserText():
                if self.LibType in eachKey:
                    d = json.loads(rs.GetDocumentUserText(eachKey))
                    d['ID'] = self.ensureIDisInt(d['ID'])
                    assmblyLib[d['ID']] = d
        
        if len(assmblyLib.keys()) == 0:
            assmblyLib[1] = self.getBlankRow(1)
        
        self.Data = assmblyLib
        return assmblyLib
    
    def ensureIDisInt(self, _in):
        try:
            return int(_in)
        except:
            return random.randint(100, 999)
    
    def getDataForGrid(self):
        """ Return the obj dict data as lists for GridView DataStore Display
        
        Instead of using a simple List for the DataStore, here I'm using an
        Eto FilterCollection. This is so that later, if the values are changed by a callback
        while the window is running (for the unit conversions) I can just use
        .DataStore.Refresh() to update all the values in the GridView.
        """
        
        outputList = []
        
        for k, v in self.Data.items():
            temp = []
            for field in self.ViewOrder:
                temp.append( v.get(field, '') )
            outputList.append(temp)
        
        if len(outputList) == 0:
            outputList = ['']
            output_FilterCollection = Eto.Forms.FilterCollection[System.Object]()
            output_FilterCollection.AddRange(outputList)
            
            return output_FilterCollection
        else:
            output_FilterCollection = Eto.Forms.FilterCollection[System.Object]()
            output_FilterCollection.AddRange(outputList)
            
            return output_FilterCollection
    
    def updateGroupData(self, _data):
        for item in _data:
            self.Data[item['ID']] = item
    
    def getBlankRow(self, _id=None):
        self.BlankRow = {k:'' for k in self.ViewOrder}
        if _id:
            self.BlankRow['ID'] = int(_id)
        
        return self.BlankRow
    
    def addBlankRowToData(self):
        id = len(self.Data) + 1
        self.Data[id] = self.getBlankRow(id)
    
    def removeRow(self, _rowID):
        # First, build a new dataset without the selected row
        # remember, 'ID' is 1 based, not 0 based
        # Note: In case there are 'gaps' in the dataset where the 'ID' skips over
        # some numnber, first get the keys and then make sure they are sorted
        
        dataKeys = list(self.Data.keys())
        dataKeys.sort()
        
        dataAsList = []
        for key in dataKeys:
            if self.Data.get(key, {'ID':None}).get('ID', None) == _rowID:
                continue
            
            dataAsList.append( self.Data.get(key) )
        
        # In case the user deletes the last row, add back in a single blank one
        if len(dataAsList) == 0:
            self.addBlankRowToData()
        
        # Now turn the new list back into a dict, update the IDs as you go
        newDataDict = {}
        for i, dataRow in enumerate(dataAsList):
            key = i + 1
            dataRow['ID'] = key
            newDataDict[key] = dataRow
        
        self.Data = newDataDict



class View(Eto.Forms.Dialog):
    
    def __init__(self, controller):
        self.controller = controller
        
        self._setWindowParams()
        self.buildWindow()
    
    def buildWindow(self):
        self.layout = self._addContentToLayout()
        self.Content = self._addOKCancelButtons(self.layout)
    
    def showWindow(self):
        self.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow)
    
    def _setWindowParams(self):
        self.Title = "PHPP Thermal Bridge Libraries"
        self.Padding = Eto.Drawing.Padding(15)
        self.Resizable = True
    
    def _getHeaderDisplayName(self, _in):
        headerNames = {'Name': 'Name',
        'psiValue': 'Psi-Value\n(w/mk)',
        'fRsi': 'f-Rsi=0.25\n(%)'
        }
        
        return headerNames.get(_in, _in)
    
    def _addContentToLayout(self):
        layout = Eto.Forms.DynamicLayout()
        layout.Spacing = Eto.Drawing.Size(10,10)
        
        self.groupContent = self.controller.getGroupContent()
        for groupContent in self.groupContent:
            groupContent.Layout = self._createGridLayout(groupContent)
            
            if len(groupContent.Layout.DataStore) == 0:
                continue
            
            for i, data in enumerate(groupContent.Layout.DataStore[0]):
                groupContent.Layout.Columns.Add(self._createGridColumn(groupContent.ViewOrder[i], groupContent.Editable[i], groupContent.ColUnit[i], i))
            
            groupObj = Eto.Forms.GroupBox(Text = groupContent.Name)
            groupObjLayout = Eto.Forms.DynamicLayout()
            groupObjLayout.Add(self._addGridToScrollPanel(groupContent.Layout))
            groupObjLayout = self._addControlButtonsToLayout(groupObjLayout, groupContent)
            
            groupObj.Content = groupObjLayout
            layout.Add(groupObj)
        
        return layout
    
    def _addControlButtonsToLayout(self, _layout, _gr):
        self.Button_Add = Eto.Forms.Button(Text = 'Add Row')
        self.Button_Add.Click += self.controller.OnAddRowButtonClick
        self.Button_Add.ID = _gr.Name
        self.Button_Del = Eto.Forms.Button(Text = 'Remove Selected Row')
        self.Button_Del.Click += self.controller.OnDelRowButtonClick
        self.Button_Del.ID = _gr.Name
        
        # Add the Buttons at the bottom
        self.vert = _layout.BeginVertical()
        self.vert.Padding = Eto.Drawing.Padding(10)
        self.vert.Spacing = Eto.Drawing.Size(15,0)
        _layout.AddRow(None, self.Button_Add, self.Button_Del, None)
        _layout.EndVertical()
        
        return _layout
        
    def _createGridLayout(self, _grContent):
        grid_Layout = Eto.Forms.GridView()
        grid_Layout.ShowHeader = True
        grid_Layout.DataStore = _grContent.getDataForGrid()
        grid_Layout.ShowCellBorders = True
        grid_Layout.CellEdited += self.controller.evalInput
        
        return grid_Layout
    
    def _createGridColumn(self, grpContent, _editable, _unit, count):
        column = Eto.Forms.GridColumn()
        column.HeaderText = self._getHeaderDisplayName(grpContent)
        column.Editable = _editable
        column.Sortable = True
        column.Width = 125
        column.AutoSize = True
        column.DataCell = Eto.Forms.TextBoxCell(count)
        column.Properties['ColumnUnit'] = _unit
        
        return column
    
    def _addGridToScrollPanel(self, _grContent):
        Scroll_panel = Eto.Forms.Scrollable()
        Scroll_panel.ExpandContentWidth = True
        Scroll_panel.ExpandContentHeight = True
        Scroll_panel.Size = Eto.Drawing.Size(600, 200)
        Scroll_panel.Content = _grContent
        
        return Scroll_panel
        
    def _addOKCancelButtons(self, _layout):
        # Create the OK / Cancel Button
        self.Button_LoadLib = Eto.Forms.Button(Text = 'Import From Libary File...')
        self.Button_LoadLib.Click += self.controller.OnLoadLibButtonClick
        self.Lib_txtBox = Eto.Forms.TextBox( Text = self.controller.getTBLibraryFileAddress() )
        self.Lib_txtBox.Width=200
        
        self.Button_OK = Eto.Forms.Button(Text = 'OK')
        self.Button_OK.Click += self.controller.OnOKButtonClick
        self.Button_Cancel = Eto.Forms.Button(Text = 'Cancel')
        self.Button_Cancel.Click += self.controller.OnCancelButtonClick
        
        # Add the Buttons at the bottom
        self.vert = _layout.BeginVertical()
        self.vert.Padding = Eto.Drawing.Padding(10)
        self.vert.Spacing = Eto.Drawing.Size(15,0)
        _layout.AddRow(None, self.Button_LoadLib, self.Lib_txtBox, None, None, self.Button_Cancel, self.Button_OK, None)
        _layout.EndVertical()
        
        return _layout
    
    def _cleanInput(self, _in, _type='str'):
        """Cast input data correctly"""
        
        castToType = {"float": lambda x: float(x),
                "int": lambda x: int(x),
                "str": lambda x: str(x),
                }
        
        if '=' in str(_in):
            try:
                _in = eval(_in.replace('=', ''))
            except:
                pass
        
        try:
            return castToType[_type](_in)
        except:
            return _in
    
    def getGridValues(self):
        dataFromGridItems = {}
        for group in self.groupContent:
            gr_fields = group.ViewOrder
            gr_data = group.Layout.DataStore
            gr_dataTypes = group.ColType
            
            try:
                for dataRow in gr_data:
                    d = {gr_fields[i]: self._cleanInput(dataRow[i], gr_dataTypes[i]) for i in range(len(gr_fields))}
                    
                    if len(d.get('Name')) > 0:
                        tempDict = {}
                        nm = "{}_{}".format(group.LibType, d.get('Name'))
                        
                        tempDict['Name'] = nm
                        tempDict['LibType'] = group.LibType
                        tempDict['Data'] = d
                        
                        dataFromGridItems[nm] = tempDict 
            except:
                return {}             
        
        return dataFromGridItems



class Controller:
    
    def __init__(self, selObjs):
        self.model = Model(selObjs)
        self.view = View(self)
    
    def main(self):
        self.view.showWindow()
    
    def OnOKButtonClick(self, sender, e):
        print("Applying the changes to the file's component library")
        data = self.view.getGridValues()
        self.model.setDocumentLibValues(data)
        self.Update = True
        self.view.Close()
    
    def OnCancelButtonClick(self, sender, e):
        print('Canceled...')
        self.Update = False
        self.view.Close()
    
    def OnLoadLibButtonClick(self, sender, e):
        update = self.view.Lib_txtBox = self.model.setLibraryFileAddress()
        
        if update:
            tbs, psiInstalls = self.model.readTBDataFromExcel()
            self.model.addTBDataToDocumentUserText( tbs, psiInstalls )
            
            self.model.setInitialGroupData()
            self.view.layout.Clear()
            self.view.buildWindow()
    
    def OnAddRowButtonClick(self, sender, e):
        data = self.view.getGridValues()
        self.model.updateGroupData(data)
        self.model.addBlankRowToGroupData(sender.ID)
        self.view.layout.Clear()
        self.view.buildWindow()
    
    def OnDelRowButtonClick(self, sender, e):
        selectedRowData = None
        for gr in self.view.groupContent:
            if gr.Name == sender.ID:
                for each in gr.Layout.SelectedItems:
                    selectedRowData = each
        
        if selectedRowData:
            data = self.view.getGridValues()
            self.model.updateGroupData(data)
            self.model.removeRow(sender.ID, selectedRowData[0])
            self.view.layout.Clear()
            self.view.buildWindow()
        
    def getGroupContent(self):
        return self.model.GroupContent
    
    def getTBLibraryFileAddress(self):
        return self.model.getTBLibAddress()
    
    def evalInput(self, sender, e):
        # Determine if the user provides some 'Units' such as 'ft' or 'in' 
        # If so, do the conversion to the right SI value and reset the grid cell value
        
        #print('-'*20)
        #for attr in dir(sender):
            #print attr, '::', getattr(sender, attr)
        
        #print('-'*20)
        #for attr in dir(e):
            #print attr, '::', getattr(e, attr)
        
        #Figure out the correct 'units' for the column being edited
        GridColumn = getattr(e, 'GridColumn')
        colProperties = getattr(GridColumn, 'Properties')
        for each in colProperties:
            if each.Key == 'ColumnUnit':
                colUnit = each.Value
        
        # Get the input value, decide what to do with it
        #print e.Row, e.Column
        #print sender.DataStore.Item[e.Row][e.Column]
        
        inputVal = sender.DataStore.Item[e.Row][e.Column]
        displayVal = self.model.determineDisplayVal(inputVal, colUnit)
        
        # Update with the new value
        sender.DataStore.Item[e.Row][e.Column] = displayVal
        sender.DataStore.Refresh()


def RunCommand( is_interactive ):
    dialog = Controller(rs.SelectedObjects())
    dialog.main()

# Use for debuging in editor
#RunCommand(True)