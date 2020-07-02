from pprint import pformat

import click
from c42eventextractor.extractors import FileEventExtractor
from click import echo
from py42.sdk.queries.fileevents.filters import *

import code42cli.errors as errors
from code42cli.cmds.search import logger_factory
from code42cli.cmds.search.cursor_store import FileEventCursorStore
from code42cli.cmds.search.enums import (
    OutputFormat,
    ExposureType as ExposureTypeOptions,
)
from code42cli.cmds.search.extraction import (
    create_handlers,
    create_time_range_filter,
)
from code42cli.cmds.search.options import (
    create_search_options,
    AdvancedQueryAndSavedSearchIncompatible,
    is_in_filter,
    exists_filter,
    output_file_arg,
    server_options,
)
from code42cli.logger import get_main_cli_logger
from code42cli.options import global_options, incompatible_with, OrderedGroup
from code42cli.util import format_to_table, find_format_width

logger = get_main_cli_logger()

search_options = create_search_options("file events")

format_option = click.option(
    "-f",
    "--format",
    type=click.Choice(OutputFormat()),
    default=OutputFormat.JSON,
    help="The format used for outputting file events.",
)
exposure_type_option = click.option(
    "-t",
    "--type",
    multiple=True,
    type=click.Choice(list(ExposureTypeOptions())),
    cls=AdvancedQueryAndSavedSearchIncompatible,
    callback=is_in_filter(ExposureType),
    help="Limits events to those with given exposure types.",
)
username_option = click.option(
    "--c42-username",
    multiple=True,
    callback=is_in_filter(DeviceUsername),
    cls=AdvancedQueryAndSavedSearchIncompatible,
    help="Limits events to endpoint events for these users.",
)
actor_option = click.option(
    "--actor",
    multiple=True,
    callback=is_in_filter(Actor),
    cls=AdvancedQueryAndSavedSearchIncompatible,
    help="Limits events to only those enacted by the cloud service user "
    "of the person who caused the event.",
)
md5_option = click.option(
    "--md5",
    multiple=True,
    callback=is_in_filter(MD5),
    cls=AdvancedQueryAndSavedSearchIncompatible,
    help="Limits events to file events where the file has one of these MD5 hashes.",
)
sha256_option = click.option(
    "--sha256",
    multiple=True,
    callback=is_in_filter(SHA256),
    cls=AdvancedQueryAndSavedSearchIncompatible,
    help="Limits events to file events where the file has one of these SHA256 hashes.",
)
source_option = click.option(
    "--source",
    multiple=True,
    callback=is_in_filter(Source),
    cls=AdvancedQueryAndSavedSearchIncompatible,
    help="Limits events to only those from one of these sources. Example=Gmail.",
)
file_name_option = click.option(
    "--file-name",
    multiple=True,
    callback=is_in_filter(FileName),
    cls=AdvancedQueryAndSavedSearchIncompatible,
    help="Limits events to file events where the file has one of these names.",
)
file_path_option = click.option(
    "--file-path",
    multiple=True,
    callback=is_in_filter(FilePath),
    cls=AdvancedQueryAndSavedSearchIncompatible,
    help="Limits events to file events where the file is located at one of these paths.",
)
process_owner_option = click.option(
    "--process-owner",
    multiple=True,
    callback=is_in_filter(ProcessOwner),
    cls=AdvancedQueryAndSavedSearchIncompatible,
    help="Limits events to exposure events where one of these users owns "
    "the process behind the exposure.",
)
tab_url_option = click.option(
    "--tab-url",
    multiple=True,
    callback=is_in_filter(TabURL),
    cls=AdvancedQueryAndSavedSearchIncompatible,
    help="Limits events to be exposure events with one of these destination tab URLs.",
)
include_non_exposure_option = click.option(
    "--include-non-exposure",
    is_flag=True,
    callback=exists_filter(ExposureType),
    cls=incompatible_with(["advanced_query", "type"]),
    help="Get all events including non-exposure events.",
)


def _get_saved_search_query(ctx, arg):
    if arg is None:
        return
    query = ctx.obj.sdk.securitydata.savedsearches.get_query(arg)
    return query


