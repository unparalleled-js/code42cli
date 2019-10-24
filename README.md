# c42seceventcli - AED

The c42seceventcli AED module contains a CLI tool for extracting AED events as well as an optional state manager 
for recording timestamps. The state manager records timestamps so that on future runs,
you only extract events you did not previously extract.

## Requirements

- Python 2.7.x or 3.5.0+
- Code42 Server 6.8.x+

## Installation
Until we are able to put `py42` and `c42secevents` on PyPI, you will need to first install them manually.

`py42` is available for download [here](https://confluence.corp.code42.com/pages/viewpage.action?pageId=61767969#py42%E2%80%93Code42PythonSDK-Downloads).
For py42 installation instructions, see its [README](https://stash.corp.code42.com/projects/SH/repos/lib_c42_python_sdk/browse/README.md).

`c42secevents` is available [here](https://confluence.corp.code42.com/display/LS/Security+Event+Extractor+-+Python).
For `c42secevents` installation instructions, see its [README](https://stash.corp.code42.com/projects/INT/repos/security-event-extractor/browse/README.md).

Once you've done that, install `c42seceventcli` using:

```bash
$ python setup.py install
```

## Usage

A simple usage requires you to pass in your Code42 authority URL and username as arguments:

```bash
c42aed -s https://example.authority.com -u security.admin@example.com
```
        
Another option is to put your Code42 authority URL and username (and other arguments) in a config file. 
Use `default.config.cfg` as an example to make your own config file; it has all the supported arguments.
The arguments in `default.config.cfg` mirror the CLI arguments.

```buildoutcfg
[Code42]
c42_authority_url=https://example.authority.com
c42_username=user@code42.com
```

Then, run the script as follows:

```bash
c42aed -c path/to/config
```

To use the state management service, simply provide the `-r` to the command line.
`-r` is particularly useful if you wish to run this script on a recurring job:

```bash
c42aed -s https://example.authority.com -u security.admin@example.com -r
```

If you are using a config file with `-c`, set `record_cursor` to True:

```buildoutcfg
[Code42]
c42_authority_url=https://example.authority.com
c42_username=user@code42.com
record_cursor=True
```
By excluding `-r`, future runs will not know about previous events you got, and 
you will get all the events in the given time range (or default time range of 60 days back). 

To clear the cursor:

```bash
c42aed -s https://example.authority.com -u security.admin@example.com -r --clear-cursor
```
There are two possible output formats.

* CEF
* JSON

JSON is the default. To use CEF, use `-o CEF`:

```bash
c42aed -s https://example.authority.com -u security.admin@example.com -o CEF
```

Or if you are using a config file with `-c`:

```buildoutcfg
[Code42]
c42_authority_url=https://example.authority.com
c42_username=user@code42.com
output_format=CEF
```

There are three possible destination types to use:

* stdout 
* file - writing to a file
* server - transmitting to a server, such as syslog

The program defaults to `stdout`. To use a file, use `--dest-type` and `--dest` this way:

```bash
c42aed -s https://example.authority.com -u security.admin@example.com --dest-type file --dest name-of-file.txt
```

To use a server destination (like syslog):

```bash
c42aed -s https://example.authority.com -u security.admin@example.com --dest-type server --dest https://syslog.example.com
```

Both `destination_type` and `destination` are possible fields in the config file as well.

You can also use CLI arguments with config file arguments, but the program will favor the CLI arguments.

If this is your first time running, you will be prompted for your Code42 password.

If you get a keychain error when running this script, you may have to add a code signature:

```bash
codesign -f -s - $(which python)
```

All errors are sent to an error log file named `c42seceventcli_aed_errors.log` 
located in your user directory under `.c42seceventcli/log`.

Full usage:

```
usage: c42aed [-h] [--clear-cursor] [--reset-password] [-c CONFIG_FILE]
              [-s C42_AUTHORITY_URL] [-u C42_USERNAME] [-b BEGIN_DATE] [-i]
              [-o {CEF,JSON}]
              [-t [{SharedViaLink,SharedToDomain,ApplicationRead,CloudStorage,RemovableMedia,IsPublic} [{SharedViaLink,SharedToDomain,ApplicationRead,CloudStorage,RemovableMedia,IsPublic} ...]]]
              [-d--debug] [--dest-type {stdout,file,server}]
              [--dest DESTINATION] [--dest-port DESTINATION_PORT]
              [--dest-protocol {TCP,UDP}] [-e END_DATE | -r]

optional arguments:
  -h, --help            show this help message and exit
  --clear-cursor        Resets the stored cursor.
  --reset-password      Clears stored password and prompts user for password.
  -c CONFIG_FILE, --config-file CONFIG_FILE
                        The path to the config file to use for the rest of the
                        arguments.
  -s C42_AUTHORITY_URL, --server C42_AUTHORITY_URL
                        The full scheme, url and port of the Code42 server.
  -u C42_USERNAME, --username C42_USERNAME
                        The username of the Code42 API user.
  -b BEGIN_DATE, --begin BEGIN_DATE
                        The beginning of the date range in which to look for
                        events, in YYYY-MM-DD UTC format OR a number (number
                        of minutes ago).
  -i, --ignore-ssl-errors
                        Do not validate the SSL certificates of Code42
                        servers.
  -o {CEF,JSON}, --output-format {CEF,JSON}
                        The format used for outputting events.
  -t [{SharedViaLink,SharedToDomain,ApplicationRead,CloudStorage,RemovableMedia,IsPublic} [{SharedViaLink,SharedToDomain,ApplicationRead,CloudStorage,RemovableMedia,IsPublic} ...]], --types [{SharedViaLink,SharedToDomain,ApplicationRead,CloudStorage,RemovableMedia,IsPublic} [{SharedViaLink,SharedToDomain,ApplicationRead,CloudStorage,RemovableMedia,IsPublic} ...]]
                        To limit extracted events to those with given exposure
                        types.
  -d--debug             Turn on debug logging.
  --dest-type {stdout,file,server}
                        The type of destination to send output to.
  --dest DESTINATION    Either a name of a local file or syslog host address.
                        Ignored if destination type is 'stdout'.
  --dest-port DESTINATION_PORT
                        Port used when sending logs to server. Ignored if
                        destination type is not 'server'.
  --dest-protocol {TCP,UDP}
                        Protocol used to send logs to server. Ignored if
                        destination type is not 'server'.
  -e END_DATE, --end END_DATE
                        The end of the date range in which to look for events,
                        in YYYY-MM-DD UTC format OR a number (number of
                        minutes ago).
  -r, --record-cursor   Only get events that were not previously retrieved.
```

# Known Issues

Only the first 10,000 of each set of events containing the exact same insertion timestamp is reported.