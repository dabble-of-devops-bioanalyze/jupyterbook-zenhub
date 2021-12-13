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
import md2zen as md

logging.basicConfig(level=logging.INFO)



def build(ctx):
    """Build the jupyterbook"""

    # read TOC YAML file
    st_code, toc = md.read_toc_yaml(os.path.join(ctx.obj["destination_dir"], md.TOC_FILE))
    if st_code is not md.OK_CODE:
        exit(1)

  # generate jupyter book

    App = md.Config()

    # Set configuration variables as environment variables.
    os.environ['USERNAME'] = App.get("username")
    os.environ['API_TOKEN'] = App.get("token")
    os.environ['URL'] = App.get("url")
    os.environ['AWS_BUCKET'] = App.get("aws_s3_bucket")
    os.environ['AWS_ACCESS_KEY'] = App.get("aws_access_key")
    os.environ['AWS_SECRET_KEY'] = App.get("aws_secret")
 
    
   

    hc = md.HelpCenter(App.get("url"), App.get("username"), App.get("token"))
    s3 = md.client("s3", aws_access_key_id=App.get('aws_access_key'),aws_secret_access_key= App.get("aws_secret"))

    
    zendesk_category_name = App.get('zendesk_category_name')
    zendesk_category_id = md.check_category_on_zendesk(hc, zendesk_category_name) 
    
    # find html files to send over
    html_files_list = md.gen_list_of_sections_and_html_files(ctx.obj["destination_dir"], toc)

    md.gen_jupyter_book(ctx.obj["destination_dir"])
    html_files_for_zendesk = md.handle_sections_on_zendesk(hc, html_files_list, zendesk_category_id)
    logger.info(f'html files to upload to Zendesk: \n {html_files_for_zendesk}')

    logging.info("building!")
    return 0
