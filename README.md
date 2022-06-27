# CAI Tools

# Description

Simple python tools to automate several routine Cloud Asset Inventory task including see identity permission, compare two identity permission & get all resource which have public access.

# Requirement

- python >= v3.x
- pip
- [google-cloud-asset library](https://github.com/googleapis/python-asset)
- [prettytable](https://pypi.org/project/prettytable/)
- [colorama](https://pypi.org/project/colorama/)

# Installation

> It’s recommended to run this tools in virtual environment to avoid dependency conflict with other project, but it can also run in global environment.
> 

## Inside Virtual Environment

Create new virtual environment for the tools run

```bash
virtualenv <your-venv-name>
```

Activate the virtual environment

```bash
source <your-venv-name>/bin/activate
```

Install all dependency

```bash
<your-venv-bame>/bin/pip install -r requirements.txt
```

Generate new Service Account that tool will used from gcloud console, download, then enter the absolute path of the downloaded key by running this command

```bash
<your-venv-name>/bin/python3 caitools.py --init-auth
```

Run the tools

```bash
<your-venv-name>/bin/python3 caitools.py --help
```

Done !

> To exit from virtual environment just type `exit` command
> 

## Global Environment

Install all dependency

```bash
pip install -r requirements.txt
```

Generate new Service Account that tool will used from gcloud console, download, then enter the absolute path of the downloaded key by running this command

```bash
python3 caitools.py --init-auth
```

Run the tools

```bash
python3 caitools.py --help
```

Done !
