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
import json
from ConfigFile import ConfigFile
import requests

class APIClient:
  def __init__(self, config):
    self.is_logged_in = False
    assert config.validate()
    self.config = config
    self.session_token = None

  def hello(self, authenticate_session=False):
    assert self.is_logged_in
    response = self.get('/api/hello', params={},
                        authenticate_session=authenticate_session)
    return response['result']['code'] == 100

  def login(self):
    response = self.post('/api/login', {
      'username': self.config.username,
      'api_token': self.config.api_token
    }, authenticate_session=False)

    if response['result']['code'] == 100:
      self.session_token = response['session_token']
      self.is_logged_in = True
      return True

    return False

  def logout(self):
    assert self.is_logged_in

    response = self.get('/api/logout')
    return response['result']['code'] == 100

  def get_domains(self):
    response = self.get('/api/domain/list')
    if response['result']['code'] == 100:
      return response['domains']
    else:
      return {}

  def get_dns_A_records(self):
    result = {}
    response = self.get('/api/dns/list/%s' % self.config.domain)

    if response['result']['code'] == 100:
      records = response['records']

      # restructure the response
      for record in records:
        if record['type'] == 'A':
          record_name = record['name']
          del record['name']
          del record['type']
          result[record_name] = record

    return result

  def create_dns_A_record(self, target, dns_A_records=None):
    dns_A_records = dns_A_records or self.get_dns_A_records()

    # does the DNS A record actually exist?
    if self.config.fqdn in dns_A_records:
      record = dns_A_records[self.config.fqdn]
      return record['content'] == target

    response = self.post('/api/dns/create/%s' % self.config.domain, {
      'hostname': self.config.subdomain,
      'type': 'A',
      'content': target,
      'ttl': 300,
      'priority': 10
    })
    return response['result']['code'] == 100

  def delete_dns_A_record(self, dns_A_records=None):
    dns_A_records = dns_A_records or self.get_dns_A_records()

    # does the DNS A record actually exist?
    if self.config.fqdn not in dns_A_records:
      return True

    record = dns_A_records[self.config.fqdn]

    response = self.post('/api/dns/delete/%s' % self.config.domain, {
      'record_id': record['record_id']
    })
    return response['result']['code'] == 100

  def update_dns_A_record(self, new_target):
    dns_A_records = self.get_dns_A_records()

    # does the DNS A record actually exist?
    if self.config.fqdn in dns_A_records:
      record = dns_A_records[self.config.fqdn]

      # check if the DNS A record needs to be updated
      if record['content'] == new_target:
        return True

      # the DNS A record needs to be updated after all
      return self.delete_dns_A_record(dns_A_records) and \
             self.create_dns_A_record(new_target)
    else:
      return self.create_dns_A_record(new_target, dns_A_records)

  def form_endpoint(self, endpoint):
    (first_part, second_part) = (self.config.url, endpoint)

    if first_part.endswith('/'):
      first_part = self.config.url[:-1]

    if second_part.startswith('/'):
      second_part = endpoint[1:]

    return first_part + '/' + second_part

  def post(self, endpoint, payload, authenticate_session=True):
    endpoint_url = self.form_endpoint(endpoint)

    headers = {}

    if authenticate_session:
      assert self.is_logged_in
      headers['Api-Session-Token'] = self.session_token

    verify = not self.config.is_test_environment()

    try:
      r = requests.post(endpoint_url, data=json.dumps(payload),
                        headers=headers, verify=verify)

      if r.status_code == 200:
        return r.json()
      else:
        return None
    except:
      return None

  def get(self, endpoint, params={}, authenticate_session=True):
    endpoint_url = self.form_endpoint(endpoint)

    headers = {}

    if authenticate_session:
      assert self.is_logged_in
      headers['Api-Session-Token'] = self.session_token

    verify = not self.config.is_test_environment()

    try:
      r = requests.get(endpoint_url, params=params,
                       headers=headers, verify=verify)

      if r.status_code == 200:
        return r.json()
      else:
        return None
    except:
      return None