saved_search_option = click.option(
    "--saved-search",
    help="Get events from a saved search filter with the given ID",
    callback=_get_saved_search_query,
)


def file_event_options(f):
    f = exposure_type_option(f)
    f = username_option(f)
    f = actor_option(f)
    f = md5_option(f)
    f = sha256_option(f)
    f = source_option(f)
    f = file_name_option(f)
    f = file_path_option(f)
    f = process_owner_option(f)
    f = tab_url_option(f)
    f = include_non_exposure_option(f)
    f = format_option(f)
    f = saved_search_option(f)
    return f


@click.group(cls=OrderedGroup)
@global_options
def security_data(state):
    """Tools for getting security related data, such as file events."""
    # store cursor class on the group state so shared --begin option can use it in validation
    state.cursor_class = FileEventCursorStore


@security_data.command()
@click.argument("checkpoint-name")
@global_options
def clear_checkpoint(state, checkpoint_name):
    """Remove the saved file event checkpoint from '--use-checkpoint/-c' mode."""
    FileEventCursorStore(state.profile.name).delete(checkpoint_name)


@security_data.command("print")
@file_event_options
@search_options
@global_options
def _print(state, format, begin, end, advanced_query, use_checkpoint, **kwargs):
    """Print file events to stdout."""
    output_logger = logger_factory.get_logger_for_stdout(format)
    cursor = FileEventCursorStore(state.profile.name) if use_checkpoint else None
    _extract(
        sdk=state.sdk,
        cursor=cursor,
        checkpoint_name=use_checkpoint,
        filter_list=state.search_filters,
        begin=begin,
        end=end,
        advanced_query=advanced_query,
        output_logger=output_logger,
    )


@security_data.command()
@output_file_arg
@file_event_options
@search_options
@global_options
def write_to(state, format, output_file, begin, end, advanced_query, use_checkpoint, **kwargs):
    """Write file events to the file with the given name."""
    output_logger = logger_factory.get_logger_for_file(output_file, format)
    cursor = FileEventCursorStore(state.profile.name) if use_checkpoint else None
    _extract(
        sdk=state.sdk,
        cursor=cursor,
        checkpoint_name=use_checkpoint,
        filter_list=state.search_filters,
        begin=begin,
        end=end,
        advanced_query=advanced_query,
        output_logger=output_logger,
    )


@security_data.command()
@server_options
@file_event_options
@search_options
@global_options
def send_to(
    state, format, hostname, protocol, begin, end, advanced_query, use_checkpoint, **kwargs
):
    """Send file events to the given server address."""
    output_logger = logger_factory.get_logger_for_server(hostname, protocol, format)
    cursor = FileEventCursorStore(state.profile.name) if use_checkpoint else None
    _extract(
        sdk=state.sdk,
        cursor=cursor,
        checkpoint_name=use_checkpoint,
        filter_list=state.search_filters,
        begin=begin,
        end=end,
        advanced_query=advanced_query,
        output_logger=output_logger,
    )


@security_data.group(cls=OrderedGroup)
@global_options
def saved_search(state):
    pass


@saved_search.command("list")
@global_options
def _list(state):
    """List available saved searches."""
    response = state.sdk.securitydata.savedsearches.get()
    header = {"name": "Name", "id": "Id"}
    format_to_table(*find_format_width(response["searches"], header))


@saved_search.command()
@click.argument("search-id")
@global_options
def show(state, search_id):
    """Get the details of a saved search."""
    response = state.sdk.securitydata.savedsearches.get_by_id(search_id)
    echo(pformat(response["searches"]))


def _extract(sdk, cursor, checkpoint_name, filter_list, begin, end, advanced_query, output_logger):
    handlers = create_handlers(sdk, FileEventExtractor, output_logger, cursor, checkpoint_name)
    extractor = FileEventExtractor(sdk, handlers)
    if advanced_query:
        extractor.extract_advanced(advanced_query)
    else:
        if begin or end:
            filter_list.append(create_time_range_filter(EventTimestamp, begin, end))
        extractor.extract(*filter_list)
    if handlers.TOTAL_EVENTS == 0 and not errors.ERRORED:
        echo("No results found.")
