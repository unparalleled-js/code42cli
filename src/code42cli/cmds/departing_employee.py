import click

from code42cli.cmds.detectionlists_shared import update_user, try_handle_user_already_added_error
from code42cli.cmds.detectionlists_shared.options import (
    username_arg,
    cloud_alias_option,
    notes_option,
)
from code42cli.bulk import generate_template_cmd_factory, run_bulk_process
from code42cli.file_readers import read_csv_arg, read_flat_file_arg
from code42cli.cmds.shared import get_user_id
from code42cli.options import global_options, OrderedGroup

from py42.exceptions import Py42BadRequestError


@click.group(cls=OrderedGroup)
@global_options
def departing_employee(state):
    """For adding and removing employees from the departing employee detection list."""
    pass


@departing_employee.command()
@username_arg
@click.option("--departure-date", help="The date the employee is departing. Format: yyyy-MM-dd.")
@cloud_alias_option
@notes_option
@global_options
def add(state, username, cloud_alias, departure_date, notes):
    """Add a user to the departing-employee detection list."""
    _add_departing_employee(state.sdk, username, cloud_alias, departure_date, notes)


@departing_employee.command()
@username_arg
@global_options
def remove(state, username):
    """Remove a user from the departing-employee detection list."""
    _remove_departing_employee(state.sdk, username)


@departing_employee.group(cls=OrderedGroup)
@global_options
def bulk(state):
    """Tools for executing bulk commands."""
    pass


DEPARTING_EMPLOYEE_CSV_HEADERS = ["username", "cloud_alias", "departure_date", "notes"]

departing_employee_generate_template = generate_template_cmd_factory(
    csv_columns=DEPARTING_EMPLOYEE_CSV_HEADERS, cmd_name="departing_employee"
)
bulk.add_command(departing_employee_generate_template)


@bulk.command(
    help="Bulk add users to the departing-employee detection list using a csv file with "
    "format: {}".format(",".join(DEPARTING_EMPLOYEE_CSV_HEADERS))
)
@read_csv_arg(headers=DEPARTING_EMPLOYEE_CSV_HEADERS)
@global_options
def add(state, csv_rows):
    row_handler = lambda username, cloud_alias, departure_date, notes: _add_departing_employee(
        state.sdk, username, cloud_alias, departure_date, notes
    )
    run_bulk_process(
        row_handler, csv_rows, progress_label="Adding users to departing employee detection list:"
    )


@bulk.command(
    help="Bulk remove users from the departing-employee detection list using a newline separated "
    "file of usernames."
)
@read_flat_file_arg
@global_options
def remove(state, file_rows):
    row_handler = lambda username: _remove_departing_employee(state.sdk, username)
    run_bulk_process(
        row_handler,
        file_rows,
        progress_label="Removing users from departing employee detection list:",
    )


def _add_departing_employee(sdk, username, cloud_alias, departure_date, notes):
    user_id = get_user_id(sdk, username)
    try:
        sdk.detectionlists.departing_employee.add(user_id, departure_date)
        update_user(sdk, user_id, cloud_alias=cloud_alias, notes=notes)
    except Py42BadRequestError as err:
        try_handle_user_already_added_error(err, username, "departing-employee list")
        raise


def _remove_departing_employee(sdk, username):
    user_id = get_user_id(sdk, username)
    sdk.detectionlists.departing_employee.remove(user_id)