"""Offline candidate: recover an edited PC document from an existing bridge plan.

No file I/O and no phone mutation. Integration into the GUI is NOT included.
"""
import copy
from bridge import BridgeError, PLAN_SCHEMA, plan


def recover_edited_pc(phone_snapshot, saved_plan):
    """Return a defensive copy only if the saved plan matches this phone snapshot.

    Supports legacy strict plans and plans generated with progress-reset allowance.
    A valid plan is NOT a phone import payload; the GUI must still require an
    explicit export and a fresh phone-side snapshot check before import.
    """
    if not isinstance(saved_plan, dict) or saved_plan.get('schema') != PLAN_SCHEMA:
        raise BridgeError('expected a bridge plan JSON, not an editor or import file')
    edited = saved_plan.get('edited_pc')
    if not isinstance(edited, dict):
        raise BridgeError('plan is missing edited_pc')
    for reset_allowed in (False, True):
        try:
            expected = plan(phone_snapshot, edited, allow_reset_progress=reset_allowed)
        except (BridgeError, ValueError, TypeError, KeyError):
            continue
        if expected == saved_plan:
            return copy.deepcopy(edited)
    raise BridgeError('plan does not match the supplied phone snapshot and edited_pc')
