import os
from shutil import copyfile
import Grasshopper.Kernel as ghK
import scriptcontext as sc

import clr
clr.AddReferenceByName('Microsoft.Office.Interop.Excel')
from System.Runtime.InteropServices import Marshal
from Microsoft.Office.Interop import Excel

class FileManager:

    @staticmethod
    def clean_file_path(_input):
        """Tries to clean user-input strings into valid paths"""
        
        if not _input:
            return None
        
        input = unicode(_input).lstrip().rstrip()
        input = os.path.splitext(input)[0]
        if '\\' in input:
            filepath_items = input.split('\\')
            filepath = os.path.sep.join(filepath_items)
            filepath += '.xlsx'
            return filepath
        elif '/' in input:
            filepath_items = input.split('/')
            filepath = os.path.sep.join(filepath_items)
            filepath += '.xlsx'
            return filepath
        else:
            return os.path.abspath(input)
    
    @staticmethod
    def get_path_target_file(_input_path, _ghenv):
        filepath = FileManager.clean_file_path(_input_path)
        
        if not filepath:
            msg = 'Please supply a valid path to a location for the new PHPP file to be saved to.\n'
            _ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Remark, msg )
            return None
        
        return filepath
    
    @staticmethod
    def get_path_source_file(_filepath, _ghenv):
        filepath = FileManager.clean_file_path(_filepath)
        
        if not filepath:
            msg = 'Please supply a valid path to the source PHPP file to use.\n'
            _ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Remark, msg )
            return None
        if not os.path.isfile(filepath):
            msg = 'I cannnot find the source PHPP file at < {} >?\n'\
                  'Please check your path input is correct?' .format( unicode(filepath) )
            _ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, msg )
        
        return filepath   

    @staticmethod
    def make_target_file(_source_path, _target_path, _ghenv):
        """Copies file from source to target path. Makes a new dir if needed"""
        
        if not _source_path and _target_path:
            return None
        
        target_dir = os.path.split(_target_path)[0]

        if not os.path.isdir(target_dir):
            os.mkdir( target_dir )
        
        if not os.path.isfile( _target_path ):
            copyfile(_source_path, _target_path)

        if not os.path.isfile( _target_path ):
            msg = 'Something went wrong copying the source file < {} > into the target\n'\
                'directory < {} >? Check your path inputs and make sure you can write\n'\
                'to the target location?'.format(_source_path, _target_path)
            _ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, msg )


class ExcelInstance:

    def __init__(self):
        self.excel_app = None
        self.active_workbook = None
        self.active_workbook_name = ''
        self.sheets_dict = {}
    
    def start_new_instance(self, _filename):
        self.excel_app = Excel.ApplicationClass()
        self.excel_app.DisplayAlerts = False
        self.excel_app.EnableEvents = False
        self.excel_app.Visible = True
        self.excel_app.ScreenUpdating = True
        self.filename = _filename

    def open_workbook(self):
        self.active_workbook_name = self.filename
        self.active_workbook = self.excel_app.Workbooks.Open(self.filename)
    
    def load_sheets(self):
        self.excel_app.ScreenUpdating = False

        for sheet in self.active_workbook.Worksheets:
            sheet.Unprotect()
            self.sheets_dict[sheet.Name] = sheet
        
        self.excel_app.ScreenUpdating = True

    def save_and_quit(self):
        self.active_workbook = None
        self.active_workbook_name = ''
        
        if self.excel_app:
            self.excel_app.activeWorkbook.Save()
            self.excel_app.activeWorkbook.Close()
            self.excel_app.Quit()
            self.excel = None
    
    def __unicode__(self):
        return u"Excel Instance | Active Worksheet: {self.activeWorkbookName}".format(self=self)
    def __str__(self):
        return unicode(self).encode("utf-8")
    def __repr__(self):
        return "{}( _nm={!r}, _ex={!r}, _activeWorkbook={!r}, _name={!r}".format(
               self.__class__.__name__,
               self.excel_app,
               self.active_workbook,
               self.active_workbook_name )
    def ToString(self):
        return str(self)
