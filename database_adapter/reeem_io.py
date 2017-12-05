"""Open a database connection to reeem_db"""

__copyright__ = "© Reiner Lemoine Institut"
__license__ = "GNU Affero General Public License Version 3 (AGPL-3.0)"
__license_url__ = "https://www.gnu.org/licenses/agpl-3.0.en.html"
__author__ = "Ludwig Hülk"
__version__ = "v0.1.2"

import sys
import os
import getpass
import logging
from sqlalchemy import *
import configparser as cp

# parameter
config_file = 'reeem_io_config.ini'
config_section = 'reeem'
log_file = 'reeem_adapter.log'
sys.tracebacklimit = 0
cfg = cp.RawConfigParser()


def logger():
    """Configure logging in console and log file.
    
    Returns
    -------
    rl : logger
        Logging in console (ch) and file (fh).
    """

    # set root logger (rl)
    rl = logging.getLogger('REEEMLogger')
    rl.setLevel(logging.INFO)
    rl.propagate = False

    # set format
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')

    # console handler (ch)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    rl.addHandler(ch)

    # file handler (fh)
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    rl.addHandler(fh)

    return rl


def config_section_set(key, value):
    """Create a config file.

    Sets input values to a [db_section] key - pair.

    Parameters
    ----------
    key : str
        The username.
    value : str
        The pw.

    """

    with open(config_file, 'w') as config:  # save
        if not cfg.has_section(config_section):
            cfg.add_section(config_section)
            cfg.set(config_section, 'username', key)
            cfg.set(config_section, 'database', config_section)
            cfg.set(config_section, 'host', '130.XXX.XX.XX')
            cfg.set(config_section, 'port', port)
            cfg.set(config_section, 'password', value)
            cfg.write(config)


def config_file_load():
    """Load the username and pw from config file."""

    if os.path.isfile(config_file):
        config_file_init()
    else:
        config_file_not_found_message()


def config_file_init():
    """Read config file."""

    try:
        print('Load ' + config_file)
        cfg.read(config_file)
        global _loaded
        _loaded = True
    except:
        config_file_not_found_message()


def config_file_get(key):
    """Read data from config file.

    Parameters
    ----------
    key : str
        Config entries.
    """

    if not _loaded:
        config_file_init()
    try:
        return cfg.getfloat(config_section, key)
    except Exception:
        try:
            return cfg.getint(config_section, key)
        except:
            try:
                return cfg.getboolean(config_section, key)
            except:
                return cfg.get(config_section, key)


def config_file_not_found_message():
    """Show error message if file not found."""

    print('The config file {} could not be found!'.format(config_file))


def reeem_session():
    """SQLAlchemy session object with valid connection to database

    Returns
    -------
    conn : SQLAlchemy object
        Database connection object.
    """

    # host = input('host (default 130.226.55.43): ')
    host = '130.226.55.43'
    # print('host: ' + host)

    # port = input('port (default 5432): ')
    global port
    port = '5432'
    # print('port: ' + port)

    # database = input("database name (default 'reeem'): ")
    database = config_section
    # print('database: ' + database)

    # user = ''
    try:
        config_file_load()
        user = config_file_get('username')
        print('Hello ' + user + '!')
    except:
        print('Please provide connection parameters!')
        user = input('User name (default surname_name): ')

    # password = ''
    try:
        password = config_file_get('password')
    except:
        password = getpass.getpass(prompt='Password: ',
                                   stream=sys.stderr)
        config_section_set(key=user, value=password)
        print('Config file created!')

    # engine
    try:
        conn = create_engine(
            'postgresql://' + '%s:%s@%s:%s/%s' % (user,
                                                  password,
                                                  host,
                                                  port,
                                                  database)).connect()
    except:
        print('Password authentication failed for user "{}"'.format(user))
        try:
            os.remove(config_file)
            print('Existing config file deleted! '
                  'Restart script and try again!')
        except OSError:
            print(
                'Cannot delete file. '
                'Please check login parameters in config file!')

    print('Database connection established!')
    return conn


def reeem_scenario_log(con, version, io, schema, table, script, comment):
    """Write an entry in scenario log table.

    Parameters
    ----------
    con : connection
        SQLAlchemy connection object.
    version : str
        Version number.
    io : str
        IO-type (input, output, temp).
    schema : str
        Database schema.
    table : str
        Database table.
    script : str
        Script name.
    comment : str
        Comment.

    """

    sql_scenario_log_entry = text("""
        INSERT INTO model_draft.reeem_scenario_log
            (version,io,schema_name,table_name,script_name,entries,comment,
            user_name,timestamp,metadata)
        SELECT  '{0}' AS version,
                '{1}' AS io,
                '{2}' AS schema_name,
                '{3}' AS table_name,
                '{4}' AS script_name,
                COUNT(*) AS entries,
                '{5}' AS comment,
                session_user AS user_name,
                NOW() AT TIME ZONE 'Europe/Berlin' AS timestamp,
                obj_description('{2}.{3}' ::regclass) ::json AS metadata
        FROM    {2}.{3};""".format(version, io, schema, table, script,
                                   comment))

    con.execute(sql_scenario_log_entry)


def get_db_username(con, log):
    """Test the database connection and return the username
    
    Returns
    -------
    username : str
        The database username.
    """

    # example select
    log.info('...test database connection...')
    sql_test = text('SELECT name FROM model_draft.test_table')
    test_table = con.execute(sql_test.execution_options(autocommit=True))
    for row in test_table:
        print('username:', row['name'])

    # select session user
    sql_username = text('SELECT session_user')
    username = con.execute(sql_username.execution_options(autocommit=True))
    row = username.fetchone()
    username = row['session_user']
    log.info('......your database username is {}!...'.format(username))

    return username
