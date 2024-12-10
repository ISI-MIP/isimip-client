import logging

import click
from rich import print_json
from rich.logging import RichHandler

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
        if 'file_url' in response:
            ctx.obj['client'].download(response['file_url'], validate=False, extract=False)
        else:
            print_json(data=response)


@main.command()
@click.pass_context
@click.argument('search', nargs=-1, type=SearchArgumentType())
@click.option('--page', default=1)
@click.option('--page-size', default=10)
def datasets(ctx, search, **kwargs):
    return ctx.obj['client'].datasets(**dict(search, **kwargs))


@main.command()
@click.pass_context
@click.argument('id')
def dataset(ctx, **kwargs):
    return ctx.obj['client'].dataset(**kwargs)


@main.command()
@click.pass_context
@click.argument('search', nargs=-1, type=SearchArgumentType())
@click.option('--page', default=1)
@click.option('--page-size', default=10)
def files(ctx, search, **kwargs):
    return ctx.obj['client'].files(**dict(search, **kwargs))


@main.command()
@click.pass_context
@click.argument('id')
def file(ctx, **kwargs):
    return ctx.obj['client'].file(**kwargs)


@main.command(name='select_bbox')
@click.pass_context
@click.argument('paths', nargs=-1, type=click.STRING)
@click.option('--west', type=click.FLOAT, required=True)
@click.option('--east', type=click.FLOAT, required=True)
@click.option('--south', type=click.FLOAT, required=True)
@click.option('--north', type=click.FLOAT, required=True)
@click.option('--mean', type=click.BOOL, default=False)
@click.option('--csv', type=click.BOOL, default=False)
@click.option('--poll', type=click.INT, default=4)
def select_bbox(ctx, **kwargs):
    return ctx.obj['client'].select_bbox(**kwargs)


@main.command(name='select_point')
@click.pass_context
@click.argument('paths', nargs=-1, type=click.STRING)
@click.option('--lat', type=click.FLOAT, required=True)
@click.option('--lon', type=click.FLOAT, required=True)
@click.option('--csv', type=click.BOOL, default=False)
@click.option('--poll', type=click.INT, default=4)
def select_point(ctx, **kwargs):
    return ctx.obj['client'].select_point(**kwargs)


@main.command(name='mask_bbox')
@click.pass_context
@click.argument('paths', nargs=-1, type=click.STRING)
@click.option('--west', type=click.FLOAT, required=True)
@click.option('--east', type=click.FLOAT, required=True)
@click.option('--south', type=click.FLOAT, required=True)
@click.option('--north', type=click.FLOAT, required=True)
@click.option('--mean', type=click.BOOL, default=False)
@click.option('--csv', type=click.BOOL, default=False)
@click.option('--poll', type=click.INT, default=4)
def mask_bbox(ctx, **kwargs):
    return ctx.obj['client'].mask_bbox(**kwargs)


@main.command(name='mask_country')
@click.pass_context
@click.argument('paths', nargs=-1, type=click.STRING)
@click.option('--country', type=click.STRING, required=True)
@click.option('--mean',type=click.BOOL, default=False)
@click.option('--csv', type=click.BOOL, default=False)
@click.option('--poll', type=click.INT, default=4)
def mask_country(ctx, **kwargs):
    return ctx.obj['client'].mask_country(**kwargs)


@main.command(name='mask_landonly')
@click.pass_context
@click.argument('paths', nargs=-1, type=click.STRING)
def mask_landonly(ctx, **kwargs):
    return ctx.obj['client'].mask_landonly(**kwargs)


@main.command(name='mask_mask')
@click.pass_context
@click.argument('paths', nargs=-1, type=click.STRING)
@click.option('--mask', type=click.Path(), required=True)
@click.option('--var', type=click.STRING, required=True)
@click.option('--mean',type=click.BOOL, default=False)
@click.option('--csv', type=click.BOOL, default=False)
@click.option('--poll', type=click.INT, default=4)
def mask_mask(ctx, **kwargs):
    return ctx.obj['client'].mask_mask(**kwargs)


@main.command(name='mask_shape')
@click.pass_context
@click.argument('paths', nargs=-1, type=click.STRING)
@click.option('--shape', type=click.Path(), required=True)
@click.option('--layer', type=click.INT, required=True)
@click.option('--mean',type=click.BOOL, default=False)
@click.option('--csv', type=click.BOOL, default=False)
@click.option('--poll', type=click.INT, default=4)
def mask_shape(ctx, **kwargs):
    return ctx.obj['client'].mask_shape(**kwargs)


@main.command(name='cutout_bbox')
@click.pass_context
@click.argument('paths', nargs=-1, type=click.STRING)
@click.option('--west', type=click.FLOAT, required=True)
@click.option('--east', type=click.FLOAT, required=True)
@click.option('--south', type=click.FLOAT, required=True)
@click.option('--north', type=click.FLOAT, required=True)
@click.option('--mean',type=click.BOOL, default=False)
@click.option('--csv', type=click.BOOL, default=False)
@click.option('--poll', type=click.INT, default=4)
def cutout_bbox(ctx, **kwargs):
    return ctx.obj['client'].cutout_bbox(**kwargs)


@main.command(name='cutout_point')
@click.pass_context
@click.argument('paths', nargs=-1, type=click.STRING)
@click.option('--lat', type=click.FLOAT, required=True)
@click.option('--lon', type=click.FLOAT, required=True)
@click.option('--csv', type=click.BOOL, default=False)
@click.option('--poll', type=click.INT, default=4)
def cutout_point(ctx, **kwargs):
    return ctx.obj['client'].cutout_point(**kwargs)
