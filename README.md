# Jupyterbook to Zendesk

```{image} https://img.shields.io/pypi/v/jupyterbook_to_zendesk.svg
:target: https://pypi.python.org/pypi/jupyterbook_to_zendesk
```

```{image} https://img.shields.io/travis/jerowe/jupyterbook_to_zendesk.svg
:target: https://travis-ci.com/jerowe/jupyterbook_to_zendesk
```

```{image} https://readthedocs.org/projects/jupyterbook-to-zendesk/badge/?version=latest
:alt: Documentation Status
:target: https://jupyterbook-to-zendesk.readthedocs.io/en/latest/?version=latest
```

```{image} https://pyup.io/repos/github/jerowe/jupyterbook_to_zendesk/shield.svg
:alt: Updates
:target: https://pyup.io/repos/github/jerowe/jupyterbook_to_zendesk/
```

Taking some jupyterbooks and slinging them onto zendesk.

- Free software: Apache Software License 2.0
- Documentation: <https://jupyterbook-to-zendesk.readthedocs.io>.

## Installation & Quickstart

1. Pre-Requisites

    a. MacOS/Linux is recommended

    b. Python3.8 should be pre-installed

1. Clone the repo on your local machine to a specified `folder_name`.

    `git clone <address to this repo> <folder_name>`

1. Create a virtual environment to keep things isolated

    `python3 -m venv <folder_name>`
1. Go to the directory where the code is cloned into.

    `cd <folder_name>`

1. Install python modules via pip

    `dir> pip install -r requirements.txt`

1. Run the script

    `./md2zen.py -h`


## Logging

The utility will create a log file in the location `./logs/`. The log file will be named as a combo of the book directory and current datetime stamp. An example of the log file name is: `mynewbook_02-04-2021:09:11:44Z.log`.

## Environment Variables

Global variables are created using a file named `config.cfg` in the root source directory. Since it contains security keys, it is not part of the git repo. Its entries are as follows:

```sh
[DEFAULT]
username = xxxx@yyyyyyyyy.zzz/token
token = xxxxxxxxxxxxxxxxxxxxxxxxxxx
url = https://dabbleofdevopshelp.zendesk.com
zendesk_category_name = General
aws_s3_bucket = zendesk.dabbleofdevops.com
aws_access_key = AKIAxxxxxxxxxxxxxxxxxxxxx
aws_secret = XXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

## Creating the book
/
Run the script: `./md2zen.py /example/mynewbook/`.

This does the following:

1. Read `_toc.yml` in the source folder (`/example/mynewbook/` here).

    `_toc.yml` is like this:

    ```yml
    - file: intro
    - part: Announcements # will be made into a Zendesk section if it doesn't exist.
    chapters:
    - file: content
    - file: notebooks
    - part: Markdown Samples # will be made into a Zendesk section if it doesn't exist.
    chapters:
    - file: markdown
    - file: myfile1
    - file: myfile2
    ```


1. The `part` names in `_toc.yml` are mapped to sections on zendesk. These sections are either located (or optionally created) in the category defined in the [Environment Variables](#Environment-Variables).

1. The `chapters` lists all the `files` that will be uploaded to zendesk under the appropriate section. The first file in the list `intro` is not sent to Zendesk.

1. The Jupyter book is created in the `_build` subdirectory of the source folder.

1. `index.html`, `genindex.html` & `search.html` are files added by Zendesk for navigation purposes to the Jupyter book. They are excluded from the list of files to be uploaded to Zendesk

1. Files are uploaded to Zendesk.

1. File's attachments (images, videos) are uploaded to Amazon Web Services S3 bucket as defined in the environment variables.

1. After the first pass on all files, Each file's links are evaluated in the 2nd pass and updated on zendesk.

1. Information on uploaded files is saved in `zendesk.json` file in the source folder. It looks like this:

    ```json
    {
    "timestamp": "02-04-2021:09:12:56Z",
    "articles": [
        {
            "section_name": "Announcements",
            "section_id": 360003315137,
            "html_file_path": "/Users/Ash/pydev/zenhub/example/mynewbook/_build/html/content.html",
            "article_id": 360017635218,
            "article_html_url": "https://dabbleofdevopshelp.zendesk.com/hc/en-us/articles/360017635218-Content-in-Jupyter-Book-My-sample-book"
        },...
    ]
    }
    ```

## Archiving the book

Run the script: `./md2zen.py /example/mynewbook/ -a`

This does the following:

1. Reads `zendesk.json` from the source folder.

1. Archives each article found in the list of articles.

1. Deletes all entries from `zendesk.json`. (Essentially the file is reduced to 0 bytes)

1. Deletes the `_build` sub-directory in the source folder.



- TODO

## Credits

This package was created with [Cookiecutter] and the [audreyr/cookiecutter-pypackage] project template.

[audreyr/cookiecutter-pypackage]: https://github.com/audreyr/cookiecutter-pypackage
[cookiecutter]: https://github.com/audreyr/cookiecutter
