import math

import LBT2PH
import LBT2PH.spaces

reload(LBT2PH)
reload(LBT2PH.spaces)

class HoneybeeZeroValueError(Exception):
    def __init__(self, _hb_room, _value):
        self.message = "Error: Honeybee Room: {} required data: {} appears to be Zero?".format(_hb_room.display_name, _value)
        super(HoneybeeZeroValueError, self).__init__(self.message)



def get_room_infiltration_rate(_n50, _q50, _blower_pressure, _hb_room, _phpp_space_dict):
    phpp_spaces = [ LBT2PH.spaces.Space.from_dict( dict ) 
                    for dict 
                    in _phpp_space_dict['spaces'].values()  ]

    phpp_spaces_vn50 = sum( [space.space_vn50 for space in phpp_spaces] )
    
    if _n50:
        room_infil_airflow = (phpp_spaces_vn50 * _n50) / 3600  #m3/s
    elif _q50:
        room_infil_airflow = _hb_room.exposed_area * _q50 / 3600
    else:
        room_infil_airflow = _hb_room.exposed_area * _hb_room.properties.energy.infiltration.flow_per_exterior_area / 3600
    
    if phpp_spaces_vn50 == 0.0:
        raise HoneybeeZeroValueError(_hb_room, 'PHPP-Spaces Vn50 Volume')
    if _hb_room.volume == 0.0:
        raise HoneybeeZeroValueError(_hb_room, 'Volume')
    if _hb_room.floor_area == 0.0:
        raise HoneybeeZeroValueError(_hb_room, 'Floor Area')
    if _hb_room.exposed_area == 0.0:
        raise HoneybeeZeroValueError(_hb_room, 'Exposed Exterior Surface Area')

    print('- '*15, 'HB-Room: {}'.format(_hb_room.display_name), '- '*15)
    print('INPUTS:')
    print('  >HB-Room PHPP Space Volumes (Vn50): {:.2f} m3'.format(phpp_spaces_vn50))
    print('  >HB-Room E+ Volume (Gross): {:.1f} m3'.format(_hb_room.volume))
    print(_hb_room.floor_area)
    print('  >HB-Room E+ Floor Area (Gross): {:.1f} m2'.format(_hb_room.floor_area))
    print('  >HB-Room E+ Exposed Surface Area: {:.1f} m2'.format(_hb_room.exposed_area))
    print('  >HB-Room Infiltration Flowrate: {:.2f} m3/hr ({:.4f} m3/s) @ {}Pa'.format(room_infil_airflow*60*60, room_infil_airflow, _blower_pressure))

    return room_infil_airflow, phpp_spaces_vn50

def calc_standard_flow_rate(_room_infil_airflow, _blower_pressure):
    # Flow Rate incorporating Blower Pressure
    # This equation comes from Honeybee. The HB Componet uses a standard pressure
    # at rest of 4 Pascals. 
    
    normal_avg_pressure = 4.0 #Pa
    factor = (math.pow((_blower_pressure/normal_avg_pressure), 0.63))
    standardFlowRate = _room_infil_airflow / factor # m3/s

    return standardFlowRate

