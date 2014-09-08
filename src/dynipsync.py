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
from ConfigFile import ConfigFile
from APIClient import APIClient

def main(argv):
  # TODO: command line arg parsing: credential file, ip check
  logging.root.setLevel(logging.DEBUG)

  config = ConfigFile('conf/config.json')

  if not config.validate():
    logging.error('There is an error in the config file.')
    return 1

  logging.info('Successfully read in the config file.')
  client = APIClient(config)

  if not client.login():
    logging.error('Unable to log in due to invalid credentials (user %s)' %
                  config.username)
    return 1

  logging.info('Successfully logged in.')
  client.hello()
  domains = client.get_domains()

  if config.domain in domains:
    logging.info('%s domain registration found.' % config.domain)
  else:
    logging.error('%s domain registration not found.' % config.domain)
    return 1

  dns_A_records = client.get_dns_A_records()

  if config.fqdn in dns_A_records:
    logging.info('%s DNS A record found.' % config.fqdn)

    if client.update_dns_A_record('192.168.1.24'):
      logging.info('Updated DNS A record: 192.168.1.24')
    else:
      logging.error('Failed to update DNS A record!')
  else:
    logging.warn('%s DNS A record not found; attempting to create.' %
                 config.fqdn)

    if not client.create_dns_A_record('130.131.132.133'):
      logging.error('Failed to automatically create a DNS A record for %s.' %
                    config.fqdn)
      return 1

    logging.info('Automatically created a DNS A record for %s.' % config.fqdn)

  client.logout()
  return 0

if __name__ == '__main__':
  sys.exit(main(sys.argv))
