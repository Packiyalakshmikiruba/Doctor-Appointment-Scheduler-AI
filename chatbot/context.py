"""
chatbot/context.py
------------------
Holds the CURRENT request's identity (patient_id/doctor_id/role) using a
contextvar -- so tool functions can enforce "only your own data" WITHOUT
trusting whatever ID the LLM decides to pass as an argument. This is the
actual security boundary; prompt instructions alone are not enough since
an LLM can be persuaded/confused into requesting someone else's data.
"""

from contextvars import ContextVar

_current_patient_id = ContextVar("current_patient_id", default=None)
_current_doctor_id = ContextVar("current_doctor_id", default=None)
_current_role = ContextVar("current_role", default=None)


def set_request_identity(patient_id=None, doctor_id=None, role=None):
    _current_patient_id.set(patient_id)
    _current_doctor_id.set(doctor_id)
    _current_role.set(role)


def get_current_patient_id():
    return _current_patient_id.get()


def get_current_doctor_id():
    return _current_doctor_id.get()


def get_current_role():
    return _current_role.get()


class PermissionDenied(Exception):
    pass