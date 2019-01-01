import shelve
from datetime import datetime
import time

import pytz
from six.moves import input

from pyecobee import *

import simplejson as json

from influxdb import InfluxDBClient

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# create a file handler
handler = logging.FileHandler('ecobee_influx.log')
handler.setLevel(logging.DEBUG)

# create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(handler)

#files for persistance storage 
file_name = 'pyecobee_db'

# influx db information
influxhost = '192.168.0.101'
influxport = '8086'
influxdbname = 'ecobee'

#Methods for storing influx db data into persistance storage


#Methods to grab data from persistance storage

def persist_to_shelf(file_name, ecobee_service):
    pyecobee_db = shelve.open(file_name, protocol=2)
    pyecobee_db[ecobee_service.thermostat_name] = ecobee_service
    pyecobee_db.close()

def refresh_tokens(ecobee_service):
    token_response = ecobee_service.refresh_tokens()
    logger.debug('TokenResponse returned from ecobee_service.refresh_tokens():\n{0}'.format(
        token_response.pretty_format()))
    persist_to_shelf('pyecobee_db', ecobee_service)

def request_tokens(ecobee_service):
    token_response = ecobee_service.request_tokens()
    logger.debug('TokenResponse returned from ecobee_service.request_tokens():\n{0}'.format(
        token_response.pretty_format()))

    persist_to_shelf('pyecobee_db', ecobee_service)

def authorize(ecobee_service):
    authorize_response = ecobee_service.authorize()
    logger.debug('AutorizeResponse returned from ecobee_service.authorize():\n{0}'.format(
        authorize_response.pretty_format()))

    persist_to_shelf('pyecobee_db', ecobee_service)

    logger.info('Please goto ecobee.com, login to the web portal and click on the settings tab. Ensure the My '
                'Apps widget is enabled. If it is not click on the My Apps option in the menu on the left. In the '
                'My Apps widget paste "{0}" and in the textbox labelled "Enter your 4 digit pin to '
                'install your third party app" and then click "Install App". The next screen will display any '
                'permissions the app requires and will ask you to click "Authorize" to add the application.\n\n'
                'After completing this step please hit "Enter" to continue.'.format(
        authorize_response.ecobee_pin))
    input()


if __name__ == '__main__':
    thermostat_name = 'Home'
    try:
        pyecobee_db = shelve.open('pyecobee_db', protocol=2)
        ecobee_service = pyecobee_db[thermostat_name]
    except KeyError:
        application_key = input('Please enter the API key of your ecobee App: ')
        ecobee_service = EcobeeService(thermostat_name=thermostat_name, application_key=application_key)
    finally:
        pyecobee_db.close()

    if not ecobee_service.authorization_token:
        authorize(ecobee_service)

    if not ecobee_service.access_token:
        request_tokens(ecobee_service)

    now_utc = datetime.now(pytz.utc)
    if now_utc > ecobee_service.refresh_token_expires_on:
        authorize(ecobee_service)
        request_tokens(ecobee_service)
    elif now_utc > ecobee_service.access_token_expires_on:
        token_response = ecobee_service.refresh_tokens()

    influx_client = InfluxDBClient(host=influxhost, port=influxport, database=influxdbname)

while True:

    now_utc = datetime.now(pytz.utc)
    if now_utc > ecobee_service.refresh_token_expires_on:
        authorize(ecobee_service)
        request_tokens(ecobee_service)
    elif now_utc > ecobee_service.access_token_expires_on:
        token_response = ecobee_service.refresh_tokens()

    try:
        thermostat_response = ecobee_service.request_thermostats(selection=Selection(
        selection_type=SelectionType.REGISTERED.value,
        selection_match='',
#        include_equipment_status=True,
#        include_alerts=True,
#        include_device=True, 
#        include_electricity=False, 
#        include_events=True, 
        include_extended_runtime=True 
#        include_house_details=True,
#        include_location=True, 
#        include_management=False, 
#        include_notification_settings=True,
#        include_oem_cfg=False, 
#        include_privacy=False, 
#        include_program=True, 
#        include_reminders=False,
#        include_runtime=True, 
#        include_security_settings=False, 
#        include_sensors=True,
#        include_settings=True, 
#        include_technician=False, 
#        include_utility=False, 
#        include_version=False,
#        include_weather=False
	))
    thermostat_response.pretty_format()

#    influx_client.write_points(thermostat_response.pretty_format())
#    parsed_response = json.loads(thermostat_response.pretty_format())
#    logger.info(parsed_response['thermostatList'])
#    print(thermostat_response.extendedRuntime())
    time.sleep(300)




