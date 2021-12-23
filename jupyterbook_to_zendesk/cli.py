"""Console script for jupyterbook_to_zendesk."""
import os
import sys
from pprint import pprint

import click

from jupyterbook_to_zendesk.commands import build_jupyterbook
from jupyterbook_to_zendesk.commands import sync_to_zendesk
from jupyterbook_to_zendesk.logging import logger


@click.group()
@click.pass_context
@click.option("--debug/--no-debug", default=False)
@click.option("-s", "--source_dir", default=".", type=click.Path())
@click.option("-d", "--destination_dir", default="docs", type=click.Path())
@click.option("-c", "--config_file", default="config.cfg", type=click.Path())
def cli(ctx, debug, source_dir, destination_dir, config_file):
    # click.echo(f"Debug mode is {'on' if debug else 'off'}")
    logger.info(f"Source dir is: {source_dir}")
    logger.info(f"Destination dir is: {destination_dir}")
    ctx.ensure_object(dict)
    ctx.obj["debug"] = debug
    ctx.obj["source_dir"] = os.path.abspath(source_dir)
    ctx.obj["destination_dir"] = os.path.abspath(destination_dir)
    if os.path.exists(config_file):
        ctx.obj["config_file"] = os.path.abspath(config_file)
    else:
        ctx.obj["config_file"] = None
    click.echo(pprint(ctx.obj))


@cli.command("build-jb")
@click.pass_context
def command_build(ctx):
    """Console script for jupyterbook_to_zendesk."""
    logger.info("Building the jupyterbook")
    build_jupyterbook.build(ctx)


@cli.command("sync-jb-to-zendesk")  # @cli, not @click!
@click.option("--archive/--no-archive", default=False)
@click.option("--draft/--no-draft", default=True)
@click.option("--public/--no-public", default=True)
@click.pass_context
def command_sync(ctx, archive, draft, public):
    ctx.obj["archive_flag"] = archive
    ctx.obj["draft"] = draft
    ctx.obj["public"] = public
    logger.info("Syncing the Jupyterbook to ZenDesk")
    sync_to_zendesk.sync(ctx)


def main():
    cli()


# if __name__ == "__main__":
#     sys.exit(main())  # pragma: no cover
