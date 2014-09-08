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
from JSONFile import JSONFile

class ConfigFile(JSONFile):
  def __init__(self, filename):
    self.environment = None
    self.username = None
    self.api_token = None
    self.url = None
    self.domain = None
    self.subdomain = None
    self.fqdn = None
    super(ConfigFile, self).__init__(filename)

  def parse_data(self, json_data):
    if 'environment' in json_data:
      if json_data['environment'] in json_data:
        env = json_data[json_data['environment']]

        if 'username' in env and 'api_token' in env and 'url' in env:
          self.environment = json_data['environment']
          self.username = env['username']
          self.api_token = env['api_token']
          self.url = env['url']
          self.domain = env['domain']
          self.subdomain = env['subdomain']
          self.fqdn = '%s.%s' % (self.subdomain, self.domain)
          return True

    return False

  def is_test_environment(self):
    return self.environment == 'test'
