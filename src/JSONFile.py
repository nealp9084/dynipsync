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
import os
import json

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
