import hashlib
import json
import logging
import time
import zipfile
from pathlib import Path
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)


class HTTPClient:

    def __init__(self, base_url, auth, headers):
        self.base_url, self.auth, self.headers = base_url, auth, headers

    def parse_response(self, response):
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(response.content)
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
            url += '{}/'.format(kwargs.pop('parent_pk'))
            url += kwargs.pop('nested_route').rstrip('/') + '/'

        if pk:
            url += f'{pk}/'

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


class DataApiMixin:

    def datasets(self, **kwargs):
        return self.list('/datasets', **kwargs)

    def dataset(self, pk, **kwargs):
        return self.retrieve('/datasets', pk, **kwargs)

    def files(self, **kwargs):
        return self.list('/files', **kwargs)

    def file(self, pk, **kwargs):
        return self.retrieve('/files', pk, **kwargs)


class FilesApiMixin:

    def check(self, version):
        if self.files_api_version != version:
            raise RuntimeError(f'This method is only available in {version} of the Files API. '
                               f'Please set "files_api_version=\'{version}\'".')

    def post_job(self, data, uploads=None, poll=None):
        logger.info(f'job submitted data={data} uploads={uploads}')

        if uploads is None:
            response = requests.post(self.files_api_url, json=data, auth=self.auth, headers=self.headers)
        else:
            files = {'data': json.dumps(data)}
            for upload in uploads:
                upload_path = Path(upload).expanduser()
                files[upload_path.name] = upload_path.read_bytes()
            response = requests.post(self.files_api_url, files=files, auth=self.auth, headers=self.headers)


        job = self.parse_response(response)
        self.log_job(job)

        if poll and job['status'] in ['queued', 'started']:
            time.sleep(poll)
            return self.get_job(job['job_url'], poll=poll)
        else:
            return job

    def get_job(self, job_url, poll=None):
        response = requests.get(job_url, auth=self.auth, headers=self.headers)

        job = self.parse_response(response)
        self.log_job(job)

        if poll and job['status'] in ['queued', 'started']:
            time.sleep(poll)
            return self.get_job(job['job_url'], poll=poll)
        else:
            return job

    def log_job(self, job):
        if job['status'] == 'finished':
            logger.info('job {id} {status} meta={meta} file_url={file_url}'.format(**job))
        else:
            logger.info('job {id} {status} meta={meta}'.format(**job))

class FilesApiV1Mixin:

    def mask(self, paths, country=None, bbox=None, landonly=None, poll=None):
        self.check('v1')

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

        return self.post_job(payload, poll=poll)

    def cutout(self, paths, bbox, poll=None):
        self.check('v1')

        payload = {
            'task': 'cutout_bbox',
            'bbox': bbox
        }

        if isinstance(paths, list):
            payload['paths'] = paths
        else:
            payload['paths'] = [paths]

        return self.post_job(payload, poll=poll)

    def select(self, paths, country=None, bbox=None, point=None, poll=None):
        self.check('v1')

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

        return self.post_job(payload, poll=poll)


class FilesApiV2Mixin:

    def submit_job(self, paths, operations, uploads, poll=None):
        self.check('v2')
        return self.post_job({
            'paths': paths,
            'operations': operations
        }, uploads=uploads, poll=poll)

    def select_bbox(self, paths, bbox, poll=None):
        self.check('v2')
        return self.post_job({
            'paths': paths,
            'operations': [
                {
                    'operation': 'select_bbox',
                    'bbox': bbox
                }
            ]
        }, poll=poll)

    def select_point(self, paths, point, poll=None):
        self.check('v2')
        return self.post_job({
            'paths': paths,
            'operations': [
                {
                    'operation': 'select_point',
                    'point': point
                }
            ]
        }, poll=poll)

    def mask_bbox(self, paths, bbox, poll=None):
        self.check('v2')
        return self.post_job({
            'paths': paths,
            'operations': [
                {
                    'operation': 'mask_bbox',
                    'bbox': bbox
                }
            ]
        }, poll=poll)

    def mask_country(self, paths, country, poll=None):
        self.check('v2')
        return self.post_job({
            'paths': paths,
            'operations': [
                {
                    'operation': 'mask_country',
                    'country': country
                }
            ]
        }, poll=poll)

    def mask_landonly(self, paths, poll=None):
        self.check('v2')
        return self.post_job({
            'paths': paths,
            'operations': [
                {
                    'operation': 'mask_landonly'
                }
            ]
        }, poll=poll)

    def mask_mask(self, paths, mask, var, compute_mean=False, output_csv=False, poll=None):
        self.check('v2')
        mask = Path(mask)
        return self.post_job({
            'paths': paths,
            'operations': [
                {
                    'operation': 'mask_mask',
                    'mask': mask.name,
                    'compute_mean': compute_mean,
                    'output_csv': output_csv,
                    'var': var
                }
            ]
        }, uploads=[mask], poll=poll)

    def mask_shape(self, paths, shape, layer, compute_mean=False, output_csv=False, poll=None):
        self.check('v2')
        shape = Path(shape)
        mask = shape.with_suffix('.nc')
        var = f'm_{layer}'
        return self.post_job({
            'paths': paths,
            'operations': [
                {
                    'operation': 'create_mask',
                    'shape': shape.name,
                    'mask': mask.name,
                },
                {
                    'operation': 'mask_mask',
                    'mask': mask.name,
                    'compute_mean': compute_mean,
                    'output_csv': output_csv,
                    'var': var
                }
            ]
        }, uploads=[shape], poll=poll)

    def cutout_bbox(self, paths, bbox, poll=None):
        self.check('v2')
        return self.post_job({
            'paths': paths,
            'operations': [
                {
                    'operation': 'cutout_bbox',
                    'bbox': bbox
                }
            ]
        }, poll=poll)

    def cutout_point(self, paths, point, poll=None):
        self.check('v2')
        return self.post_job({
            'paths': paths,
            'operations': [
                {
                    'operation': 'cutout_point',
                    'point': point
                }
            ]
        }, poll=poll)


class DownloadMixin:

    def download(self, url, path=None, validate=False, extract=True):
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


class ISIMIPClient(DataApiMixin, FilesApiMixin, FilesApiV1Mixin, FilesApiV2Mixin, DownloadMixin, RESTClient):

    def __init__(self, data_url='https://data.isimip.org/api/v1', files_api_url='https://files.isimip.org/api/v1',
                 files_api_version='v1', auth=None, headers={}):
        self.data_url = data_url
        self.files_api_url = files_api_url
        self.files_api_version = files_api_version

        self.base_url = data_url
        self.auth = auth
        self.headers = {}
