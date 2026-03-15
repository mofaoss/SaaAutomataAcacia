# coding:utf-8

from app.framework.application.tasks.periodic_task_specs import get_primary_task_id

def get_mandatory_periodic_task_ids():
    return {get_primary_task_id()}

MANDATORY_PERIODIC_TASK_IDS = {get_primary_task_id()} # Keep for compat if needed, but it will lazy load on first import of this module after discovery
