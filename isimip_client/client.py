import hashlib
import zipfile
import time

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

    def download(self, url, path=None, validate=True, extract=True):
        headers = self.headers.copy()

        file_name = Path(urlparse(url).path.split('/')[-1])
        file_path = (Path(path) if path else Path.cwd()) / file_name
        file_path.parent.mkdir(exist_ok=True, parents=True)
        if file_path.exists():
            # resume download
            headers.update({'Range': f'bytes={file_path.stat().st_size}-'})

        response = requests.get(url, stream=True, headers=headers)
        if response.status_code == 416:
            # download is complete
            pass
        else:
            response.raise_for_status()

            with open(file_path, 'ab') as fd:
                for chunk in response.iter_content(chunk_size=65*1024):
                    fd.write(chunk)

        if validate:
            json_url = url.rsplit('/', 1)[0] + '/' + file_name.with_suffix('.json').as_posix()
            response = requests.get(json_url, headers=self.headers)
            response.raise_for_status()
            json_data = response.json()
            remote_checksum, remote_path = json_data['checksum'], json_data['path']

            # compute file checksum
            m = hashlib.sha512()
            with open(file_path, 'rb') as fp:
                # read and update in blocks of 64K
                for block in iter(lambda: fp.read(65536), b''):
                    m.update(block)
            checksum = m.hexdigest()

            assert remote_path.endswith(file_name.as_posix())
            assert remote_checksum == checksum, f'Checksum {checksum} != {remote_checksum}'

        if file_path.suffix == '.zip' and extract:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(path)

    def mask(self, paths, country=None, bbox=None, landonly=None, poll=None):
        payload = {}

        if isinstance(paths, list):
            payload['paths'] = paths
        else:
            payload['paths'] = [paths]

        if country is not None:
            payload['task'] = 'mask_country'
            payload['country'] = country
        elif bbox is not None:
            payload['task'] = 'mask_bbox'
            payload['bbox'] = bbox
        elif landonly is not None:
            payload['task'] = 'mask_landonly'

        response = requests.post(self.files_api_url, json=payload, auth=self.auth, headers=self.headers)
        job = self.parse_response(response)
        if poll:
            return self.poll(job, self.mask, [paths, country, bbox, landonly, poll], poll)
        else:
            return job

    def cutout(self, paths, bbox, poll=None):
        payload = {
            'task': 'cutout_bbox',
            'bbox': bbox
        }

        if isinstance(paths, list):
            payload['paths'] = paths
        else:
            payload['paths'] = [paths]

        response = requests.post(self.files_api_url, json=payload, auth=self.auth, headers=self.headers)
        job = self.parse_response(response)
        if poll:
            return self.poll(job, self.cutout, [paths, bbox, poll], poll)
        else:
            return job

    def select(self, paths, country=None, bbox=None, point=None, poll=None):
        payload = {}

        if isinstance(paths, list):
            payload['paths'] = paths
        else:
            payload['paths'] = [paths]

        if country is not None:
            payload['task'] = 'select_country'
            payload['country'] = country
        elif bbox is not None:
            payload['task'] = 'select_bbox'
            payload['bbox'] = bbox
        elif point is not None:
            payload['task'] = 'select_point'
            payload['point'] = point

        response = requests.post(self.files_api_url, json=payload, auth=self.auth, headers=self.headers)
        job = self.parse_response(response)
        if poll:
            return self.poll(job, self.select, [paths, country, bbox, point, poll], poll)
        else:
            return job

    def poll(self, job, method, args, poll_sleep):
        print('job', job['id'], job['status'], job['meta'] if job['meta'] else '')
        if job['status'] in ['queued', 'started']:
            time.sleep(poll_sleep)
            return method(*args)
        else:
            return job
