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
Read a list of fields from an Excel workbook.
To configure this module, provide three comma separated lists of the same length 
for the sheet name, cell name, and the label of the result. Alternatively, use 
the form entry option.
-
Original component design by Jack Hymowitz <https://github.com/jackhymowitz>, 
Pinacle Scholar Summer Research Student, Stevens Institute of Technology
-
March 1, 2021
    Args:
        excel: A running excel instance
        sheets: A comma separated list of the worksheet to read from for each output.
        fields: A comma separated list of the cells to read for each output
        labels: A comma separated list of what to  label each read cell
    Returns:
        data: The values of the requested fields in a list of length-2 tuple (label, value)
        text: The information from data written out to a string.
"""

from System import Object
from Grasshopper import DataTree
from Grasshopper.Kernel.Data import GH_Path

from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs
import scriptcontext as sc
import Grasshopper.Kernel as ghK
from math import floor,log10

import LBT2PH.__versions__
reload(LBT2PH.__versions__)

ghenv.Component.Name = "LBT2PH XL Read from Workbook"
LBT2PH.__versions__.set_component_params(ghenv, dev=False)
#-------------------------------------------------------------------------------

class MyComponent(component):
    
    def doRead(self, excel, sheets, fields, labels):
        if sheets:
            sheetsList=sheets.split(",")
            fieldsList=fields.split(",")
            labelsList=labels.split(",")
            
            if len(sheetsList) != len(fieldsList) or len(sheetsList) != len(labelsList):
                msg1 = "Fields and Labels don't match!"
                ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Error, msg1)
                return (None,None)
            
            labelList=[]
            for i in range(len(sheetsList)):
                labelList.append([labelsList[i],sheetsList[i],fieldsList[i]])
        else:
            if not "displayFields" in sc.sticky:
                #msg1 = "No Fields Found!"
                #ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Error, msg1)
                #return (None,None)
                #Default, verification page
                labelList=[
                    ["TFA","Verification","I34"],
                    ["Heating Demand","Verification","I35"],
                    ["Heating Load","Verification","I36"],
                    ["Cooling + Dehum Demand","Verification","I38"],
                    ["Cooling Load","Verification","I39"],
                    ["Frequency of Overheating","Verification","I40"],
                    ["Frequency of excessively high humidity","Verification","I41"],
                    ["Pressurization test result","Verification","I43"],
                    ["Non-Renewable PE","Verification","I53"],
                    ["PER Demand","Verification","I55"],
                    ["PER","Verification","I56"],
                    ["Heating Total","Heating","O27"],
                    ["Cooling Total","Cooling","O28"]
                    ]
            else:
                labelList=sc.sticky["displayFields"]
        
        data = DataTree[Object]() 
        text = ""
        
        for i, cell in enumerate(labelList):
            label=cell[0].strip()
            sheet=cell[1].strip()
            field=cell[2].strip()
            
            if sheet in excel.sheets_dict:
                val=excel.sheets_dict[sheet].Range[field].Value2
                
                if(type(val).__name__=="float" and val!=0): #Round to 4 significant figures
                    val=str(round(val,3-int(floor(log10(abs(val))))))
                data.Add(label, GH_Path(i))
                data.Add(val, GH_Path(i))
                text+=str(label)+": "+str(val)+"\n"
        
        return (data, text)
    
    def RunScript(self, excel, sheets, fields, labels):
        if excel and excel.active_workbook and excel.sheets_dict:
            return self.doRead(excel, sheets, fields, labels)
        
        msg1 = "No Excel Instance!"
        ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, msg1)
        
        return (None, None)
