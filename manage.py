#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def _has_runserver_addrport(args):
    options_with_value = {'--settings', '--pythonpath', '--verbosity'}
    skip_next = False

    for arg in args:
        if skip_next:
            skip_next = False
            continue

        if arg in options_with_value:
            skip_next = True
            continue

        if (
            arg.startswith('--settings=')
            or arg.startswith('--pythonpath=')
            or arg.startswith('--verbosity=')
        ):
            continue

        if arg.startswith('-'):
            continue

        return True

    return False


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

    if len(sys.argv) > 1 and sys.argv[1] == 'runserver':
        runserver_args = sys.argv[2:]
        if not _has_runserver_addrport(runserver_args):
            sys.argv.insert(2, '0.0.0.0:8090')

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
