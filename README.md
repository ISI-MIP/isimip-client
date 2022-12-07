isimip-client
=============

A *thin* client library to use the API of the [ISIMIP repository](https://data.isimip.org) using Python.

Setup
-----

The library is written in Python (> 3.6) uses only dependencies, which can be installed without administrator priviledges. The installation of Python (and its developing packages), however differs from operating system to operating system. Optional Git is needed if the application is installed directly from GitHub. The installation of Python 3 and Git for different plattforms is documented [here](https://github.com/ISI-MIP/isimip-utils/blob/master/docs/prerequisites.md).

The library can be installed via pip. Usually you want to create a [virtual environment](https://docs.python.org/3/library/venv.html) first, but this is optional.

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
pip install -r notebooks/requirements.txt
```

Then Jupyter lab can be started using:

```bash
jupyter lab
```
