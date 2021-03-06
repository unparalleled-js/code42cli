import json
import logging

import py42.sdk.queries.fileevents.filters as f
import pytest
from c42eventextractor.extractors import FileEventExtractor
from py42.sdk.queries.fileevents.file_event_query import FileEventQuery
from tests.cmds.conftest import filter_term_is_in_call_args
from tests.cmds.conftest import get_filter_value_from_json
from tests.conftest import get_test_date_str

from code42cli import errors
from code42cli import PRODUCT_NAME
from code42cli.cmds.search.cursor_store import FileEventCursorStore
from code42cli.main import cli


BEGIN_TIMESTAMP = 1577858400.0
END_TIMESTAMP = 1580450400.0
CURSOR_TIMESTAMP = 1579500000.0


TEST_LIST_RESPONSE = {
    "searches": [
        {
            "id": "a083f08d-8f33-4cbd-81c4-8d1820b61185",
            "name": "test-events",
            "notes": "py42 is here",
        },
    ]
}

TEST_EMPTY_LIST_RESPONSE = {"searches": []}


@pytest.fixture
def file_event_extractor(mocker):
    mock = mocker.patch(
        "{}.cmds.securitydata._get_file_event_extractor".format(PRODUCT_NAME)
    )
    mock.return_value = mocker.MagicMock(spec=FileEventExtractor)
    return mock.return_value


@pytest.fixture
def file_event_cursor_with_checkpoint(mocker):
    mock = mocker.patch(
        "{}.cmds.securitydata._get_file_event_cursor_store".format(PRODUCT_NAME)
    )
    mock_cursor = mocker.MagicMock(spec=FileEventCursorStore)
    mock_cursor.get.return_value = CURSOR_TIMESTAMP
    mock.return_value = mock_cursor
    mock.expected_timestamp = "2020-01-20T06:00:00+00:00"
    return mock


@pytest.fixture
def file_event_cursor_without_checkpoint(mocker):
    mock = mocker.patch(
        "{}.cmds.securitydata._get_file_event_cursor_store".format(PRODUCT_NAME)
    )
    mock_cursor = mocker.MagicMock(spec=FileEventCursorStore)
    mock_cursor.get.return_value = None
    mock.return_value = mock_cursor
    return mock


@pytest.fixture
def begin_option(mocker):
    mock = mocker.patch(
        "{}.cmds.search.options.parse_min_timestamp".format(PRODUCT_NAME)
    )
    mock.return_value = BEGIN_TIMESTAMP
    mock.expected_timestamp = "2020-01-01T06:00:00.000Z"
    return mock


ADVANCED_QUERY_JSON = '{"some": "complex json"}'


@pytest.mark.parametrize(
    "command",
    (
        ["security-data", "search", "--advanced-query", ADVANCED_QUERY_JSON],
        [
            "security-data",
            "send-to",
            "0.0.0.0",
            "--advanced-query",
            ADVANCED_QUERY_JSON,
        ],
    ),
)
def test_search_when_is_advanced_query_uses_only_the_extract_advanced_method(
    runner, cli_state, file_event_extractor, command
):
    runner.invoke(cli, command, obj=cli_state)
    file_event_extractor.extract_advanced.assert_called_once_with(
        '{"some": "complex json"}'
    )
    assert file_event_extractor.extract.call_count == 0
    assert file_event_extractor.extract_advanced.call_count == 1


@pytest.mark.parametrize(
    "command",
    (
        ["security-data", "search", "--begin", "1d"],
        ["security-data", "send-to", "0.0.0.0", "--begin", "1d"],
    ),
)
def test_search_when_is_not_advanced_query_uses_only_the_extract_advanced_method(
    runner, cli_state, file_event_extractor, command
):
    runner.invoke(cli, command, obj=cli_state)
    assert file_event_extractor.extract_advanced.call_count == 0
    assert file_event_extractor.extract.call_count == 1


