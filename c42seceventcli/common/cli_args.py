from argparse import SUPPRESS
from datetime import datetime, timedelta


def add_config_file_path_arg(arg_group):
    arg_group.add_argument(
        "-c",
        "--config-file",
        dest="c42_config_file",
        action="store",
        help="The path to the config file to use for the rest of the arguments.",
    )


def add_clear_cursor_arg(arg_group):
    arg_group.add_argument(
        "--clear-cursor",
        dest="c42_clear_cursor",
        action="store_true",
        help="Resets the stored cursor.",
        default=False,
    )


def add_reset_password_arg(arg_group):
    arg_group.add_argument(
        "--reset-password",
        dest="c42_reset_password",
        action="store_true",
        help="Clears stored password and prompts user for password.",
        default=False,
    )


def add_authority_host_address_arg(arg_group):
    arg_group.add_argument(
        "-s",
        "--server",
        dest="c42_authority_url",
        action="store",
        help="The full scheme, url and port of the Code42 server.",
    )


def add_username_arg(arg_group):
    arg_group.add_argument(
        "-u",
        "--username",
        action="store",
        dest="c42_username",
        help="The username of the Code42 API user.",
    )


def add_begin_date_arg(arg_group):
    arg_group.add_argument(
        "-b",
        "--begin",
        action="store",
        dest="c42_begin_date",
        help="The end of the date range in which to look for events, "
        "in YYYY-MM-DD UTC format OR a number (number of minutes ago).",
    )


def add_end_date_arg(arg_group):
    arg_group.add_argument(
        "-e",
        "--end",
        action="store",
        dest="c42_end_date",
        help="The beginning of the date range in which to look for events, "
        "in YYYY-MM-DD UTC format OR a number (number of minutes ago).",
    )


def add_ignore_ssl_errors_arg(arg_group):
    arg_group.add_argument(
        "-i",
        "--ignore-ssl-errors",
        action="store_true",
        dest="c42_ignore_ssl_errors",
        help="Set to ignore ssl errors.",
    )


def add_output_format_arg(arg_group):
    arg_group.add_argument(
        "-o",
        "--output-format",
        dest="c42_output_format",
        action="store",
        choices=["CEF", "JSON"],
        help="The format used for outputting events.",
    )


def add_record_cursor_arg(arg_group):
    arg_group.add_argument(
        "-r",
        "--record-cursor",
        dest="c42_record_cursor",
        action="store_true",
        help="To only get events that were not previously retrieved.",
    )


def add_exposure_types_arg(arg_group):
    arg_group.add_argument(
        "-t",
        "--types",
        nargs="*",
        action="store",
        dest="c42_exposure_types",
        choices=[
            u"SharedViaLink",
            u"SharedToDomain",
            u"ApplicationRead",
            u"CloudStorage",
            u"RemovableMedia",
            u"IsPublic",
        ],
        help="To limit extracted events to those with given exposure types.",
    )


def add_debug_arg(arg_group):
    arg_group.add_argument(
        "-d" "--debug",
        action="store_true",
        dest="c42_debug_mode",
        help="Set to turn on debug logging.",
    )


def add_destination_type_arg(arg_group):
    arg_group.add_argument(
        "--dest-type",
        action="store",
        dest="c42_destination_type",
        choices=["stdout", "file", "server"],
        help="The type of destination to send output to.",
    )


def add_destination_arg(arg_group):
    arg_group.add_argument(
        "--dest",
        action="store",
        dest="c42_destination",
        help="Either a name of a local file or syslog host address. Ignored if destination type is 'stdout'.",
    )


def add_port_arg(arg_group):
    arg_group.add_argument(
        "--syslog-port",
        action="store",
        dest="c42_destination_port",
        help="Port used when sending logs to server. Ignored if destination type is not 'server'.",
    )


def add_protocol_arg(arg_group):
    arg_group.add_argument(
        "--syslog-protocol",
        action="store",
        dest="c42_destination_protocol",
        choices=["TCP", "UDP"],
        help="Protocol used to send logs to server. Ignored if destination type is not 'server'.",
    )


def add_help_arg(arg_group):
    arg_group.add_argument(
        "-h", "--help", action="help", default=SUPPRESS, help="Show this help message and exit."
    )
