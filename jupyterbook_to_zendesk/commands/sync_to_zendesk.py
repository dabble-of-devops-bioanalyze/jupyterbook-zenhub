import sys
import click
import random
import string
import os
import json
import logging
from pprint import pprint
from datetime import datetime

logging.basicConfig(level=logging.INFO)

def sync(ctx):
    """Sync the jupyterbook to zendesk"""
    logging.info("Syncing the jupyterbook to zendesk...")
    logging.info(ctx)
    # add the rest of the sync commands here
    return 0