@pytest.mark.parametrize(
    "arg",
    [
        ("--begin", "1d"),
        ("--end", "1d"),
        ("--c42-username", "test@code42.com"),
        ("--actor", "test.testerson"),
        ("--md5", "abcd1234"),
        ("--sha256", "abcdefg12345678"),
        ("--source", "Gmail"),
        ("--file-name", "test.txt"),
        ("--file-path", "C:\\Program Files"),
        ("--file-category", "IMAGE"),
        ("--process-owner", "root"),
        ("--tab-url", "https://example.com"),
        ("--type", "SharedViaLink"),
        ("--include-non-exposure",),
        ("--use-checkpoint", "test"),
    ],
)
def test_search_with_advanced_query_and_incompatible_argument_errors(
    runner, arg, cli_state
):
    result = runner.invoke(
        cli,
        ["security-data", "search", "--advanced-query", ADVANCED_QUERY_JSON, *arg],
        obj=cli_state,
    )
    assert result.exit_code == 2
    assert "{} can't be used with: --advanced-query".format(arg[0]) in result.output


@pytest.mark.parametrize(
    "arg",
    [
        ("--begin", "1d"),
        ("--end", "1d"),
        ("--c42-username", "test@code42.com"),
        ("--actor", "test.testerson"),
        ("--md5", "abcd1234"),
        ("--sha256", "abcdefg12345678"),
        ("--source", "Gmail"),
        ("--file-name", "test.txt"),
        ("--file-path", "C:\\Program Files"),
        ("--file-category", "IMAGE"),
        ("--process-owner", "root"),
        ("--tab-url", "https://example.com"),
        ("--type", "SharedViaLink"),
        ("--include-non-exposure",),
        ("--use-checkpoint", "test"),
    ],
)
def test_search_with_saved_search_and_incompatible_argument_errors(
    runner, arg, cli_state
):
    result = runner.invoke(
        cli,
        ["security-data", "search", "--saved-search", "test_id", *arg],
        obj=cli_state,
    )
    assert result.exit_code == 2
    assert "{} can't be used with: --saved-search".format(arg[0]) in result.output


@pytest.mark.parametrize(
    "command",
    (
        [
            "security-data",
            "search",
            "--begin",
            get_test_date_str(days_ago=89),
            "--end",
            get_test_date_str(days_ago=1),
        ],
        [
            "security-data",
            "send-to",
            "0.0.0.0",
            "--begin",
            get_test_date_str(days_ago=89),
            "--end",
            get_test_date_str(days_ago=1),
        ],
    ),
)
def test_command_when_given_begin_and_end_dates_uses_expected_query(
    runner, cli_state, file_event_extractor, command
):
    begin_date = get_test_date_str(days_ago=89)
    end_date = get_test_date_str(days_ago=1)
    runner.invoke(
        cli, command, obj=cli_state,
    )
    filters = file_event_extractor.extract.call_args[0][1]
    actual_begin = get_filter_value_from_json(filters, filter_index=0)
    expected_begin = "{}T00:00:00.000Z".format(begin_date)
    actual_end = get_filter_value_from_json(filters, filter_index=1)
    expected_end = "{}T23:59:59.999Z".format(end_date)
    assert actual_begin == expected_begin
    assert actual_end == expected_end


def test_search_when_given_begin_and_end_date_and_time_uses_expected_query(
    runner, cli_state, file_event_extractor
):
    begin_date = get_test_date_str(days_ago=89)
    end_date = get_test_date_str(days_ago=1)
    time = "15:33:02"
    runner.invoke(
        cli,
        [
            "security-data",
            "search",
            "--begin",
            "{} {}".format(begin_date, time),
            "--end",
            "{} {}".format(end_date, time),
        ],
        obj=cli_state,
    )
    filters = file_event_extractor.extract.call_args[0][1]
    actual_begin = get_filter_value_from_json(filters, filter_index=0)
    expected_begin = "{}T{}.000Z".format(begin_date, time)
    actual_end = get_filter_value_from_json(filters, filter_index=1)
    expected_end = "{}T{}.000Z".format(end_date, time)
    assert actual_begin == expected_begin
    assert actual_end == expected_end


def test_search_when_given_begin_date_and_time_without_seconds_uses_expected_query(
    runner, cli_state, file_event_extractor
):
    date = get_test_date_str(days_ago=89)
    time = "15:33"
    runner.invoke(
        cli,
        ["security-data", "search", "--begin", "{} {}".format(date, time)],
        obj=cli_state,
    )
    actual = get_filter_value_from_json(
        file_event_extractor.extract.call_args[0][1], filter_index=0
    )
    expected = "{}T{}:00.000Z".format(date, time)
    assert actual == expected


