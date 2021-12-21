import json
import logging
import os
import random
import string
import sys
from datetime import datetime
from pprint import pprint

import boto3
import click
from cookiecutter.main import cookiecutter

from jupyterbook_to_zendesk.commands import md2zen as md
from jupyterbook_to_zendesk.logging import logger


def build(ctx):
    """Build the jupyterbook"""

    App = md.Config(ctx.obj["config_file"])

    hc = md.HelpCenter(App.get("url"), App.get("username"), App.get("token"))
    s3 = boto3.client(
        "s3",
        aws_access_key_id=App.get("aws_access_key"),
        aws_secret_access_key=App.get("aws_secret"),
    )

    zendesk_category_name = App.get("zendesk_category_name")
    zendesk_category_id = md.check_category_on_zendesk(hc, zendesk_category_name)

    # find html files to send over
    html_files_list = md.gen_list_of_sections_and_html_files(ctx.obj["source_dir"])

    # generate jupyter book
    md.gen_jupyter_book(ctx.obj["source_dir"])
    html_files_for_zendesk = md.handle_sections_on_zendesk(
        hc, html_files_list, zendesk_category_id
    )
    # logging.info(f"html files to upload to Zendesk: \n {html_files_for_zendesk}")
    return 0
