#!/usr/bin/env python
"""The setup script."""
from setuptools import find_packages
from setuptools import setup

with open("README.md") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

with open("requirements.txt") as requirements_file:
    requirements = requirements_file.read().splitlines()

# requirements = ['Click>=7.0', ]

test_requirements = ["pytest>=3"]

setup(
    author="Jillian Rowe",
    author_email="jillian@dabbleofdevops.com",
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    description="Taking some jupyterbooks and slinging them onto zendesk.",
    entry_points={
        "console_scripts": ["jupyterbook-to-zendesk=jupyterbook_to_zendesk.cli:main"]
    },
    install_requires=requirements,
    license="Apache Software License 2.0",
    long_description=readme + "\n\n" + history,
    include_package_data=True,
    keywords="jupyterbook_to_zendesk",
    name="jupyterbook_to_zendesk",
    packages=find_packages(
        include=["jupyterbook_to_zendesk", "jupyterbook_to_zendesk.*"]
    ),
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/jerowe/jupyterbook_to_zendesk",
    version="0.1.0",
    zip_safe=False,
)