def test_search_when_given_end_date_and_time_uses_expected_query(
    runner, cli_state, file_event_extractor
):
    begin_date = get_test_date_str(days_ago=10)
    end_date = get_test_date_str(days_ago=1)
    time = "15:33"
    runner.invoke(
        cli,
        [
            "security-data",
            "search",
            "--begin",
            begin_date,
            "--end",
            "{} {}".format(end_date, time),
        ],
        obj=cli_state,
    )
    actual = get_filter_value_from_json(
        file_event_extractor.extract.call_args[0][1], filter_index=1
    )
    expected = "{}T{}:00.000Z".format(end_date, time)
    assert actual == expected


@pytest.mark.parametrize(
    "command",
    (
        [
            "security-data",
            "search",
            "--begin",
            get_test_date_str(days_ago=91) + " 12:51:00",
        ],
        [
            "security-data",
            "send-to",
            "0.0.0.0",
            "--begin",
            get_test_date_str(days_ago=91) + " 12:51:00",
        ],
    ),
)
def test_command_when_given_begin_date_more_than_ninety_days_back_errors(
    runner, cli_state, command
):
    result = runner.invoke(cli, command, obj=cli_state)
    assert result.exit_code == 2
    assert "must be within 90 days" in result.output


def test_search_when_given_begin_date_past_90_days_and_use_checkpoint_and_a_stored_cursor_exists_and_not_given_end_date_does_not_use_any_event_timestamp_filter(
    runner, cli_state, file_event_cursor_with_checkpoint, file_event_extractor
):
    begin_date = get_test_date_str(days_ago=91) + " 12:51:00"
    runner.invoke(
        cli,
        ["security-data", "search", "--begin", begin_date, "--use-checkpoint", "test"],
        obj=cli_state,
    )
    assert not filter_term_is_in_call_args(
        file_event_extractor, f.InsertionTimestamp._term
    )


def test_search_when_given_begin_date_and_not_use_checkpoint_and_cursor_exists_uses_begin_date(
    runner, cli_state, file_event_extractor
):
    begin_date = get_test_date_str(days_ago=1)
    runner.invoke(
        cli, ["security-data", "search", "--begin", begin_date], obj=cli_state
    )
    actual_ts = get_filter_value_from_json(
        file_event_extractor.extract.call_args[0][1], filter_index=0
    )
    expected_ts = "{}T00:00:00.000Z".format(begin_date)
    assert actual_ts == expected_ts
    assert filter_term_is_in_call_args(file_event_extractor, f.EventTimestamp._term)


def test_search_when_end_date_is_before_begin_date_causes_exit(runner, cli_state):
    begin_date = get_test_date_str(days_ago=1)
    end_date = get_test_date_str(days_ago=3)
    result = runner.invoke(
        cli,
        ["security-data", "search", "--begin", begin_date, "--end", end_date],
        obj=cli_state,
    )
    assert result.exit_code == 2
    assert "'--begin': cannot be after --end date" in result.output


def test_search_with_only_begin_calls_extract_with_expected_args(
    runner, cli_state, file_event_extractor, begin_option
):
    result = runner.invoke(
        cli, ["security-data", "search", "--begin", "1h"], obj=cli_state
    )
    assert result.exit_code == 0
    assert str(
        file_event_extractor.extract.call_args[0][1]
    ) == '{{"filterClause":"AND", "filters":[{{"operator":"ON_OR_AFTER", "term":"eventTimestamp", "value":"{}"}}]}}'.format(
        begin_option.expected_timestamp
    )


def test_search_with_use_checkpoint_and_without_begin_and_without_checkpoint_causes_expected_error(
    runner, cli_state, file_event_cursor_without_checkpoint
):
    result = runner.invoke(
        cli, ["security-data", "search", "--use-checkpoint", "test"], obj=cli_state
    )
    assert result.exit_code == 2
    assert (
        "--begin date is required for --use-checkpoint when no checkpoint exists yet."
        in result.output
    )


