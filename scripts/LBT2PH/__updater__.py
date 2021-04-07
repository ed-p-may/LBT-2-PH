from contextlib import contextmanager
import os.path
import Grasshopper as gh
import Grasshopper.Kernel as ghK

@contextmanager
def gh_solver_locked():
    """Locks the GH Solver temporarily so some edits can be performed """
    
    try:
        gh_interface = gh.Plugin.GH_RhinoScriptInterface()
        gh.Plugin.GH_RhinoScriptInterface.DisableSolver(gh_interface)
        yield
    except Exception:
        raise
    finally:
        gh.Plugin.GH_RhinoScriptInterface.EnableSolver(gh_interface)

def update_scene_components(_gh_user_path, _ghenv):
    """ Looks through each component in the scene, updates its Code with that of
        the component in the GHUser Directory with the same name.
    """
    
    with gh_solver_locked():
        doc = _ghenv.Component.OnPingDocument()
        components_in_scene = list(doc.Objects)
        
        for scene_component in components_in_scene:
            if scene_component.Category != 'PH-Tools': continue
            if '__' == scene_component.Name[0:2]: continue     
            
            master_compo_path = _gh_user_path + scene_component.Name + '.ghuser'
            if os.path.isfile(master_compo_path):
                master_compo = ghK.GH_UserObject(master_compo_path).InstantiateObject()
                scene_component.Code = master_compo.Code
                print('Updated: {}'.format(scene_component.Name))
            else:
                msg = "Error: Cannot find the Component: '{}'\n"\
                    "in the directory:\n'{}'\n"\
                    "Please check the UserObjects source directory"\
                    "path is correct?".format(scene_component.Name, _gh_user_path)
                raise Exception(msg)
