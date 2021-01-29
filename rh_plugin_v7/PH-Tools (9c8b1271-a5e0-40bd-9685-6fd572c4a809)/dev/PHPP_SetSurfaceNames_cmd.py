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
This is a helper tool to autoname any objects in Rhino. It will take a set of
selected objects and name them 1..2..3..4.. etc... from left-->right. It figures
out left--->right based on the surface normals and U/V directions of the surfaces. 
That means before using it, be sure to evaluate and standardize ALL the normals
and UV directions of your surfaces! Be sure they are pointing 'out' and that the
V is up, U is to the right. Otherwise it'll name things backwards or in an
unexpected way. Use the native Rhino 'Show Object Direction' tool to review all
the UV and directions.
-
EM Jul. 24 2020
"""

import rhinoscriptsyntax as rs
import Eto
import json
import Rhino
import scriptcontext as sc
from Rhino.Geometry import *
from collections import defaultdict

__commandname__ = "PHPP_SetSurfaceNames"

class Model:
    def __init__(self, selObjs):
        self.selectedObjects = selObjs
    
    def _findWindowPlane(self, _srfcs):
        """
        Takes in a set of surfaces, returns a list of their Centroids in 'order'
        
        Assess the surface normal of the group of surfaces and attempts to 
        figuere out the 'order' of the srfcs when viewed from 'outside' (according
        to the surface normal) and orders the centroids from left--->right
        """
        setXs = []
        setYs = []
        setZs = []
        Centroids = []
        
        for srfc in _srfcs:
            windowBrep = rs.coercebrep(srfc)
            surfaceList =  windowBrep.Surfaces
            for eachSurface in surfaceList:
                srfcCentroid = rs.SurfaceAreaCentroid(eachSurface)[0]
                b, u, v = eachSurface.ClosestPoint(srfcCentroid)
                srfcNormal = eachSurface.NormalAt(u, v)
                setXs.append( srfcNormal.X )
                setYs.append( srfcNormal.Y )
                setZs.append( srfcNormal.Z )
                Centroids.append( srfcCentroid )
        
        # Find the average Normal Vector of the set
        px = sum(setXs) / len(setXs)
        py = sum(setYs) / len(setYs)
        pz = sum(setZs) / len(setZs)
        avgNormalVec = Rhino.Geometry.Point3d(px, py, pz)
        
        # Find a line through all the points and its midpoint
        fitLine = rs.LineFitFromPoints(Centroids)
        
        # Find the Midpoint of the Line
        midX = (fitLine.From.X + fitLine.To.X) / 2
        midY = (fitLine.From.Y + fitLine.To.Y) / 2
        midZ = (fitLine.From.Z + fitLine.To.Z) / 2
        lineMidpoint = Rhino.Geometry.Point3d(midX, midY, midZ)
        
        # Rotate new Plane to match the window avg
        newAvgWindowPlane = rs.CreatePlane(lineMidpoint, avgNormalVec, [0,0,1] )
        finalPlane = rs.RotatePlane(newAvgWindowPlane, 90, [0,0,1])
        
        # Plot the window Centroids onto the selection Set Plane
        centroidsReMaped = []
        for eachCent in Centroids:
            centroidsReMaped.append( finalPlane.RemapToPlaneSpace(eachCent) )
        
        # Return a list of the new Centroids remapped onto the Set's Plane
        return centroidsReMaped
    
    def getStickyValues(self):
        prefix = sc.sticky.get('winName_prefix', '')
        suffix = sc.sticky.get('winName_suffix', '')
        
        return {'Prefix':prefix, 'Suffix':suffix}
    
    def setStickyValues(self, _dialogVals):
        sc.sticky['winName_prefix'] = _dialogVals.get('prefix')
        sc.sticky['winName_suffix'] = _dialogVals.get('suffix')
    
    def _orderSurfaces(self, _srfcs):
        # Sort the surfaces 'Left to Right'
        # when viewed from the 'outside'
        
        if len(_srfcs)>1:
            try:
                centroidSet = self._findWindowPlane(_srfcs)
                orderedSrfcs = [x for _,x in sorted(zip(centroidSet, _srfcs))]
            except:
                print('Error finding the centroids and order of the surfaces.')
                orderedSrfcs = _srfcs
        else:
            orderedSrfcs = _srfcs
        
        return orderedSrfcs
    
    def _filterOutNonSurfaces(self, _srfcs):
        return [s for s in _srfcs if rs.IsSurface(s)]
    
    def setObjAttrs(self, _dialogVals):
        self.setStickyValues(_dialogVals)
        
        surfacesToOrder = self._filterOutNonSurfaces(self.selectedObjects)
        srfcsInOrder = self._orderSurfaces(surfacesToOrder)
        
        # Now that the Surfaces are in order, Set all the names
        for i, srfc in enumerate(srfcsInOrder):
            newName = "{}{}{}".format(_dialogVals.get('prefix'), i+1, _dialogVals.get('suffix'))
            rs.ObjectName(srfc, newName)

class View(Eto.Forms.Dialog):
    
    def __init__(self, controller):
        self.controller = controller
        self.controller.model.getStickyValues()
        self.groupContent = self.createContent()
        self._setWindowParams()
        self._addContentToWindow()
        self._addOKCancelButtons()
    
    def createContent(self):
        _prefix = self.controller.model.getStickyValues().get('Prefix', '')
        _suffix = self.controller.model.getStickyValues().get('Suffix', '')
        note = "Only works for 'Surfaces', no Meshes or Curves.\n"\
               "Be sure the surface normals on all windows\nare pointed 'out'."
        
        
        groupContent = [
            {'groupName': 'Input Name Prefix and Suffix to use (if any)',
            'content':[
                {'name': 'prefix', 'label':'Name Prefix:', 'input':Eto.Forms.TextBox( Text = str(_prefix))},
                {'name': 'suffix', 'label':'Name Suffix:', 'input':Eto.Forms.TextBox( Text = str(_suffix))}
                ]
            },
                {'groupName': '',
                'content':[
                    {'name': 'note', 'label':'Note:', 'input':Eto.Forms.Label(Text = note)}
                    ]
            }]
        
        return groupContent
    
    def _setWindowParams(self):
        self.Title = "Set Names for Selected Surface(s)"
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
    
    def getDialogValues(self):
        dialogValues = defaultdict()
        for eachEntry in self.groupContent[0]['content']:
            dialogValues[eachEntry['name']] = eachEntry['input'].Text
        
        return dialogValues
    
    def showWindow(self):
        self.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow)

class Controller:
    def __init__(self, selObjs):
        self.model = Model(selObjs)
        self.view = View(self)
    
    def main(self):
        self.view.showWindow()
    
    def OnOKButtonClick(self, sender, e):
        print('Applying the New Properites to Selected')
        self.Update = True
        dialogValues = self.view.getDialogValues()
        self.model.setObjAttrs(dialogValues)
        self.view.Close()
    
    def OnCancelButtonClick(self, sender, e):
        print('Canceled...')
        self.Update = False
        self.view.Close()

def RunCommand( is_interactive ):
    print "Setting the name(s) for the selected object(s)"
    
    dialog = Controller(rs.SelectedObjects())
    dialog.main()

# Use for debuging in editor
#RunCommand(True)