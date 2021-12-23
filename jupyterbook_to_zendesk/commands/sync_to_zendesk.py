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
from prettyprinter import cpprint

import jupyterbook_to_zendesk.commands.md2zen as md
from jupyterbook_to_zendesk.logging import logger


def sync(ctx):
    """Sync the jupyterbook to zendesk"""

    # 0. Initialize Zendesk router & S3

    App = md.Config(ctx.obj["config_file"])

    hc = md.HelpCenter(App.get("url"), App.get("username"), App.get("token"))
    try:
        hc.get_me()
    except Exception as e:
        logger.warn("Error authenticating as the ZenDesk User")
        logger.exception(e)
        exit(1)

    logger.info("Init s3 configuration")
    try:
        s3 = boto3.client(
            "s3",
            aws_access_key_id=App.get("aws_access_key"),
            aws_secret_access_key=App.get("aws_secret"),
        )
    except Exception as e:
        logger.warn("Error calling boto3.client")
        logger.exception(e)
        exit(1)

    # TODO add check that s3 bucket exists
    aws_s3_bucket = App.get("aws_s3_bucket")

    # check if user exists on Zendesk and can do something on it.
    md.check_user_on_zendesk(hc)

    # load any previous zendesk activity on this source folder
    zendesk_file_path = os.path.join(ctx.obj["destination_dir"], md.ZENDESK_FILE)

    category_id = md.check_category_on_zendesk(
        hc=hc, zendesk_category_name=App.get("zendesk_category_name")
    )
    zendesk_json_pre = hc.list_articles_by_category(category_id=category_id)

    if ctx.obj["archive_flag"]:  # archive the book on Zendesk and exit OK.
        md.archive_book_from_zendesk(hc, zendesk_json_pre, zendesk_file_path)
        md.delete_local_html_of_book(ctx.obj["destination_dir"])
        exit(0)

    aws_s3_bucket = App.get("aws_s3_bucket")

    try:
        html_files_for_zendesk = md.gen_list_of_sections_and_html_files(
            source_folder_path=ctx.obj["source_dir"]
        )
    except Exception as e:
        logger.warn("Error creating html files for zendesk")
        logger.exception(e)
        exit(1)

    html_files_for_zendesk = md.handle_sections_on_zendesk(
        hc=hc, html_files_list=html_files_for_zendesk, zendesk_category_id=category_id
    )

    zendesk_json_pre = hc.list_articles_by_category(category_id=category_id)

    # now we iterate over list of files
    for f in html_files_for_zendesk:
        logger.info(f"Processing: {f}")
        article_dict = md.update_article_dict(f["html_file_path"], s3, aws_s3_bucket)

        section_id = f["section_id"]
        # article exists on zendesk
        # if article with same title and section_id is found
        # then article exists
        logger.info("Checking to see if article exists")
        article_info = md.article_exists(
            articles=zendesk_json_pre,
            title=article_dict["article"]["title"],
            section_id=section_id,
        )
        logger.info(f"Article Exists: {cpprint(article_info)}")

        if ctx.obj["public"]:
            article_dict["article"]["user_segment_id"] = None

        if not article_info:
            logger.info("Creating the article")
            response_json = hc.create_article(section_id, json.dumps(article_dict))
            article_id = response_json["article"]["id"]
            f.update({"article_id": article_id})
            article_html_url = response_json["article"]["html_url"]
            f.update({"article_html_url": article_html_url})
            md.logger.info(f"Article ID: {article_id}, Article URL: {article_html_url}")
        else:  # update_article
            logger.info("Updating the article")
            article_id = article_info["id"]
            article_html_url = article_info["html_url"]
            translation_dict = {
                "article": {
                    "user_segment_id": article_dict["article"]["user_segment_id"]
                },
                "translation": {
                    "title": article_dict["article"]["title"],
                    "body": article_dict["article"]["body"],
                },
            }
            response_json = hc.update_article_metadata(
                article_id=article_id,
                data=json.dumps(article_dict["article"]),
                locale="en-us",
            )
            f.update({"article_id": article_id})
            f.update({"article_html_url": article_html_url})

    # 2nd pass to fix URLs
    for f in html_files_for_zendesk:
        logging.info(f"Processing (2nd Pass): {f}")
        article_dict = md.update_urls_in_article_dict(
            f["html_file_path"],
            html_files_for_zendesk,
        )

        draft = ctx.obj["draft"]
        article_dict["article"]["draft"] = draft

        if ctx.obj["public"]:
            article_dict["article"]["user_segment_id"] = None

        translation_dict = {
            "translation": {
                "title": article_dict["article"]["title"],
                "body": article_dict["article"]["body"],
                "draft": article_dict["article"]["draft"],
            }
        }
        logging.info("Syncing the jupyterbook to zendesk...")
        response_json = hc.update_article_metadata(
            article_id=article_id,
            data=json.dumps(article_dict["article"]),
            locale="en-us",
        )
        logging.info("Updating article visibility")
        logging.debug(cpprint(response_json))

        response_json = hc.update_article_translation(
            f["article_id"], json.dumps(translation_dict), locale="en-us"
        )
        # get useful output
        del response_json["translation"]["body"]
        logging.debug(cpprint(response_json))

    # add the rest of the sync commands here
    return 0
