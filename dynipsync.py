import json
import sys
import os
import requests
import logging

class JSONFile(object):
  def __init__(self, filename):
    self.is_read = False
    self.is_parsed = False

    json_data = self.read_file(filename)

    if json_data:
      self.is_read = True

      if self.parse_data(json_data):
        self.is_parsed = True

  def read_file(self, filename):
    if not os.path.isfile(filename):
      return None

    try:
      with open(filename) as f:
        return json.load(f)
    except:
      return None

  def validate(self):
    return self.is_read and self.is_parsed


class Config(JSONFile):
  def __init__(self, filename):
    self.environment = None
    self.username = None
    self.api_token = None
    self.url = None
    self.domain = None
    self.subdomain = None
    self.fqdn = None
    super(Config, self).__init__(filename)

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

class APIClient:
  def __init__(self, config):
    self.is_logged_in = False
    assert config.validate()
    self.config = config
    self.session_token = None

  def login(self):
    response = self.post('/api/login', {
      'username': self.config.username,
      'api_token': self.config.api_token
    }, authenticate_session=False)

    if response:
      if response['result']['code'] == 100:
        self.session_token = response['session_token']
        self.is_logged_in = True
        return True

    return False

  def hello(self):
    assert self.is_logged_in
    response = self.get('/api/hello', params={}, authenticate_session=False)
    return response['result']['code'] == 100

  def get_domains(self):
    response = self.get('/api/domain/list')
    if response['result']['code'] == 100:
      return response['domains']
    else:
      return {}

  def get_dns_A_records(self):
    response = self.get('/api/dns/list/%s' % self.config.domain)
    if response['result']['code'] == 100:
      records = response['records']

      # restructure the response
      result = {}

      for record in records:
        if record['type'] == 'A':
          record_name = record['name']
          del record['name']
          del record['type']
          result[record_name] = record

      return result
    else:
      return {}

  def create_dns_A_record(self, target):
    response = self.post('/api/dns/create/%s' % self.config.domain, {
      'hostname': self.config.subdomain,
      'type': 'A',
      'content': target,
      'ttl': 300,
      'priority': 10
    })
    return response['result']['code'] == 100

  # TODO: implement
  def update_dns_A_record(self, new_target):
    1

  def logout(self):
    assert self.is_logged_in

    response = self.get('/api/logout')
    return response['result']['code'] == 100

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

    try:
      if self.config.is_test_environment:
        r = requests.post(endpoint_url, data=json.dumps(payload), headers=headers, verify=False)
      else:
        r = requests.post(endpoint_url, data=json.dumps(payload), headers=headers)

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

    try:
      if self.config.is_test_environment:
        r = requests.get(endpoint_url, params=params, headers=headers, verify=False)
      else:
        r = requests.get(endpoint_url, params=params, headers=headers)

      if r.status_code == 200:
        return r.json()
      else:
        return None
    except:
      return None


def main():
  # todo: command line arg parsing: credential file, ip check
  logging.root.setLevel(logging.DEBUG)

  config = Config('config.json')

  if not config.validate():
    logging.error('There is an error in the config file.')
    return 1

  logging.info('Successfully read in the config file.')
  client = APIClient(config)

  if not client.login():
    logging.error('Unable to log in due to invalid credentials (user %s)' % config.username)
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
  else:
    logging.warn('%s DNS A record not found; attempting to create.' % config.fqdn)

    if not client.create_dns_A_record('130.131.132.133'):
      logging.error('Failed to automatically create a DNS A record for %s.' % config.fqdn)
      return 1

    logging.info('Automatically created a DNS A record for %s.' % config.fqdn)

  client.logout()
  return 0


if __name__ == '__main__':
  sys.exit(main())
