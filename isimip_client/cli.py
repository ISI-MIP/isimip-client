import logging

import click
from rich import print_json
from rich.console import Console
from rich.logging import RichHandler
from rich.pretty import pretty_repr
from rich.table import Table
from rich.text import Text

from .client import ISIMIPClient

logging.basicConfig(level='INFO', format='%(message)s', handlers=[RichHandler()])


class SearchArgumentType(click.ParamType):
    name = "search"

    def convert(self, value, param, ctx):
        try:
            search_key, search_value = value.split('=')
            return (search_key, search_value)
        except ValueError:
            self.fail(f'{param} needs to be of the form key=value')


@click.group()
@click.pass_context
def main(ctx):
    ctx.ensure_object(dict)
    ctx.obj['client'] = ISIMIPClient(
        data_url='https://data.isimip.org/api/v1',
        files_api_url='https://files.isimip.org/api/v2',
        files_api_version='v2'
    )


@main.result_callback()
@click.pass_context
def print_response(ctx, response, **kwargs):
    if response:
        if ctx.obj.get('download'):
            if 'file_url' in response:
                ctx.obj['client'].download(response['file_url'], validate=False, extract=False)
        elif ctx.obj.get('json'):
            print_json(data=response)
        else:
            table = Table()

            if 'results' in response:
                table.add_column('id', style='green')
                table.add_column('path', style='cyan')
                table.add_column('version')
                for result in response['results']:
                    row = [result[key] for key in ['id', 'path', 'version']]
                    table.add_row(*row)
            else:
                table.add_column('key')
                table.add_column('value')
                for key in [
                    'id',
                    'path',
                    'version',
                    'size',
                    'checksum',
                    'checksum_type',
                    'specifiers',
                    'url',
                    'metadata_url',
                    'file_url',
                    'json_url'
                ]:
                    value = response.get(key, '')
                    if isinstance(value, dict):
                        table.add_row(key, pretty_repr(value))
                    else:
                        text = Text(str(value))
                        if key == 'id':
                            text.stylize('green')
                        elif key == 'path':
                            text.stylize('cyan')
                        table.add_row(key, text)

            console = Console()
            console.print(table)


@main.command()
@click.pass_context
@click.argument('search', nargs=-1, type=SearchArgumentType())
@click.option('--page', default=1)
@click.option('--page-size', default=10)
@click.option('--json', is_flag=True)
def datasets(ctx, search, json, **kwargs):
    ctx.obj['json'] = json
    return ctx.obj['client'].datasets(**dict(search, **kwargs))


@main.command()
@click.pass_context
@click.argument('id')
@click.option('--json', is_flag=True)
def dataset(ctx, id, json):
    ctx.obj['json'] = json
    return ctx.obj['client'].dataset(id)


@main.command()
@click.pass_context
@click.argument('search', nargs=-1, type=SearchArgumentType())
@click.option('--page', default=1)
@click.option('--page-size', default=10)
@click.option('--json', is_flag=True)
def files(ctx, search, json, **kwargs):
    ctx.obj['json'] = json
    return ctx.obj['client'].files(**dict(search, **kwargs))


@main.command()
@click.pass_context
@click.argument('id')
@click.option('--json', is_flag=True)
def file(ctx, id, json):
    ctx.obj['json'] = json
    return ctx.obj['client'].file(id)


@main.command(name='select_bbox')
@click.pass_context
@click.argument('paths', nargs=-1, type=click.STRING)
@click.option('--west', type=click.FLOAT, required=True)
@click.option('--east', type=click.FLOAT, required=True)
@click.option('--south', type=click.FLOAT, required=True)
@click.option('--north', type=click.FLOAT, required=True)
@click.option('--mean', is_flag=True)
@click.option('--csv', is_flag=True)
@click.option('--poll', type=click.INT, default=4)
def select_bbox(ctx, **kwargs):
    ctx.obj['download'] = True
    return ctx.obj['client'].select_bbox(**kwargs)


