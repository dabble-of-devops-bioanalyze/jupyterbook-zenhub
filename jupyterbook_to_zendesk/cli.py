"""Console script for jupyterbook_to_zendesk."""
import sys
import click
import os
from pprint import pprint

import sys
import os

from .commands import build_jupyterbook, sync_to_zendesk


@click.group()
@click.pass_context
@click.option("--debug/--no-debug", default=False)
@click.option("-s", "--source_dir", default=".", type=click.Path())
@click.option("-d", "--destination_dir", default="docs", type=click.Path())
def cli(ctx, debug, source_dir, destination_dir):
    click.echo(f"Debug mode is {'on' if debug else 'off'}")
    click.echo(f"Source dir is: {source_dir}")
    click.echo(f"Destination dir is: {destination_dir}")
    ctx.ensure_object(dict)
    ctx.obj["debug"] = debug
    ctx.obj["source_dir"] = os.path.abspath(source_dir)
    ctx.obj["destination_dir"] = os.path.abspath(destination_dir)
    click.echo(pprint(ctx.obj))


@cli.command('build-jb')
@click.pass_context
def command_build(ctx):
    """Console script for jupyterbook_to_zendesk."""
    click.echo("Building the jupyterbook")
    click.echo(ctx)
    build_jupyterbook.build(ctx)


@cli.command('sync-jb-to-zendesk')  # @cli, not @click!
@click.pass_context
def command_sync(ctx):
    sync_to_zendesk.sync()
    click.echo("Syncing")


def main():
    cli()


# if __name__ == "__main__":
#     sys.exit(main())  # pragma: no cover
