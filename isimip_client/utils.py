import click
from rich.console import Console
from rich.pretty import pretty_repr
from rich.table import Table
from rich.text import Text


class SearchArgumentType(click.ParamType):
    name = "search"

    def convert(self, value, param, ctx):
        try:
            search_key, search_value = value.split('=')
            return (search_key, search_value)
        except ValueError:
            self.fail(f'{param} needs to be of the form key=value')


def print_results_table(results):
    table = Table()
    table.add_column('id', style='green')
    table.add_column('path', style='cyan')
    table.add_column('version')

    for result in results:
        row = [result[key] for key in ['id', 'path', 'version']]
        table.add_row(*row)

    console = Console()
    console.print(table)


def print_details_table(details):
    table = Table()
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
        'resources',
        'caveats',
        'metadata_url',
        'file_url',
        'json_url'
    ]:
        value = details.get(key)
        if value is None:
            continue
        elif isinstance(value, (dict, list)):
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