@pytest.mark.parametrize(
    "command",
    (
        ["security-data", "search", "--use-checkpoint", "test", "--begin", "1h"],
        [
            "security-data",
            "send-to",
            "0.0.0.0",
            "--use-checkpoint",
            "test",
            "--begin",
            "1h",
        ],
    ),
)
def test_command_with_use_checkpoint_and_with_begin_and_without_checkpoint_calls_extract_with_begin_date(
    runner,
    cli_state,
    file_event_extractor,
    begin_option,
    file_event_cursor_without_checkpoint,
    command,
):
    result = runner.invoke(cli, command, obj=cli_state,)
    assert result.exit_code == 0
    assert len(file_event_extractor.extract.call_args[0]) == 2
    assert begin_option.expected_timestamp in str(
        file_event_extractor.extract.call_args[0][1]
    )


@pytest.mark.parametrize(
    "command",
    (
        ["security-data", "search", "--use-checkpoint", "test", "--begin", "1h"],
        [
            "security-data",
            "send-to",
            "0.0.0.0",
            "--use-checkpoint",
            "test",
            "--begin",
            "1h",
        ],
    ),
)
def test_command_with_use_checkpoint_and_with_begin_and_with_stored_checkpoint_calls_extract_with_checkpoint_and_ignores_begin_arg(
    runner, cli_state, file_event_extractor, file_event_cursor_with_checkpoint, command,
):
    result = runner.invoke(cli, command, obj=cli_state,)
    assert result.exit_code == 0
    assert len(file_event_extractor.extract.call_args[0]) == 1
    assert (
        "checkpoint of {} exists".format(
            file_event_cursor_with_checkpoint.expected_timestamp
        )
        in result.output
    )


@pytest.mark.parametrize(
    "command",
    (
        ["security-data", "search", "--begin", "1d", "-t", "NotValid"],
        ["security-data", "send-to", "0.0.0.0", "--begin", "1d", "-t", "NotValid"],
    ),
)
def test_command_when_given_invalid_exposure_type_causes_exit(
    runner, cli_state, command
):
    result = runner.invoke(cli, command, obj=cli_state,)
    assert result.exit_code == 2
    assert "invalid choice: NotValid" in result.output


@pytest.mark.parametrize(
    "command",
    (
        ["security-data", "search", "--begin", "1h", "--c42-username"],
        ["security-data", "send-to", "0.0.0.0", "--begin", "1h", "--c42-username"],
    ),
)
def test_command_when_given_username_uses_username_filter(
    runner, cli_state, file_event_extractor, command
):
    c42_username = "test@code42.com"
    command.append(c42_username)
    runner.invoke(
        cli, command, obj=cli_state,
    )
    filter_strings = [str(arg) for arg in file_event_extractor.extract.call_args[0]]
    assert str(f.DeviceUsername.is_in([c42_username])) in filter_strings


@pytest.mark.parametrize(
    "command",
    (
        ["security-data", "search", "--begin", "1h", "--actor"],
        ["security-data", "send-to", "0.0.0.0", "--begin", "1h", "--actor"],
    ),
)
def test_command_when_given_actor_is_uses_username_filter(
    runner, cli_state, file_event_extractor, command
):
    actor_name = "test.testerson"
    command.append(actor_name)
    runner.invoke(
        cli, command, obj=cli_state,
    )
    filter_strings = [str(arg) for arg in file_event_extractor.extract.call_args[0]]
    assert str(f.Actor.is_in([actor_name])) in filter_strings


@pytest.mark.parametrize(
    "command",
    (
        ["security-data", "search", "--begin", "1h", "--md5"],
        ["security-data", "send-to", "0.0.0.0", "--begin", "1h", "--md5"],
    ),
)
def test_command_when_given_md5_uses_md5_filter(
    runner, cli_state, file_event_extractor, command
):
    md5 = "abcd12345"
    command.append(md5)
    runner.invoke(cli, command, obj=cli_state)
    filter_strings = [str(arg) for arg in file_event_extractor.extract.call_args[0]]
    assert str(f.MD5.is_in([md5])) in filter_strings


@pytest.mark.parametrize(
    "command",
    (
        ["security-data", "search", "--begin", "1h", "--sha256"],
        ["security-data", "send-to", "0.0.0.0", "--begin", "1h", "--sha256"],
    ),
)
def test_command_when_given_sha256_uses_sha256_filter(
    runner, cli_state, file_event_extractor, command
):
    sha_256 = "abcd12345"
    command.append(sha_256)
    runner.invoke(
        cli, command, obj=cli_state,
    )
    filter_strings = [str(arg) for arg in file_event_extractor.extract.call_args[0]]
    assert str(f.SHA256.is_in([sha_256])) in filter_strings


