# dynipsync - a dynamic DNS utility
# Copyright (C) 2014  Neal Patel
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import sys
import logging
from argparse import ArgumentParser
from lib.APIClient import APIClient
from lib.ConfigFile import ConfigFile

def main():
  # read in the command line args
  parser = ArgumentParser(description=
                          'A dynamic DNS client for the Name.com API')
  parser.add_argument('-f', '--config-file', dest='config_file', required=True,
                    help='The JSON config file containing Name.com API'
                         'credentials. See conf/config.json.example for'
                         'a sample config file.')
  parser.add_argument('-v', '--verbose', action='store_true', dest='verbose',
                    default=False, help='Print debugging information')

  opts = parser.parse_args()

  # set log level
  if opts.verbose:
    logging.root.setLevel(logging.DEBUG)

  # read in the config file
  config = ConfigFile(opts.config_file)

  # validate the config file
  if not config.validate():
    logging.error('The config file (%s) is unreadable or invalid.' %
                  opts.config_file)
    return 1

  logging.info('Successfully read in the config file.')
  client = APIClient(config)

  # try to log in
  if not client.login():
    logging.error('Unable to log in due to invalid credentials (user %s)' %
                  config.username)
    return 1

  # ping/pong
  logging.info('Successfully logged in.')
  client.hello()
  domains = client.get_domains()

  # check for domain registration
  if config.domain in domains:
    logging.info('%s domain registration found.' % config.domain)
  else:
    logging.error('%s domain registration not found.' % config.domain)
    return 1

  # get DNS records for domains
  dns_A_records = client.get_dns_A_records()

  # check if our subdomain is registered
  if config.fqdn in dns_A_records:
    # yup, it's registered
    logging.info('%s DNS A record found.' % config.fqdn)

    # update the subdomain's record
    if client.update_dns_A_record('192.168.1.24'):
      logging.info('Updated DNS A record: 192.168.1.24')
    else:
      logging.error('Failed to update DNS A record!')
  else:
    # nope, not registered
    logging.warn('%s DNS A record not found; attempting to create.' %
                 config.fqdn)

    # create the subdomain's record
    if not client.create_dns_A_record('130.131.132.133'):
      logging.error('Failed to automatically create a DNS A record for %s.' %
                    config.fqdn)
      return 1

    logging.info('Automatically created a DNS A record for %s.' % config.fqdn)

  # bye!
  client.logout()
  return 0

if __name__ == '__main__':
  sys.exit(main())
