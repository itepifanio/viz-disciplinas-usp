#!/usr/bin/env python3

import argparse
import subprocess
from pathlib import Path

def lock():
    command = 'uv pip compile requirements.in --universal --output-file requirements.txt'.split(" ")
    subprocess.run(
        command,
        check=True
    )

def lock_dev():
    command = 'uv pip compile requirements-dev.in --universal --output-file requirements-dev.txt'.split(" ")
    subprocess.run(command, check=True)

def lock_all():
    """Run both lock and lock-dev commands"""
    lock()
    lock_dev()

def preview():
    """Run the dashboard preview"""
    subprocess.run(['python3', 'src/dashboard/run.py'], check=True)

def main():
    parser = argparse.ArgumentParser(description='CLI tool for viz-disciplinas-usp project management')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    subparsers.add_parser('lock', help='Compile requirements.in to requirements.txt')
    subparsers.add_parser('lock-dev', help='Compile requirements-dev.in to requirements-dev.txt')
    subparsers.add_parser('lock-all', help='Run both lock and lock-dev commands')
    subparsers.add_parser('preview', help='Run the dashboard preview')

    args = parser.parse_args()

    commands = {
        'lock': lock,
        'lock-dev': lock_dev,
        'lock-all': lock_all,
        'preview': preview
    }

    if args.command in commands:
        commands[args.command]()
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
