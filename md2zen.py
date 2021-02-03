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
ROOT_SOURCE_DIR = os.path.dirname(os.path.abspath(__file__))  # top source directory
AWS_URL_PREFIX = "https://s3.amazonaws.com/"

# setup logger
LOG_FILE_DIR = os.path.join(ROOT_SOURCE_DIR,'logs')
LOGGING_FORMAT = '%(name)s - %(levelname)s - %(message)s'
logger = logging.getLogger(__name__)


CONFIG_FILE = 'config.cfg'
TOC_FILE = "_toc.yml"
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
    html_files = [] # list of dicts
    sections = [] # list of section names
    # first we find all the html files in the path
    html_folder_path = os.path.join(source_folder_path, "_build", "html")
    html_folder_glob_path = os.path.join(html_folder_path,"*.html")
    html_file_paths_list = glob(html_folder_glob_path)
    excluded_html_file_paths_list = [os.path.join(html_folder_path, x + ".html") for x in EXCLUDED_HTML_FILENAMES]
    # now we exclude the files that jupyter adds to make an independent book
    final_html_file_paths_list = list(set(html_file_paths_list) - set(excluded_html_file_paths_list))
    for item in toc:
        if 'part' in item.keys():
            section = item['part']
            sections.append(section)
            files = item['chapters']
            for f in files:
                filename = f['file']
                html_file_path = os.path.join(html_folder_path, filename + ".html")
                html_files.append(
                    {
                        'section': section,
                        'html_file_path': html_file_path
                    }
                )
    logger.info(f'Final List of html files to be sent to Zendesk: \n {html_files}')
    return sections, html_files

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
    
def find_section_id_from_zendesk(hc, section_name):
    sections_list = hc.list_all_sections()
    for item in sections_list:
        if item['name'] == section_name:
            return item['id']
    # item not found
    return None

def found_category_name_in_list(cat_name, category_resp):
    for cat in category_resp["categories"]:
        if cat_name == cat["name"]:
            return True
    return False

def delete_book_from_zendesk():
    pass

def find_or_create_section_on_zendesk():
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
    if not found_category_name_in_list(zendesk_category_name, zendesk_categories):
        logger.error("This Category does not exist on Zendesk. Please set it up via UI and retry")
        exit(1)
    # generate jupyter book
    st_code = gen_jupyter_book(source_folder_path)
    if st_code != OK_CODE:
        print('Error in creating Jupyter Book.')
        exit(1)
    # find html files to send over
    sections, html_file_paths = gen_list_of_sections_and_html_files(source_folder_path, toc)
    print(html_file_paths)
    exit(1)
    # Find section id
    section_id = None #find_section_id_from_zendesk(hc, section_name)
    if section_id is None:
        section_id = SECTION_ID
    exit(1)
    for f in html_file_paths:
        logger.info(f'Processing: {f}')
        article_dict = update_article_dict(f, s3, aws_s3_bucket)
        response_json = hc.create_article(section_id, json.dumps(article_dict))
        logger.info(f"Article ID: {response_json['article']['id']}, Article URL: {response_json['article']['html_url']}")



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
