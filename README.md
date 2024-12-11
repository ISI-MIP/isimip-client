isimip-client
=============

[![Latest release](https://shields.io/github/v/release/ISI-MIP/isimip-client)](https://github.com/ISI-MIP/isimip-client/releases)
[![PyPI release](https://img.shields.io/pypi/v/isimip-client)](https://pypi.org/project/isimip-client/)
[![Python Version](https://img.shields.io/badge/python->=3.9-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](https://github.com/ISI-MIP/isimip-qc/blob/master/LICENSE)

A *thin* client library to use the API of the [ISIMIP repository](https://data.isimip.org) using Python.

Setup
-----

The library is written in Python (> 3.9) uses only dependencies, which can be installed without administrator priviledges. The installation of Python (and its developing packages), however differs from operating system to operating system. The installation of Python 3 for different plattforms is documented [here](https://github.com/ISI-MIP/isimip-utils/blob/master/docs/prerequisites.md).

The library can be installed via pip. Usually you want to create a [virtual environment](https://docs.python.org/3/library/venv.html) first, but this is optional:

```bash
# setup venv on Linux/macOS/Windows WSL
python3 -m venv env
source env/bin/activate

# setup venv on Windows cmd
python -m venv env
call env\Scripts\activate.bat
```

The library can conveniently installed using `pip`:

```
pip install isimip-client
```

Usage
-----

The package provides a the Python class `ISIMIPClient` which can be used in scripts or notebooks in the following way:

```python
from isimip_client.client import ISIMIPClient

client = ISIMIPClient()
```

The methods of this `client` object can then be used to perform queries to the ISIMIP Repository, e.g. to seach for datasets

```python
# search the ISIMIP repository using a search string
response = client.datasets(query='gfdl-esm4 ssp370 pr')

# search the ISIMIP repository for a specific subtree
response = client.datasets(path='ISIMIP3b/InputData/climate/atmosphere/bias-adjusted/global/daily/ssp370/GFDL-ESM4/')

# search the ISIMIP repository using specifiers
response = client.datasets(simulation_round='ISIMIP3b',
                           product='InputData',
                           climate_forcing='gfdl-esm4',
                           climate_scenario='ssp370',
                           climate_variable='pr')
```

The response object is a dictionary of the form

```python
{
    "count": 1001,
    "next": "https://data.isimip.org/api/v1/datasets/?page=2&...",
    "previous": null,
    "results": [
        ...
    ]
}
```

where each result contains the information for one dataset matching the provided search criteria. By default, only 10 datasets are returned and you can access the next 10 by providing `page=2` to the `datasets` method. You can also use `page_size=N` to increase the number of returned results per page.

Similar searches can be performed on the `files` endpoint, e.g.:

```python
response = client.files(...)
```

The ISIMIP Repository proviedes a "Configure download" feature, which can be used to perform operations on a set of files before downloading them. A common use case it the cut-out of a specific region. Technical details about this Files API can be found [here](https://github.com/ISI-MIP/isimip-files-api). The client can be used to perform the same operations which are available on the webpage:

```python
response = client.select_bbox(paths, west, east, south, north, poll=poll)

response = client.select_point(paths, lat, lon, poll=poll)

response = client.mask_bbox(paths, west, east, south, north, poll=poll)

response = client.mask_country(paths, country, poll=poll)

response = client.mask_landonly(paths, poll=poll)

response = client.mask_mask(paths, mask, var, poll=poll)

response = client.mask_shape(paths, shapefile, layer, poll=poll)

response = client.mask_shape(paths, geojson, layer, poll=poll)

response = client.cutout_bbox(paths, west, east, south, north, poll=poll)

response = client.cutout_point(paths, lat, lon, poll=poll)

# in order to download the created zip file, download method can be used
client.download(response['file_url'], path='downloads')
```

In addition, the client allows to use the API with a custom list of operations. In order to first cut out a rectangular area from the CHELSA high resolution data and then cut out a shape from a shapefile, you can use:

```python
# Admin 0 - Countries from https://www.naturalearthdata.com
ne_shape = Path('~/data/isimip/shapes/ne_10m_admin_0_sovereignty.zip')
ne_mask = ne_shape.with_suffix('.nc')

# ISIMIP3a high resolution precipitation input data
paths = [
    'ISIMIP3a/InputData/climate/atmosphere/obsclim/global/daily/historical/CHELSA-W5E5/chelsa-w5e5_obsclim_pr_30arcsec_global_daily_201612.nc',
    ...
]

# chain of operations
operations = [
    {
        'operation': 'cutout_bbox',
        'bbox': [
             5.800,  # west
            10.600,  # east
            45.800,  # south
            47.900   # north
        ]
    },
    {
        'operation': 'create_mask',
        'shape': ne_shape.name,
        'mask': ne_mask.name,
    },
    {
        'operation': 'mask_mask',
        'mask': ne_mask.name,
        'var': 'm_91'  # switzerland layer 91 in the shapefile
    }
]

# list of uploaded files, referenced in the operations list
uploads = [ne_shape]

# sumbit the prepared job to the API and poll every 4 seconds for it's status
response = client.submit_job(paths, operations, uploads, poll=4)
```

Before 2025, the File API was only available in its first version, which can still be used:

```python
client = ISIMIPClient(files_api_url='https://files.isimip.org/api/v1', files_api_version='v1')

client.select(paths, bbox=[south, north, west, east])
client.select(paths, point=(lat, lon))
client.select(paths, country=country)

client.mask(paths, bbox=[south, north, west, east])
client.mask(paths, country=country)
client.mask(paths, landonly=True)

client.cutout(paths, bbox=[south, north, west, east])
```

More examples can be found in the [notebooks directory](/notebooks).


Command line client
-------------------

Most features of the client can also be used on the command line using the `isimip-client` command, e.g.:

```bash
isimip-client select_bbox   [PATHS]... --west=-20 --east=20 --south=-10 --north=10

isimip-client select_point  [PATHS]... --lat=6.25 --lon=18.17

isimip-client mask_bbox     [PATHS]... --west=-20 --east=20 --south=-10 --north=10

isimip-client mask_country  [PATHS]... --country=bra

isimip-client mask_landonly [PATHS]...

isimip-client mask_mask     [PATHS]... --mask=~/data/isimip/api/countrymasks.nc --var=m_AUS

isimip-client mask_shape    [PATHS]... --shape=~/data/isimip/shapes/World_Continents.zip --layer=3

isimip-client mask_shape    [PATHS]... --shape=~/data/isimip/shapes/World_Continents.geojson --layer=4

isimip-client cutout_bbox   [PATHS]... --west=-20 --east=20 --south=-10 --north=10

isimip-client cutout_point  [PATHS]... --lat=6.25 --lon=18.17
```

where `[PATHS]...` denotes the list of ISIMIP file path to process, seperated by spaces.


Jupyter notebooks
-----------------

I you want to run the included jupyter notebooks, you can install the additional packages using:

```
pip install isimip-client[jupyter]
```

Then Jupyter lab can be started using:

```bash
jupyter lab
```

The example notebooks are in the `notebooks` directory.
