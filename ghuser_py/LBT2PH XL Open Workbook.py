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
Enables the connection from Rhino to Excel.
> When _run is set to TRUE, this will start up a new instance of Microsoft Excel.
> If valid source and target file paths are provided, a new copy of the source PHPP 
will be created and automatically opened. 
> Once open, this new PHPP can be connected to the 'Write to Excel' or the 'Read 
from Excel' components.
-
Original component design by Jack Hymowitz <https://github.com/jackhymowitz>, 
Pinacle Scholar Summer Research Student, Stevens Institute of Technology
-
March 1, 2021
    Args:
        _run: Set to True to enable the Excel application, False saves the open 
            workbook and stops the application.
        _source_PHPP_filepath: (str) The existing filepath to the PHPP you would 
            like to use as the 'source' for the new one.
        _new_PHPP_filepath: (str) The new filepath to the PHPP you would like to 
            create. If this file does not already exist it will be created by 
            this component when _run==True.
    Returns:
        excel: The Excel COM interface created, or None if not running.
"""

from ghpythonlib.componentbase import executingcomponent as component
import scriptcontext as sc

import LBT2PH
import LBT2PH.__versions__
import LBT2PH.xl_connect

reload( LBT2PH )
reload(LBT2PH.__versions__)
reload( LBT2PH.xl_connect )

ghenv.Component.Name = "LBT2PH XL Open Workbook"
LBT2PH.__versions__.set_component_params(ghenv, dev=False)
#-------------------------------------------------------------------------------

class ThisComponent(component):
    
    def RunScript(self, _run, _source_PHPP_filepath, _new_PHPP_filepath):
        #---- Sort out the file paths
        path_source_file = LBT2PH.xl_connect.FileManager.get_path_source_file(_source_PHPP_filepath, ghenv)
        path_target_file = LBT2PH.xl_connect.FileManager.get_path_target_file(_new_PHPP_filepath, ghenv)
        
        #---- Execute
        if _run and path_source_file and path_target_file:
            LBT2PH.xl_connect.FileManager.make_target_file(path_source_file, path_target_file, ghenv)
            
            #In order for this to close and save properly, the Excel instance needs
            #so stick around even after _run is truned to FALSE. So always refer to
            #the Excel instance saved in sc.sticky['excel']
            excel = sc.sticky.get('excel', None)
            if not excel:
                excel = LBT2PH.xl_connect.ExcelInstance()
                excel.start_new_instance( path_target_file )
                excel.open_workbook()
                excel.load_sheets()
                
                sc.sticky['excel'] = excel
            
        else:
            excel = sc.sticky.pop('excel', None)
            
            if excel:
                excel.save_and_quit()
                excel = None
        
        return excel

