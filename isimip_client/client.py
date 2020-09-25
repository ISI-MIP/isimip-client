from pathlib import Path
from urllib.parse import urlparse

import requests


class HTTPClient(object):

    def __init__(self, base_url, auth, headers):
        self.base_url, self.auth, self.headers = base_url, auth, headers

    def parse_response(self, response):
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(response.content)
            raise e

    def get(self, url, params={}):
        response = requests.get(self.base_url + url, params=params, auth=self.auth, headers=self.headers)
        return self.parse_response(response)

    def post(self, url, data):
        response = requests.post(self.base_url + url, json=data, auth=self.auth, headers=self.headers)
        return self.parse_response(response)

    def put(self, url, data):
        response = requests.put(self.base_url + url, data, auth=self.auth, headers=self.headers)
        return self.parse_response(response)

    def patch(self, url, data):
        response = requests.patch(self.base_url + url, json=data, auth=self.auth, headers=self.headers)
        return self.parse_response(response)

    def delete(self, url):
        response = requests.delete(self.base_url + url, auth=self.auth, headers=self.headers)
        return self.parse_response(response)


class RESTClient(HTTPClient):

    def _build_url(self, resource_url, kwargs, pk=None):
        url = resource_url.rstrip('/') + '/'

        if 'list_route' in kwargs:
            url += kwargs.pop('list_route').rstrip('/') + '/'
        elif 'nested_route' in kwargs:
            url += '%s/' % kwargs.pop('parent_pk')
            url += kwargs.pop('nested_route').rstrip('/') + '/'

        if pk:
            url += '%s/' % pk

        if 'detail_route' in kwargs:
            url += kwargs.pop('detail_route').rstrip('/') + '/'

        return url

    def list(self, resource_url, **kwargs):
        url = self._build_url(resource_url, kwargs)
        return self.get(url, params=kwargs)

    def retrieve(self, resource_url, pk, **kwargs):
        url = self._build_url(resource_url, kwargs, pk)
        return self.get(url)

    def create(self, resource_url, data, **kwargs):
        url = self._build_url(resource_url, kwargs)
        return self.post(url, data)

    def update(self, resource_url, pk, data, **kwargs):
        url = self._build_url(resource_url, kwargs, pk)
        return self.put(url, data)

    def destroy(self, resource_url, pk, **kwargs):
        url = self._build_url(resource_url, kwargs, pk)
        return self.delete(url, pk)


class ISIMIPClient(RESTClient):

    def __init__(self, data_url='https://data.isimip.org/api/v1', files_api_url='https://files.isimip.org/api/v1',
                 auth=None, headers={}):
        self.data_url = data_url
        self.files_api_url = files_api_url

        self.base_url = data_url
        self.auth = auth
        self.headers = {}

    def datasets(self, **kwargs):
        return self.list('/datasets', **kwargs)

    def dataset(self, pk, **kwargs):
        return self.retrieve('/datasets', pk, **kwargs)

    def files(self, **kwargs):
        return self.list('/files', **kwargs)

    def file(self, pk, **kwargs):
        return self.retrieve('/files', pk, **kwargs)

    def download(self, url, path=None):
        response = requests.get(url, stream=True)
        response.raise_for_status()

        file_path = Path(path) if path else Path.cwd()
        file_name = urlparse(url).path.split('/')[-1]
        with open(file_path / file_name, 'wb') as fd:
            for chunk in response.iter_content(chunk_size=128):
                fd.write(chunk)

    def mask(self, path, country=None):
        if country is not None:
            response = requests.post(self.files_api_url, json={
                'path': path,
                'country': country
            }, auth=self.auth, headers=self.headers)
            return self.parse_response(response)
