#!/usr/bin/env python

"""Tests for `jupyterbook_to_zendesk` package."""

import pytest

from click.testing import CliRunner
from pprint import pprint

from jupyterbook_to_zendesk import jupyterbook_to_zendesk
from jupyterbook_to_zendesk.commands import build_jupyterbook
from jupyterbook_to_zendesk import cli

import sys


def test_command_line_interface():
    """Test the CLI."""
    runner = CliRunner()
    runner.invoke(cli.command_build)
