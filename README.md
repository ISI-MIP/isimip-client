isimip-client
=============

A *thin* client library to use the API of the [ISIMIP repository](https://data.isimip.org) using Python.

Prerequisites
-------------

### Linux

On Linux, Python3 is probably already installed, but the development packages are usually not. You should be able to install them using:

```
# Ubuntu/Debian
sudo apt-get install python3 python3-dev python3-venv

# CentOS/RHEL
sudo yum install python3 python3-devel

# openSUSE/SLES
zypper install python3 python3-devel
```

Git can be installed in a similar way using the `git` package (on all distributions).

### macOS

While we reccoment using [Homebrew](https://brew.sh) to install Python3 on a Mac, other means of obtaining Python like [Anaconda](https://www.anaconda.com/products/individual), [MacPorts](https://www.macports.org/), or [Fink](https://www.finkproject.org/) should work just as fine:

```
brew install python
brew install git
```

### Windows

#### Regular installation

The software prerequisites need to be downloaded and installed from their particular web sites.

For python:
* download from <https://www.python.org/downloads/windows/>
* use the 64bit version if your system is not very old
* **don't forget to check 'Add Python to PATH' during setup**

For git:
* download from <https://git-for-windows.github.io/>
* use the 64bit version if your system is not very old

#### Using the Windows Subsystem for Linux (WSL)

As an alternative for advanced users, you can use the Windows Subsystem for Linux (WSL) to install a Linux distribution whithin Windows 10. The installation is explained in the [Microsoft documentation](https://docs.microsoft.com/en-us/windows/wsl/install-win10). When using WSL, please install Python3 as explained in the Linux section.


Setup
-----

The library can be installed via pip. Usually you want to create a [virtual environment]() first, but this is optional.

```bash
# setup venv on Linux/macOS/Windows WSL
python3 -m venv env
source env/bin/activate

# setup venv on Windows cmd
python -m venv env
call env\Scripts\activate.bat

# install from GitHub
pip install git+https://github.com/ISI-MIP/isimip-client

# update from Github
pip install -I git+https://github.com/ISI-MIP/isimip-client
```


Usage
-----

The library is used in the following way:

```python
from isimip_client.client import ISIMIPClient
client = ISIMIPClient()

# search the ISIMIP repository using a search string
response = client.datasets(query='gfdl-esm4 ssp370 pr')

# search the ISIMIP repository for a specific subtree
response = client.datasets(tree='ISIMIP3b/InputData/climate/atmosphere/global/daily/ssp370/gfdl-esm4/r1i1p1f1/w5e5/pr')

# search the ISIMIP repository using specifiers
response = client.datasets(simulation_round='ISIMIP3b',
                           product='InputData',
                           climate_forcing='gfdl-esm4',
                           climate_scenario='ssp370',
                           climate_variable='pr')
```

In order to use the `dev` version of the repository use:

```python
client = ISIMIPClient(data_url='https://dev.isimip.org/api/v1', auth=(USER, PASS))
```

More examples can be found in the [notebooks directory](/notebooks).


Jupyter notebooks
-----------------

I you want to run the included jupyter notebooks, you can install the additional packages using:

```
pip install jupyter jupyterlab
```

Then Jupyter lab can be started using:

```bash
jupyter lab
```
