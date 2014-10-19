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
from copy import deepcopy

class APIClient:
  def __init__(self, config):
    self.is_logged_in = False
    assert config.validate()
    self.config = config
    self.session_token = None
    # TODO: create a DNSCache class and use that to aggressively cache domains
    self.cache = {}

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
      # update internal state
      self.session_token = response['session_token']
      self.is_logged_in = True
      # invalidate the cache after a login
      self.invalidate_cache()
      return True

    return False

  def logout(self):
    assert self.is_logged_in

    response = self.get('/api/logout')

    if response['result']['code'] == 100:
      # update internal state
      self.session_token = None
      self.is_logged_in = False
      # invalidate the cache after a logout
      self.invalidate_cache()
      return True
    else:
      return False

  def get_domains(self, use_cache=True):
    assert self.is_logged_in

    if use_cache:
      if self.is_cache_line_set('domains'):
        return self.get_cache_line('domains')

    response = self.get('/api/domain/list')

    if response['result']['code'] == 100:
      self.set_cache_line('domains', response['domains'])
      return response['domains']
    else:
      return {}

  def get_dns_A_records(self, use_cache=True):
    assert self.is_logged_in

    if use_cache:
      if self.is_cache_line_set('records'):
        return self.get_cache_line('records')

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

      self.set_cache_line('records', result)

    return result

  def create_dns_A_record(self, target, use_cache=True):
    assert self.is_logged_in

    dns_A_records = self.get_dns_A_records(use_cache=use_cache)

    # does the DNS A record actually exist?
    if self.config.fqdn in dns_A_records:
      record = dns_A_records[self.config.fqdn]
      if record['content'] == target:
        # it exists and is configured properly, so there is nothing to do
        return True
      else:
        # it exists, but the contents are not what we want, so we need to update it
        return self.update_dns_A_record(target, use_cache=True)

    response = self.post('/api/dns/create/%s' % self.config.domain, {
      'hostname': self.config.subdomain,
      'type': 'A',
      'content': target,
      'ttl': 300,
      'priority': 10
    })

    if response['result']['code'] == 100:
      # TODO: break here
      self.invalidate_cache_line('records')
      return True
    else:
      return False

  def delete_dns_A_record(self, use_cache=True):
    assert self.is_logged_in

    dns_A_records = self.get_dns_A_records(use_cache=use_cache)

    # does the DNS A record actually exist?
    if self.config.fqdn not in dns_A_records:
      return True

    record = dns_A_records[self.config.fqdn]

    response = self.post('/api/dns/delete/%s' % self.config.domain, {
      'record_id': record['record_id']
    })

    if response['result']['code'] == 100:
      del dns_A_records[self.config.fqdn]
      self.set_cache_line('records', dns_A_records)
      return True
    else:
      return False

  def update_dns_A_record(self, new_target, use_cache=True):
    assert self.is_logged_in

    dns_A_records = self.get_dns_A_records(use_cache=use_cache)

    # does the DNS A record actually exist?
    if self.config.fqdn in dns_A_records:
      record = dns_A_records[self.config.fqdn]

      # check if the DNS A record needs to be updated
      if record['content'] == new_target:
        return True

      # the DNS A record needs to be updated after all
      # note: the cache will automatically be updated
      return self.delete_dns_A_record(use_cache=True) and \
             self.create_dns_A_record(new_target, use_cache=True)
    else:
      return self.create_dns_A_record(new_target, use_cache=True)

  def invalidate_cache(self):
    self.cache = {}

  def invalidate_cache_line(self, key):
    if key in self.cache:
      del self.cache[key]

  def set_cache_line(self, key, value):
    self.cache[key] = deepcopy(value)

  def is_cache_line_set(self, key):
    return key in self.cache

  def get_cache_line(self, key):
    assert self.is_cache_line_set(key)
    return deepcopy(self.cache[key])

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
