#!/usr/bin/env python
"""Tests for `jupyterbook_to_zendesk` package."""
import sys
from pprint import pprint

import pytest
from click.testing import CliRunner

from jupyterbook_to_zendesk import cli
from jupyterbook_to_zendesk import jupyterbook_to_zendesk
from jupyterbook_to_zendesk.commands import build_jupyterbook


def test_command_line_interface():
    """Test the CLI."""
    runner = CliRunner()
    runner.invoke(cli.command_build)
