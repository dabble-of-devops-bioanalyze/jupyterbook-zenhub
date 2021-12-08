#!/usr/bin/env python3
from zendeskhc.HelpCenter import HelpCenter
from config import Config
from bs4 import BeautifulSoup as bs4
import json
import os
import shutil
import boto3
import subprocess
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



TOC_FILE = "_toc.yml"
ZENDESK_FILE = "zendesk.json"
EXCLUDED_HTML_FILENAMES = ['index', 'genindex', 'search'] # these files will not be carried over to Zendesk

# permission_group_id & user_segment_id for zendesk are hardcoded for testprepco@gmail.com user.
# The same ids may be applicable to other users but there is no sure way to know. 
# If the program fails as-is for a different user ID, do this:
# 1. Create a dummy article on Zendesk. Note down its article_ID (provided in the URL).
# 2. Make a call using python CLI (inside virtual environment): 
#     from zendeskhc.HelpCenter import *
#     hc = HelpCenter(url, username, token)
#     response = hc.show_article(article_ID)
# 3. Read these values off the "response".
#     response['article']['permission_group_id']
#     response['article']['user_segment_id']
# 4. Edit these values in ARTICLE_DICT below.
ARTICLE_DICT =  {
    "article": {
        "body": "",
        "locale": "en-us",
        "permission_group_id": 1326317, # should not change after Zendesk Account is setup initially.
        "title": "",
        "html_url": "",
        "user_segment_id": 360000471977, # may change per user ID in config.cfg
        "label_names": "",
        "draft": True,
    },
    "notify_subscribers": False
}


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


def gen_jupyter_book(source_folder_path, cwd=None):
    cmd_string = f"jupyter-book build {source_folder_path}"
    result = subprocess.run(cmd_string, shell=True, cwd=cwd)
    st_code = result.returncode
    logger.info(f'jupyter-book build STATUS CODE = {st_code}')
    if st_code != OK_CODE:
        print('Error in creating Jupyter Book.')
        exit(1)

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
    article_dict['article']['body'] = msoup.prettify(formatter='html5')
    with open(html_file_path,'w') as oFile: # write the file back to disk
        # formatter html to retain &nbsp; etc.
        oFile.write(soup.prettify(formatter='html5'))
        oFile.close() 
    return article_dict

def find_matching_url(url, html_files_for_zendesk):
    html_url, rhs_url, lhs_url = url, "", ""
    if '#' in url:
        hash_loc = url.find('#')
        lhs_url = url[:hash_loc]
        rhs_url = url[hash_loc:]
        dot_loc = lhs_url.find('.')
        html_url = lhs_url[:dot_loc] + '.html'
        
    for item in html_files_for_zendesk:
        if item['html_file_path'].endswith(html_url):
            zendesk_url = item['article_html_url']
            matching_url = zendesk_url + rhs_url
            return matching_url
    logger.warning(f'For {html_url}, Matching URL not found on Zendesk')
    return ('#')

def update_urls_in_article_dict(html_file_path, html_files_for_zendesk, article_dict=ARTICLE_DICT):
    with open(html_file_path,'r') as f:
        soup = bs4(f.read(),'html.parser')
    article_dict['article']['title'] = soup.title.text
    # extract out main content of the html page
    msoup = soup.find(id="main-content")
    a_tags = msoup.find_all('a')
    for tag in a_tags:
        a_url = tag['href']
        if a_url.startswith('https://') or a_url.startswith('http://') or a_url.startswith('mailto:') or a_url.startswith('#'):
            continue
        else:
            new_url = find_matching_url(a_url, html_files_for_zendesk)
            tag['href'] = new_url
    article_dict['article']['body'] = msoup.prettify(formatter='html5')
    with open(html_file_path,'w') as oFile: # write the file back to disk
        # formatter html to retain &nbsp; etc.
        oFile.write(soup.prettify(formatter='html5'))
        oFile.close() 
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


def read_zendesk_json(zendesk_file_path):
    try:
        with open(zendesk_file_path,'r') as f:
            zendesk_json_pre = json.loads(f.read())
    except: # probably a new book so no file OR an empty file OR not a valid json file 
        zendesk_json_pre = {"timestamp": "","articles": []}
    return zendesk_json_pre