@pytest.mark.parametrize(
    "command",
    (
        ["security-data", "search", "--begin", "1h", "--source"],
        ["security-data", "send-to", "0.0.0.0", "--begin", "1h", "--source"],
    ),
)
def test_command_when_given_source_uses_source_filter(
    runner, cli_state, file_event_extractor, command
):
    source = "Gmail"
    command.append(source)
    runner.invoke(cli, command, obj=cli_state)
    filter_strings = [str(arg) for arg in file_event_extractor.extract.call_args[0]]
    assert str(f.Source.is_in([source])) in filter_strings


@pytest.mark.parametrize(
    "command",
    (
        ["security-data", "search", "--begin", "1h", "--file-name"],
        ["security-data", "send-to", "0.0.0.0", "--begin", "1h", "--file-name"],
    ),
)
def test_command_when_given_file_name_uses_file_name_filter(
    runner, cli_state, file_event_extractor, command
):
    filename = "test.txt"
    command.append(filename)
    runner.invoke(
        cli, command, obj=cli_state,
    )
    filter_strings = [str(arg) for arg in file_event_extractor.extract.call_args[0]]
    assert str(f.FileName.is_in([filename])) in filter_strings


@pytest.mark.parametrize(
    "command",
    (
        ["security-data", "search", "--begin", "1h", "--file-path"],
        ["security-data", "send-to", "0.0.0.0", "--begin", "1h", "--file-path"],
    ),
)
def test_command_when_given_file_path_uses_file_path_filter(
    runner, cli_state, file_event_extractor, command
):
    filepath = "C:\\Program Files"
    command.append(filepath)
    runner.invoke(
        cli, command, obj=cli_state,
    )
    filter_strings = [str(arg) for arg in file_event_extractor.extract.call_args[0]]
    assert str(f.FilePath.is_in([filepath])) in filter_strings


def test_search_when_given_file_category_uses_file_category_filter(
    runner, cli_state, file_event_extractor
):
    file_category = "IMAGE"
    runner.invoke(
        cli,
        ["security-data", "search", "--begin", "1h", "--file-category", file_category],
        obj=cli_state,
    )
    filter_strings = [str(arg) for arg in file_event_extractor.extract.call_args[0]]
    assert str(f.FileCategory.is_in([file_category])) in filter_strings


@pytest.mark.parametrize(
    "command",
    (
        ["security-data", "search", "--begin", "1h", "--process-owner"],
        ["security-data", "send-to", "0.0.0.0", "--begin", "1h", "--process-owner"],
    ),
)
def test_when_given_process_owner_uses_process_owner_filter(
    runner, cli_state, file_event_extractor, command
):
    process_owner = "root"
    command.append(process_owner)
    runner.invoke(
        cli, command, obj=cli_state,
    )
    filter_strings = [str(arg) for arg in file_event_extractor.extract.call_args[0]]
    assert str(f.ProcessOwner.is_in([process_owner])) in filter_strings


@pytest.mark.parametrize(
    "command",
    (
        ["security-data", "search", "--begin", "1h", "--tab-url"],
        ["security-data", "send-to", "0.0.0.0", "--begin", "1h", "--tab-url"],
    ),
)
def test_when_given_tab_url_uses_process_tab_url_filter(
    runner, cli_state, file_event_extractor, command
):
    tab_url = "https://example.com"
    command.append(tab_url)
    runner.invoke(
        cli, command, obj=cli_state,
    )
    filter_strings = [str(arg) for arg in file_event_extractor.extract.call_args[0]]
    assert str(f.TabURL.is_in([tab_url])) in filter_strings


@pytest.mark.parametrize(
    "command",
    (
        ["security-data", "search", "--begin", "1h", "--type"],
        ["security-data", "send-to", "0.0.0.0", "--begin", "1h", "--type"],
    ),
)
def test_when_given_exposure_types_uses_exposure_type_is_in_filter(
    runner, cli_state, file_event_extractor, command
):
    exposure_type = "SharedViaLink"
    command.append(exposure_type)
    runner.invoke(
        cli, command, obj=cli_state,
    )
    filter_strings = [str(arg) for arg in file_event_extractor.extract.call_args[0]]
    assert str(f.ExposureType.is_in([exposure_type])) in filter_strings


