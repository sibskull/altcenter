#!/usr/bin/python3

# Application for configure and maintain ALT operating system
# (c) 2024 Andrey Cherepanov <cas@altlinux.org>

# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 3 of the License, or (at your option) any later
# version.

# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.

# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 59 Temple
# Place - Suite 330, Boston, MA  02111-1307, USA.

import os
import traceback
from importlib import util
from PyQt5.QtCore import QObject

class Base(QObject):
    """Base skel for plugin"""
    plugins = []
    name = ""

    def __init__(self):
        super().__init__()

    # For every class that inherits from the current,
    # the class name will be added to plugins
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.plugins.append(cls)

    def start(self, plist, pane):
        pass

    def setName(self, name):
        self.name = name

# Load one module
def load_module(path):
    name = os.path.split(path)[-1]
    spec = util.spec_from_file_location(name, path)
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

plugin_path = os.path.dirname(os.path.abspath(__file__))
for fname in os.listdir(plugin_path):
    if not fname.startswith('.') and \
       not fname.startswith('__') and fname.endswith('.py'):
        try:
            load_module(os.path.join(plugin_path, fname))
        except Exception:
            traceback.print_exc()