def file_exists_on_zendesk(file_dict, zendesk_json_pre):
    # first find if file exists in zendesk_json_pre
    html_file_path = file_dict['html_file_path']
    for item in zendesk_json_pre['articles']:
        if item['html_file_path'] == html_file_path: # file exists in pre
            # now we check if it exists on zendesk (TBD)
            return item
    return NOT_FOUND

def check_category_on_zendesk(hc, zendesk_category_name):
    # check if category exists on zendesk. If not create it.
    logger.info(f"Category Name: {zendesk_category_name}")
    zendesk_categories = hc.list_all_categories()
    for cat in zendesk_categories["categories"]:
        if zendesk_category_name == cat["name"]:
            logger.info(f"Category_ID: {cat['id']}")
            return cat['id']
        
          
        
        data_dict = {
        "category": {
            "position": 0, 
            "locale": "en-us", 
            "name": zendesk_category_name,
        }
        
    }
    try: 
        resp = hc.create_category(json.dumps(data_dict))
        logger.info(f'Created new Category on Zendesk:\n {resp}')
        return resp['id']
    except:
        logger.error(f'Error in creating Category: {zendesk_category_name} on Zendesk')
        return NOT_FOUND

def check_user_on_zendesk(hc):
    user_info = hc.get_me()
    user_id = user_info['user']['id']
    if user_id is None:
        logger.error(f'The user ID setup in config.cfg does not exist. Please check and try again')
        exit(1)
    user_role = user_info['user']['role']
    if user_role != "admin":
        logger.error(f'User role:{user_role}, is not an Admin Role. Please apply appropriate permissions and try again')
        exit(1)

def archive_book_from_zendesk(hc, zendesk_json_pre, zendesk_file_path):
    articles = zendesk_json_pre['articles'] 
    if len(articles) < 1:
        logger.info('No articles found in the zendesk.json file to Archive')
        return
    for article in articles:
        article_id = article['article_id']
        html_file_path = article['html_file_path']
        logger.info(f"Archiving: {html_file_path} at Zendesk, Article ID:{article_id}")
        resp = hc.archive_article(article_id, locale='en-us')
        status_code = resp['status_code']
        if  status_code == 204:
            logger.info(f'{article_id} Successfully Archived')
        else:
            logger.warning(f"Error occured in Archiving: {article_id}. HTTP Code = {status_code}")
    open(zendesk_file_path,'w').close() # will rewrite zendesk.json to zero bytes
    logger.info(f'Book archived at Zendesk. You can delete it manually from the Admin UI')

def delete_local_html_of_book(source_folder_path):
    build_folder_path = os.path.join(source_folder_path, "_build")
    logger.info(f'Build Folder: {build_folder_path}')
    if os.path.exists(build_folder_path):
        logger.info(f'Removing old version of build folder: {build_folder_path}')
        shutil.rmtree(build_folder_path)   


