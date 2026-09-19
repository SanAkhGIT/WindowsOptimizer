"""Compatibility wrappers around the primary WinGet software-update module."""

from modules.software import upgrade_available, upgrade_all as _upgrade_all


def scan():
    return upgrade_available()


def upgrade_all():
    return _upgrade_all()
