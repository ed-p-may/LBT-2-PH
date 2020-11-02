from contextlib import contextmanager
import scriptcontext as sc
import Rhino

@contextmanager
def context_rh_doc(_ghdoc):
    ''' Switches the sc.doc to the Rhino Active Doc temporaily '''
    
    try:
        sc.doc = Rhino.RhinoDoc.ActiveDoc
        yield
    finally:
        sc.doc = _ghdoc

def preview_obj(_classObj):
    ''' For looking at the contents of a Class Object '''

    if not hasattr(_classObj, '__dict__'):
    	print('{} object "{}" has no "__dict__" attribute.'.format(type(_classObj), _classObj))
    	return None
    
    print('-------')
    for item_key, item in _classObj.__dict__.items():
        print(item_key, "::", item)
        try:
            for k, v in item.__dict__.items():
                print("   > {} :: {}".format(k, v))
        except:
            pass