def main(source_folder_path, archive_book_flag):
    # read TOC YAML file
    st_code, toc = read_toc_yaml(os.path.join(source_folder_path, TOC_FILE))
    if st_code is not OK_CODE:
        exit(1)

    # 0. Initialize Zendesk router & S3

    
    App = Config()

    # Set configuration variables as environment variables.
    os.environ['USERNAME'] = App.get("username")
    os.environ['API_TOKEN'] = App.get("token")
    os.environ['URL'] = App.get("url")
    os.environ['AWS_BUCKET'] = App.get("aws_s3_bucket")
    os.environ['AWS_ACCESS_KEY'] = App.get("aws_access_key")
    os.environ['AWS_SECRET_KEY'] = App.get("aws_secret")
 
    
   

    hc = HelpCenter(App.get("url"), App.get("username"), App.get("token"))
    s3 = boto3.client("s3", aws_access_key_id=App.get('aws_access_key'),aws_secret_access_key= App.get("aws_secret"))

    
    # check if user exists on Zendesk and can do something on it.
    check_user_on_zendesk(hc)

    # load any previous zendesk activity on this source folder
    zendesk_file_path = os.path.join(source_folder_path, ZENDESK_FILE)
    zendesk_json_pre = read_zendesk_json(zendesk_file_path)

    if archive_book_flag: # archive the book on Zendesk and exit OK.
        archive_book_from_zendesk(hc, zendesk_json_pre, zendesk_file_path)
        delete_local_html_of_book(source_folder_path)
        exit(0)

    

    aws_s3_bucket = App.get("aws_s3_bucket")
    zendesk_category_name = App.get('zendesk_category_name')
    zendesk_category_id = check_category_on_zendesk(hc, zendesk_category_name) # will exit program if not found

    # find html files to send over
    html_files_list = gen_list_of_sections_and_html_files(source_folder_path, toc)

    # generate jupyter book
    gen_jupyter_book(source_folder_path)
    html_files_for_zendesk = handle_sections_on_zendesk(hc, html_files_list, zendesk_category_id)
    logger.info(f'html files to upload to Zendesk: \n {html_files_for_zendesk}')

    # now we iterate over list of files
    for f in html_files_for_zendesk:
        logger.info(f'Processing: {f}')
        article_dict = update_article_dict(f['html_file_path'], s3, aws_s3_bucket)
        section_id = f['section_id']
        # check if file already exists in zendesk_json_pre & if yes, then check if file exists still on zendesk
        article_info = file_exists_on_zendesk(f, zendesk_json_pre)
        if article_info == NOT_FOUND:
            response_json = hc.create_article(section_id, json.dumps(article_dict))
            article_id = response_json['article']['id']
            f.update({'article_id': article_id})
            article_html_url = response_json['article']['html_url']
            f.update({'article_html_url': article_html_url})
            logger.info(f"Article ID: {article_id}, Article URL: {article_html_url}")
        else: # update_article
            article_id = article_info['article_id']
            article_html_url = article_info['article_html_url']
            translation_dict = {
                "translation": {
                    "title": article_dict['article']['title'],
                    "body": article_dict['article']['body']
                }
            }
            response_json = hc.update_article_translation(article_id, json.dumps(translation_dict), locale='en-us')
            f.update({'article_id': article_id})
            f.update({'article_html_url': article_html_url})
    
    # 2nd pass to fix URLs
    for f in html_files_for_zendesk:
        logger.info(f'Processing (2nd Pass): {f}')
        article_dict = update_urls_in_article_dict(f['html_file_path'], html_files_for_zendesk)
        translation_dict = {
            "translation": {
                "title": article_dict['article']['title'],
                "body": article_dict['article']['body']
            }
        }
        response_json = hc.update_article_translation(f['article_id'], json.dumps(translation_dict), locale='en-us')


    # write html_files_for_zendesk to json
    current_utc_datetime = datetime.utcnow()
    dt_stamp = current_utc_datetime.strftime("%m-%d-%Y:%H:%M:%SZ")
    zendesk_json_post = {'timestamp': dt_stamp, 'articles': html_files_for_zendesk}
    with open(zendesk_file_path,'w') as f:
        f.write(json.dumps(zendesk_json_post))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        description="This utility creates jupyterbook html from .md files and uploads them to zendesk OR archives them on zendesk",
        epilog=''' 
    Examples of the command are: 
        To Build (or Update) a book on Zendesk:
            ./md2zen.py <path/to/bookdirectory/>
        To Archive a book's pages on Zendesk:
            ./md2zen.py <path/to/bookdirectory/> -a
    ''', formatter_class=argparse.RawTextHelpFormatter) 
    parser.add_argument("bookdir",
    help='''
    A directory path where the source markdown files for the book reside.
    A sample book is found at ./example/mynewbook/ ''')
    parser.add_argument("-a", "--archive", default=False, action='store_true',
                        help='if True, it will archive any html pages on Zendesk(found in zendesk.json file).')
    args = parser.parse_args()
    book_dir_path = os.path.abspath(args.bookdir)
    archive_book_flag = args.archive
    # set up logging
    book_dir_name = os.path.basename(book_dir_path)
    current_utc_datetime = datetime.utcnow()
    dt_stamp = current_utc_datetime.strftime("%m-%d-%Y:%H:%M:%SZ")
    log_file_name = f'{book_dir_name}_{dt_stamp}.log'
    log_file_path = os.path.join(LOG_FILE_DIR,log_file_name)
    os.makedirs(LOG_FILE_DIR, exist_ok=True)
    logging.basicConfig(
        filename=log_file_path,
        level=logging.INFO,
        filemode='w',
        format=LOGGING_FORMAT
    )
    logger.info(f"Script initiated with Arguments: {args}")
    main(book_dir_path, archive_book_flag)
