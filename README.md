<!-- Badge for License -->
<div align="right">

  [![](https://img.shields.io/badge/docs-Tutorial-F7D360.svg?logo=&style=flat-square)](https://github.com/LZerApp/crawlerenv/wiki)
  [![](https://img.shields.io/github/license/LZerApp/crawlerenv.svg?style=flat-square)](./LICENSE)
  <br>
  [![](https://img.shields.io/github/last-commit/LZerApp/crawlerenv.svg?style=flat-square)](https://github.com/LZerApp/crawlerenv/commits)
  
</div>

<!-- Logo -->
<p align="center">
  <img src="https://i.imgur.com/Ar77xLR.png" alt="Flask Crawler" height="150px">
</p>


<!-- Title and Description -->
<div align="center">

# Flask Crawler (Toy Project)

πΈοΈ _A simple web application for scheduling crawlers based on the Flask framework._

</div>

## Directory Structure

```
.
βββ application
βΒ Β  βββ __init__.py
βΒ Β  βββ models
βΒ Β  βΒ Β  βββ __init__.py
βΒ Β  βΒ Β  βββ ...
βΒ Β  βββ blueprints
βΒ Β  βΒ Β  βββ __init__.py
βΒ Β  βΒ Β  βββ ...
βΒ Β  βββ services
βΒ Β  βΒ Β  βββ __init__.py
βΒ Β  βΒ Β  βββ ...
βΒ Β  βββ static
βΒ Β  βΒ Β  βββ ...
βΒ Β  βββ templates
βΒ Β   Β Β  βββ ...
βββ crawer_data
βΒ Β  βββ ...
βββ tests
βΒ Β  βββ __init__.py
βΒ Β  βββ ...
βββ requirements
βΒ Β  βββ develop.txt
βΒ Β  βββ product.txt
βββ requirements.txt
βββ install.sh
βββ config.py
βββ wsgi.py
βββ ...
βββ LICENSE
βββ README.md
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

Licensed under the MIT License, Copyright Β© 2021-present Hsins.
