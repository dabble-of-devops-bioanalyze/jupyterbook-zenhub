import sys
import click
import random
import string
import os
import json
import logging
from pprint import pprint
from datetime import datetime
import jupyterbook_to_zendesk.commands.md2zen as md

logging.basicConfig(level=logging.INFO)


def sync(ctx):
    """Sync the jupyterbook to zendesk"""

    # 0. Initialize Zendesk router & S3

    App = md.Config()

    # Set configuration variables as environment variables.
    os.environ["USERNAME"] = App.get("username")
    os.environ["API_TOKEN"] = App.get("token")
    os.environ["URL"] = App.get("url")
    os.environ["AWS_BUCKET"] = App.get("aws_s3_bucket")
    os.environ["AWS_ACCESS_KEY"] = App.get("aws_access_key")
    os.environ["AWS_SECRET_KEY"] = App.get("aws_secret")

    hc = md.HelpCenter(App.get("url"), App.get("username"), App.get("token"))
    s3 = md.client(
        "s3",
        aws_access_key_id=App.get("aws_access_key"),
        aws_secret_access_key=App.get("aws_secret"),
    )
    aws_s3_bucket = App.get("aws_s3_bucket")

    # check if user exists on Zendesk and can do something on it.
    md.check_user_on_zendesk(hc)

    # load any previous zendesk activity on this source folder
    zendesk_file_path = os.path.join(ctx.obj["destination_dir"], md.ZENDESK_FILE)
    zendesk_json_pre = md.read_zendesk_json(zendesk_file_path)

    if ctx.obj["archive_flag"]:  # archive the book on Zendesk and exit OK.
        md.archive_book_from_zendesk(hc, zendesk_json_pre, zendesk_file_path)
        md.delete_local_html_of_book(ctx.obj["destination_dir"])
        exit(0)

    aws_s3_bucket = App.get("aws_s3_bucket")

    # now we iterate over list of files
    for f in md.html_files_for_zendesk:
        md.logger.info(f"Processing: {f}")
        article_dict = md.update_article_dict(f["html_file_path"], s3, aws_s3_bucket)
        section_id = f["section_id"]
        # check if file already exists in zendesk_json_pre & if yes, then check if file exists still on zendesk
        article_info = md.file_exists_on_zendesk(f, zendesk_json_pre)
        if article_info == md.NOT_FOUND:
            response_json = hc.create_article(section_id, json.dumps(article_dict))
            article_id = response_json["article"]["id"]
            f.update({"article_id": article_id})
            article_html_url = response_json["article"]["html_url"]
            f.update({"article_html_url": article_html_url})
            md.logger.info(f"Article ID: {article_id}, Article URL: {article_html_url}")
        else:  # update_article
            article_id = article_info["article_id"]
            article_html_url = article_info["article_html_url"]
            translation_dict = {
                "translation": {
                    "title": article_dict["article"]["title"],
                    "body": article_dict["article"]["body"],
                }
            }
            response_json = hc.update_article_translation(
                article_id, json.dumps(translation_dict), locale="en-us"
            )
            f.update({"article_id": article_id})
            f.update({"article_html_url": article_html_url})

    # 2nd pass to fix URLs
    for f in md.html_files_for_zendesk:
        logger.info(f"Processing (2nd Pass): {f}")
        article_dict = md.update_urls_in_article_dict(
            f["html_file_path"], md.html_files_for_zendesk
        )
        translation_dict = {
            "translation": {
                "title": article_dict["article"]["title"],
                "body": article_dict["article"]["body"],
            }
        }
        response_json = hc.update_article_translation(
            f["article_id"], json.dumps(translation_dict), locale="en-us"
        )

    logging.info("Syncing the jupyterbook to zendesk...")
    logging.info(ctx)
    # add the rest of the sync commands here
    return 0
