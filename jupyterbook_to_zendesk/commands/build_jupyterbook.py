import sys
import click
import random
import string
import os
import json
import logging
from pprint import pprint
from cookiecutter.main import cookiecutter
from datetime import datetime

logging.basicConfig(level=logging.INFO)

def hello():
    logging.info('hello')

def build(ctx):
    """Build the jupyterbook"""
    logging.info("building!")
    return 0