@pytest.mark.parametrize(
    "command",
    (
        ["security-data", "search", "--begin", "1h", "--include-non-exposure"],
        [
            "security-data",
            "send-to",
            "0.0.0.0",
            "--begin",
            "1h",
            "--include-non-exposure",
        ],
    ),
)
def test_when_given_include_non_exposure_does_not_include_exposure_type_exists(
    runner, cli_state, file_event_extractor, command
):
    runner.invoke(
        cli, command, obj=cli_state,
    )
    filter_strings = [str(arg) for arg in file_event_extractor.extract.call_args[0]]
    assert str(f.ExposureType.exists()) not in filter_strings


@pytest.mark.parametrize(
    "command",
    (
        ["security-data", "search", "--begin", "1h"],
        ["security-data", "send-to", "0.0.0.0", "--begin", "1h"],
    ),
)
def test_when_not_given_include_non_exposure_includes_exposure_type_exists(
    runner, cli_state, file_event_extractor, command
):
    runner.invoke(
        cli, command, obj=cli_state,
    )
    filter_strings = [str(arg) for arg in file_event_extractor.extract.call_args[0]]
    assert str(f.ExposureType.exists()) in filter_strings


def test_when_given_multiple_search_args_uses_expected_filters(
    runner, cli_state, file_event_extractor
):
    process_owner = "root"
    c42_username = "test@code42.com"
    filename = "test.txt"
    runner.invoke(
        cli,
        [
            "security-data",
            "search",
            "--begin",
            "1h",
            "--process-owner",
            process_owner,
            "--c42-username",
            c42_username,
            "--file-name",
            filename,
        ],
        obj=cli_state,
    )
    filter_strings = [str(arg) for arg in file_event_extractor.extract.call_args[0]]
    assert str(f.ProcessOwner.is_in([process_owner])) in filter_strings
    assert str(f.FileName.is_in([filename])) in filter_strings
    assert str(f.DeviceUsername.is_in([c42_username])) in filter_strings


def test_when_given_include_non_exposure_and_exposure_types_causes_exit(
    runner, cli_state, file_event_extractor
):
    result = runner.invoke(
        cli,
        [
            "security-data",
            "search",
            "--begin",
            "1h",
            "--include-non-exposure",
            "--type",
            "SharedViaLink",
        ],
        obj=cli_state,
    )
    assert result.exit_code == 2


def test_when_extraction_handles_error_expected_message_logged_and_printed_and_global_errored_flag_set(
    runner, cli_state, caplog
):
    errors.ERRORED = False
    exception_msg = "Test Exception"

    def file_search_error(x):
        raise Exception(exception_msg)

    cli_state.sdk.securitydata.search_file_events.side_effect = file_search_error
    with caplog.at_level(logging.ERROR):
        result = runner.invoke(
            cli, ["security-data", "search", "--begin", "1d"], obj=cli_state
        )
        assert exception_msg in result.output
        assert exception_msg in caplog.text
        assert errors.ERRORED


def test_saved_search_calls_extractor_extract_and_saved_search_execute(
    runner, cli_state, file_event_extractor
):
    search_query = {
        "groupClause": "AND",
        "groups": [
            {
                "filterClause": "AND",
                "filters": [
                    {
                        "operator": "ON_OR_AFTER",
                        "term": "eventTimestamp",
                        "value": "2020-05-01T00:00:00.000Z",
                    }
                ],
            },
            {
                "filterClause": "OR",
                "filters": [
                    {"operator": "IS", "term": "eventType", "value": "DELETED"},
                    {"operator": "IS", "term": "eventType", "value": "EMAILED"},
                    {"operator": "IS", "term": "eventType", "value": "MODIFIED"},
                    {"operator": "IS", "term": "eventType", "value": "READ_BY_AP"},
                    {"operator": "IS", "term": "eventType", "value": "CREATED"},
                ],
            },
        ],
        "pgNum": 1,
        "pgSize": 10000,
        "srtDir": "asc",
        "srtKey": "eventId",
    }
    query = FileEventQuery.from_dict(search_query)
    cli_state.sdk.securitydata.savedsearches.get_query.return_value = query
    runner.invoke(
        cli, ["security-data", "search", "--saved-search", "test_id"], obj=cli_state
    )
    assert file_event_extractor.extract.call_count == 1
    assert str(file_event_extractor.extract.call_args[0][0]) in str(query)
    assert str(file_event_extractor.extract.call_args[0][1]) in str(query)


