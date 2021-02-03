#!/usr/bin/env python3
from zendeskhc.HelpCenter import HelpCenter
from bs4 import BeautifulSoup as bs4
import json
import os
import boto3
import subprocess
import configparser
import yaml
from glob import glob
import logging
from datetime import datetime


ERROR_CODE = 1
OK_CODE = 0
NOT_FOUND = -1
ROOT_SOURCE_DIR = os.path.dirname(os.path.abspath(__file__))  # top source directory
AWS_URL_PREFIX = "https://s3.amazonaws.com/"

# setup logger
LOG_FILE_DIR = os.path.join(ROOT_SOURCE_DIR,'logs')
LOGGING_FORMAT = '%(name)s - %(levelname)s - %(message)s'
logger = logging.getLogger(__name__)


CONFIG_FILE = 'config.cfg'
TOC_FILE = "_toc.yml"
ZENDESK_FILE = "zendesk.json"
EXCLUDED_HTML_FILENAMES = ['index', 'genindex', 'search'] # these files will not be carried over to Zendesk

# ids for zendesk are hardcoded for now. Need to be made configurable via some API calls.
ARTICLE_DICT =  {
    "article": {
        "body": "",
        "locale": "en-us",
        "permission_group_id": 1326317,
        "title": "",
        "html_url": "",
        "user_segment_id": 360000471977
    },
    "notify_subscribers": False
}
SECTION_ID = 360003315137


def read_config_file(configfilepath=CONFIG_FILE): # will return a dict
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    cfg = config['DEFAULT'] # KISS for now.
    config_dict = {key:cfg[key] for key in cfg.keys()}
    return config_dict

def read_toc_yaml(yaml_file):
    logger.info(f'Reading TOC yaml file: {yaml_file}')
    toc_dict = {}
    # tie yaml read in try+except to return empty if there is an error.
    try:
        with open(yaml_file, "r") as f:
            toc_dict = yaml.load(f, Loader=yaml.FullLoader)
            logger.debug(f'TOC dict: {toc_dict}')
    except Exception as e:
        logger.exception(
            f'Exception occured while reading TOC yaml file: {yaml_file}\n Exception: {e}')
        return ERROR_CODE, toc_dict
    return OK_CODE, toc_dict

''' TOC Dict looks like this:
[
  {"file": "intro"},
  { "part": "Get started",
    "chapters": [
      { "file": "content"},
      {"file": "notebooks"}
    ]},
  {"part": "Markdown Samples",
    "chapters": [
      {"file": "markdown"},
      {"file": "myfile1"},
      { "file": "sub/myfile2"}
    ]}
]
'''

def gen_jupyter_book(source_folder_path, cwd=None):
    cmd_string = f"jupyter-book build {source_folder_path}"
    result = subprocess.run(cmd_string, shell=True, cwd=cwd)
    st_code = result.returncode
    logger.info(f'jupyter-book build STATUS CODE = {st_code}')
    return st_code

def gen_list_of_sections_and_html_files(source_folder_path, toc):
    html_files_list = [] # list of dicts
    html_folder_path = os.path.join(source_folder_path, "_build", "html")
    for item in toc:
        if 'part' in item.keys(): # will exclude intro file from the transfer to zendesk
            section = item['part']
            files = item['chapters']
            for f in files:
                filename = f['file']
                html_file_path = os.path.join(html_folder_path, filename + ".html")
                html_files_list.append({'section_name': section, 'html_file_path': html_file_path})
    logger.info(f'Final List of html files to be sent to Zendesk: \n {html_files_list}')
    return html_files_list

def upload_to_aws_s3(s3, local_file_path, bucket, s3_file_key):
    try:
        s3.upload_file(
            local_file_path, 
            bucket, 
            s3_file_key, 
            ExtraArgs={'ACL': 'public-read'}
        )
        logger.info(f"{local_file_path}: Upload Successful")
        return True
    except Exception as e:
        logger.error(f'{local_file_path}: Some Error occured uploading. \n', e, '\n')
        return False

def update_article_dict(html_file_path, s3, aws_s3_bucket, article_dict=ARTICLE_DICT):
    with open(html_file_path,'r') as f:
        soup = bs4(f.read(),'html.parser')
    article_dict['article']['title'] = soup.title.text
    # extract out main content of the html page
    msoup = soup.find(id="main-content")
    # find all image references in main content
    img_tags = msoup.find_all('img')
    for tag in img_tags:
        img_url = tag['src']
        if img_url.startswith('https://') or img_url.startswith('http://'):
            continue
        img_file_path = os.path.join(os.path.dirname(html_file_path), img_url)
        img_s3_file_key = os.path.basename(img_url)
        status = upload_to_aws_s3(s3, img_file_path, aws_s3_bucket, img_s3_file_key)
        # fix url to point to aws s3 instead of local path
        tag['src'] = AWS_URL_PREFIX + aws_s3_bucket + '/' + img_s3_file_key
    article_dict['article']['body'] = msoup.prettify()
    return article_dict

def find_section_name_in_list(section_name, sections_resp, category_id):
    for item in sections_resp['sections']:
        if item['name'] == section_name and item['category_id'] == category_id:
            return item['id']
    return NOT_FOUND

def setup_section_on_zendesk(hc, section_name, zendesk_category_id):
    data_dict = {
        "section": {
            "position": 0, 
            "locale": "en-us", 
            "name": section_name,
        }
    }
    try: 
        resp = hc.create_section(zendesk_category_id, json.dumps(data_dict), locale='en-us')
        logger.info(f'Created new section on Zendesk:\n {resp}')
        return resp
    except:
        logger.error(f'Error in creating section_name: {section_name} on Zendesk')
        return NOT_FOUND

