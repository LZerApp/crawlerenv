<!-- Badge for License -->
<div align="right">

  [![](https://img.shields.io/badge/docs-Tutorial-F7D360.svg?logo=&style=flat-square)](https://github.com/LZerApp/crawlerenv/wiki)
  [![](https://img.shields.io/github/license/LZerApp/crawlerenv.svg?style=flat-square)](./LICENSE)

</div>

<!-- Logo -->
<p align="center">
  <img src="https://i.imgur.com/Ar77xLR.png" alt="Flask Crawler Tutorial" height="150px">
</p>


<!-- Title and Description -->
<div align="center">

# Flask Crawler (Toy Project)

🕸️ _A simple web application for scheduling crawlers based on the Flask framework._

</div>

## Directory Structure

```
.
├── application
│   ├── __init__.py
│   ├── models
│   │   ├── __init__.py
│   │   └── ...
│   ├── blueprints
│   │   ├── __init__.py
│   │   └── ...
│   ├── services
│   │   ├── __init__.py
│   │   └── ...
│   ├── static
│   │   └── ...
│   └── templates
│       └── ...
├── crawer_data
│   └── ...
├── tests
│   ├── __init__.py
│   └── ...
├── requirements
│   ├── develop.txt
│   └── product.txt
├── requirements.txt
├── install.sh
├── config.py
├── wsgi.py
├── ...
├── LICENSE
└── README.md
```

## Quickstart

Assume that you're going to serve this server on the VM instance (use the Ubuntu 20.04 Image) of [Oracle Cloud](https://cloud.oracle.com/).

### System Dependencies

```bash
# clone project
$ git clone https://github.com/LZerApp/crawlerenv.git
$ cd crawlerenv

# update system package
$ sudo apt update && sudo apt upgrade

# install packages
$ sudo apt install python3-pip
$ sudo apt install unzip

# install google-chrome
$ wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
$ sudo apt update && sudo apt install -y -f ./google-chrome-stable_current_amd64.deb

# download chromedriver
$ wget https://chromedriver.storage.googleapis.com/89.0.4389.23/chromedriver_linux64.zip
$ unzip chromedriver_linux64.zip
$ chmod +x chromedriver

# remove the installer file
$ rm ./google-chrome-stable_current_amd64.deb
$ rm ./chromedriver_linux64.zip
```

### Python Environment and `.env` File

```bash
# install create virtual environment
$ python3 -m pip install virtualenv
$ python3 -m virtualenv env

# create the .env file and fill with variables
$ touch .env
$ echo "SERVER_URL=\"<URL>\"" >> .env
$ echo "SERVER_TOKEN=\"<TOKEN>\"" >> .env
```

### Run Server

Before start your server, make sure:

1. The browser driver `chromedriver` is exist in the project folder (`crawlerenv`).
2. You have activate the python virtual environment (text `(env)` shown on your shell prompt).
3. You have copy and fill the `.env` file.

```bash
# activate virtual environment
$ source env/bin/activate

# install dependencies (python environment)
$ pip install -r requirements.txt

# gunicorn --bind=<HOST> --timeout <TIME> <MODULE_NAME>:<APPLICATION_OBJECT>
$ gunicorn --bind=127.0.0.1 --timeout 600 wsgi:app
```

## Run Certain Crawler

If you're going to run certain crawler with `crawler_id` individually.

```bash
# activate virtual environment
$ source env/bin/activate

# flask run-crawler <crawler_id>
$ flask run-crawler 1
```

## License

Licensed under the MIT License, Copyright © 2021-present Hsins.