@main.command(name='select_point')
@click.pass_context
@click.argument('paths', nargs=-1, type=click.STRING)
@click.option('--lat', type=click.FLOAT, required=True)
@click.option('--lon', type=click.FLOAT, required=True)
@click.option('--csv', is_flag=True)
@click.option('--poll', type=click.INT, default=4)
def select_point(ctx, **kwargs):
    ctx.obj['download'] = True
    return ctx.obj['client'].select_point(**kwargs)


@main.command(name='mask_bbox')
@click.pass_context
@click.argument('paths', nargs=-1, type=click.STRING)
@click.option('--west', type=click.FLOAT, required=True)
@click.option('--east', type=click.FLOAT, required=True)
@click.option('--south', type=click.FLOAT, required=True)
@click.option('--north', type=click.FLOAT, required=True)
@click.option('--mean', is_flag=True)
@click.option('--csv', is_flag=True)
@click.option('--poll', type=click.INT, default=4)
def mask_bbox(ctx, **kwargs):
    ctx.obj['download'] = True
    return ctx.obj['client'].mask_bbox(**kwargs)


@main.command(name='mask_country')
@click.pass_context
@click.argument('paths', nargs=-1, type=click.STRING)
@click.option('--country', type=click.STRING, required=True)
@click.option('--mean', is_flag=True)
@click.option('--csv', is_flag=True)
@click.option('--poll', type=click.INT, default=4)
def mask_country(ctx, **kwargs):
    ctx.obj['download'] = True
    return ctx.obj['client'].mask_country(**kwargs)


@main.command(name='mask_landonly')
@click.pass_context
@click.argument('paths', nargs=-1, type=click.STRING)
def mask_landonly(ctx, **kwargs):
    ctx.obj['download'] = True
    return ctx.obj['client'].mask_landonly(**kwargs)


@main.command(name='mask_mask')
@click.pass_context
@click.argument('paths', nargs=-1, type=click.STRING)
@click.option('--mask', type=click.Path(), required=True)
@click.option('--var', type=click.STRING, required=True)
@click.option('--mean', is_flag=True)
@click.option('--csv', is_flag=True)
@click.option('--poll', type=click.INT, default=4)
def mask_mask(ctx, **kwargs):
    ctx.obj['download'] = True
    return ctx.obj['client'].mask_mask(**kwargs)


@main.command(name='mask_shape')
@click.pass_context
@click.argument('paths', nargs=-1, type=click.STRING)
@click.option('--shape', type=click.Path(), required=True)
@click.option('--layer', type=click.INT, required=True)
@click.option('--mean', is_flag=True)
@click.option('--csv', is_flag=True)
@click.option('--poll', type=click.INT, default=4)
def mask_shape(ctx, **kwargs):
    ctx.obj['download'] = True
    return ctx.obj['client'].mask_shape(**kwargs)


@main.command(name='cutout_bbox')
@click.pass_context
@click.argument('paths', nargs=-1, type=click.STRING)
@click.option('--west', type=click.FLOAT, required=True)
@click.option('--east', type=click.FLOAT, required=True)
@click.option('--south', type=click.FLOAT, required=True)
@click.option('--north', type=click.FLOAT, required=True)
@click.option('--mean', is_flag=True)
@click.option('--csv', is_flag=True)
@click.option('--poll', type=click.INT, default=4)
def cutout_bbox(ctx, **kwargs):
    ctx.obj['download'] = True
    return ctx.obj['client'].cutout_bbox(**kwargs)


@main.command(name='cutout_point')
@click.pass_context
@click.argument('paths', nargs=-1, type=click.STRING)
@click.option('--lat', type=click.FLOAT, required=True)
@click.option('--lon', type=click.FLOAT, required=True)
@click.option('--csv', is_flag=True)
@click.option('--poll', type=click.INT, default=4)
def cutout_point(ctx, **kwargs):
    ctx.obj['download'] = True
    return ctx.obj['client'].cutout_point(**kwargs)