def test_saved_search_list_calls_get_method(runner, cli_state):
    runner.invoke(cli, ["security-data", "saved-search", "list"], obj=cli_state)
    assert cli_state.sdk.securitydata.savedsearches.get.call_count == 1


def test_show_detail_calls_get_by_id_method(runner, cli_state):
    test_id = "test_id"
    runner.invoke(
        cli, ["security-data", "saved-search", "show", test_id], obj=cli_state
    )
    cli_state.sdk.securitydata.savedsearches.get_by_id.assert_called_once_with(test_id)


def test_search_with_or_query_flag_produces_expected_query(runner, cli_state):
    begin_date = get_test_date_str(days_ago=10)
    test_username = "test@example.com"
    test_filename = "test.txt"
    runner.invoke(
        cli,
        [
            "security-data",
            "search",
            "--or-query",
            "--begin",
            begin_date,
            "--c42-username",
            test_username,
            "--file-name",
            test_filename,
        ],
        obj=cli_state,
    )
    expected_query = {
        "groupClause": "AND",
        "groups": [
            {
                "filterClause": "AND",
                "filters": [
                    {"operator": "EXISTS", "term": "exposure", "value": None},
                    {
                        "operator": "ON_OR_AFTER",
                        "term": "eventTimestamp",
                        "value": "{}T00:00:00.000Z".format(begin_date),
                    },
                ],
            },
            {
                "filterClause": "OR",
                "filters": [
                    {
                        "operator": "IS",
                        "term": "deviceUserName",
                        "value": "test@example.com",
                    },
                    {"operator": "IS", "term": "fileName", "value": "test.txt"},
                ],
            },
        ],
        "pgNum": 1,
        "pgSize": 10000,
        "srtDir": "asc",
        "srtKey": "insertionTimestamp",
    }
    actual_query = json.loads(
        str(cli_state.sdk.securitydata.search_file_events.call_args[0][0])
    )
    assert actual_query == expected_query


def test_saved_search_list_with_format_option_returns_csv_formatted_response(
    runner, cli_state
):
    cli_state.sdk.securitydata.savedsearches.get.return_value = TEST_LIST_RESPONSE
    result = runner.invoke(
        cli, ["security-data", "saved-search", "list", "-f", "CSV"], obj=cli_state
    )
    assert "id" in result.output
    assert "name" in result.output
    assert "notes" in result.output

    assert "083f08d-8f33-4cbd-81c4-8d1820b61185" in result.output
    assert "test-events" in result.output
    assert "py42 is here" in result.output


def test_saved_search_list_with_format_option_does_not_return_when_response_is_empty(
    runner, cli_state
):
    cli_state.sdk.securitydata.savedsearches.get.return_value = TEST_EMPTY_LIST_RESPONSE
    result = runner.invoke(
        cli, ["security-data", "saved-search", "list", "-f", "csv"], obj=cli_state
    )
    assert "Name,Id" not in result.output


def test_send_to_when_is_advanced_query_uses_only_the_extract_advanced_method(
    runner, cli_state, file_event_extractor, event_extractor_logger
):
    runner.invoke(
        cli,
        [
            "security-data",
            "send-to",
            "localhost",
            "--advanced-query",
            ADVANCED_QUERY_JSON,
        ],
        obj=cli_state,
    )
    file_event_extractor.extract_advanced.assert_called_once_with(
        '{"some": "complex json"}'
    )
    assert file_event_extractor.extract.call_count == 0
    assert file_event_extractor.extract_advanced.call_count == 1


def test_send_to_when_is_not_advanced_query_uses_only_the_extract_advanced_method(
    runner, cli_state, file_event_extractor
):
    runner.invoke(
        cli, ["security-data", "send-to", "localhost", "--begin", "1d"], obj=cli_state
    )
    assert file_event_extractor.extract_advanced.call_count == 0
    assert file_event_extractor.extract.call_count == 1