def handle_sections_on_zendesk(hc, html_files_list, zendesk_category_id):
# will check if all sections exist on Zendesk in the category
# if not, will create the section on Zendesk
# will update
    sections_resp = hc.list_all_sections()
    logger.info(sections_resp)
    html_files_for_zendesk = []
    for item in html_files_list:
        section_name = item['section_name']
        section_id = find_section_name_in_list(section_name, sections_resp,zendesk_category_id)
        if section_id == NOT_FOUND:
            # set up section on zendesk
            section_resp = setup_section_on_zendesk(hc, section_name, zendesk_category_id)
            if section_resp == NOT_FOUND:
                logger.error(f'Could not create section name: {section_name} on Zendesk. Please check, cleanup and retry')
                exit(1)
            else:
                sections_resp['sections'].append(section_resp['section'])
                section_id = section_resp['section']['id']
        html_files_for_zendesk.append({'section_name': item['section_name'], 'section_id': section_id, 'html_file_path': item['html_file_path']})
    return html_files_for_zendesk

def find_category_id_in_list(cat_name, category_resp):
    for cat in category_resp["categories"]:
        if cat_name == cat["name"]:
            return cat['id']
    return NOT_FOUND

def delete_book_from_zendesk():
    pass


def main(source_folder_path, section_name=None):
    # 0. Initialize Zendesk router
    # 1. Generate the html from the markdown files.
    # 2. Create a list of html files that need to be exported to zendesk
    # 3. For each file:
    #    a. extract only the relevant body portion that will be exported.
    #    b. prepare payload () {}
    #    c. Check if the file already exists on zendesk hc.
    #        - If yes then use PUT
    #        - If no then use POST
    # read TOC YAML file
    st_code, toc = read_toc_yaml(os.path.join(source_folder_path, TOC_FILE))
    if st_code is not OK_CODE:
        exit(1)
     # 0. Initialize Zendesk router & S3
    zdc = read_config_file()
    hc = HelpCenter(zdc['url'], zdc['username'], zdc['token'])
    s3 = boto3.client("s3", aws_access_key_id=zdc['aws_access_key'], aws_secret_access_key=zdc['aws_secret'])
    aws_s3_bucket = zdc['aws_s3_bucket']
    zendesk_category_name = zdc['zendesk_category_name']
    logger.info(f"Category Name: {zendesk_category_name}")
    # check if category exists on zendesk. If not error out.
    zendesk_categories = hc.list_all_categories()
    zendesk_category_id = find_category_id_in_list(zendesk_category_name, zendesk_categories)
    if zendesk_category_id == NOT_FOUND:
        logger.error("This Category does not exist on Zendesk. Please set it up via UI and retry")
        exit(1)
    else:
        logger.info(f'Category_ID: {zendesk_category_id}')
    # find html files to send over
    html_files_list = gen_list_of_sections_and_html_files(source_folder_path, toc)
    print(html_files_list)
    # generate jupyter book
    st_code = gen_jupyter_book(source_folder_path)
    if st_code != OK_CODE:
        print('Error in creating Jupyter Book.')
        exit(1)
    html_files_for_zendesk = handle_sections_on_zendesk(hc, html_files_list, zendesk_category_id)
    logger.info(f'html files to upload to Zendesk: \n {html_files_for_zendesk}')
    # find out if these files exist already on Zendesk (To Be Done)
    for f in html_files_for_zendesk:
        logger.info(f'Processing: {f}')
        article_dict = update_article_dict(f['html_file_path'], s3, aws_s3_bucket)
        section_id = f['section_id']
        response_json = hc.create_article(section_id, json.dumps(article_dict))
        article_id = response_json['article']['id']
        f.update({'article_id': article_id})
        article_html_url = response_json['article']['html_url']
        f.update({'article_html_url': article_html_url})
        logger.info(f"Article ID: {article_id}, Article URL: {article_html_url}")
    # write html_files_for_zendesk to json
    zendesk_file_path = os.path.join(source_folder_path, ZENDESK_FILE)
    current_utc_datetime = datetime.utcnow()
    dt_stamp = current_utc_datetime.strftime("%m-%d-%Y:%H:%M:%SZ")
    zendesk_json = {'timestamp': dt_stamp, 'articles': html_files_for_zendesk}
    with open(zendesk_file_path,'w') as f:
        f.write(json.dumps(zendesk_json))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        description="This utility creates jupyterbook html from .md files and uploads them to zendesk",
        epilog=''' 
            Examples of the command are: 
            ./md2zen.py <path/to/bookdirectory> [--sectionname "section name"]
            ''', formatter_class=argparse.RawTextHelpFormatter) 
    parser.add_argument("bookdir",
                        help='''
        A directory path where the source markdown files for the book reside
        A sample book is found at ./example/mynewbook/
        ''')
    parser.add_argument("-sn", "--sectionname", help='Name of the Section to put the files in')
    args = parser.parse_args()
    book_dir_path = os.path.abspath(args.bookdir)
    # set up logging
    book_dir_name = os.path.basename(book_dir_path)
    current_utc_datetime = datetime.utcnow()
    dt_stamp = current_utc_datetime.strftime("%m-%d-%Y:%H:%M:%SZ")
    log_file_name = f'{book_dir_name}_{dt_stamp}.log'
    log_file_path = os.path.join(LOG_FILE_DIR,log_file_name)
    os.makedirs(LOG_FILE_DIR, exist_ok=True)
    logging.basicConfig(
        filename=log_file_path,
        level=logging.DEBUG,
        filemode='w',
        format=LOGGING_FORMAT
    )
    main(book_dir_path)
