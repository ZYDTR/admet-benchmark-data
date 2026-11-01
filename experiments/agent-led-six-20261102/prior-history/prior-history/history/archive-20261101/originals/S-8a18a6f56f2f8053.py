"""Offline-testable sequencing contract for the fixed Skill's read-only client.

This module contains no SSH or upload/start function. A future adapter must use
the fixed Skill route and classify errors there, never classify every exit 255
or every 'Permission denied' as transient.
"""
from common_guarded import now

READ_ONLY_ACTIONS = frozenset(('identity', 'resources', 'workspace'))
BACKOFF_SECONDS = (2, 5, 10)
TRANSIENT_REASONS = frozenset(('connection_timeout', 'connection_reset',
                             'temporarily_unreachable', 'registered_ssh_auth_once'))


class TransientConnectionError(Exception):
    def __init__(self, reason, returncode=None):
        if reason not in TRANSIENT_REASONS:
            raise ValueError('unclassified/hard failure cannot be retried')
        self.reason, self.returncode = reason, returncode
        super().__init__(reason)


def recover_read_only(action, query, validate, sleep, record, context):
    """Inject all I/O. Persist each event before any dependent next operation.

Only query's typed transient connection failures retry. Validation failures
propagate immediately, so a final successful connection cannot mask an earlier
failed identity/environment/resource check. No arbitrary mutation is accepted.
"""
    if action not in READ_ONLY_ACTIONS:
        raise ValueError('operation is outside fixed read-only recovery scope')
    events = []
    for attempt in range(1, 5):
        try:
            value = query(action)
        except TransientConnectionError as error:
            delay = BACKOFF_SECONDS[attempt-1] if attempt < 4 else None
            event = {'at': now(), 'attempt': attempt, 'action': action,
                     'status': 'connection_failed', 'reason': error.reason,
                     'returncode': error.returncode, 'backoff_seconds': delay}
            events.append(event)
            record(event)
            if delay is not None:
                sleep(delay)
                continue
            return {'state': 'waiting_for_connection', 'checks_passed': False,
                    'context': context, 'events': events,
                    'cooldown_seconds_if_already_authorized': 300,
                    'automatic_wakeup_created': False}
        # Intentionally outside the retry catch: failed checks are hard gates.
        try:
            validate(value)
        except Exception as error:
            record({'at': now(), 'attempt': attempt, 'action': action,
                    'status': 'checks_failed', 'error_type': type(error).__name__})
            raise
        event = {'at': now(), 'attempt': attempt, 'action': action,
                 'status': 'checks_passed'}
        events.append(event)
        record(event)
        return {'state': 'ready', 'checks_passed': True, 'value': value,
                'context': context, 'events': events}
    raise RuntimeError('unreachable')
