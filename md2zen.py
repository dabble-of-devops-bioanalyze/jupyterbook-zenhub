from zendeskhc.HelpCenter import *
from bs4 import BeautifulSoup as bs4
import os
import subprocess
import configparser
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

LOGGING_FORMAT = '%(name)s - %(levelname)s - %(message)s'
ERROR_CODE = 1
OK_CODE = 0

ROOT_SOURCE_DIR = os.path.dirname(os.path.abspath(__file__))  # top source directory
LOG_FILE_DIR = os.path.join(ROOT_SOURCE_DIR,'logs')

article_dict =  {
    "article": {
        "body": "",
        "locale": "en-us",
        "permission_group_id": 1326317,
        "title": "Sample2 from notebook",
        "user_segment_id": 360000471977
    },
    "notify_subscribers": false
}

def main():
    # 0. Initialize Zendesk router
    # 1. Generate the html from the markdown files.
    # 2. Create a list of html files that need to be exported to zendesk
    # 3. For each file:
    #    a. extract only the relevant body portion that will be exported.
    #    b. prepare payload () {}
    #    c. Check if the file already exists on zendesk hc.
    #        - If yes then use PUT
    #        - If no then use POST
    



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
