from honeybee.typing import clean_and_id_ep_string
from honeybee_energy.schedule.ruleset import ScheduleRuleset
from honeybee_energy.lib.scheduletypelimits import schedule_type_limit_by_identifier

def create_hb_constant_schedule(_name, _type_limit='Fractional'):
    type_limit = schedule_type_limit_by_identifier( _type_limit )

    schedule = ScheduleRuleset.from_constant_value(
        clean_and_id_ep_string(_name), 1, type_limit)

    schedule.display_name = _name

    return schedule