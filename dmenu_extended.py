# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import sys
import os
import subprocess
import signal
import json
import codecs
import locale
import operator
import time

# Try and import the faster os.walk implementation - scandir
scandir_present = False
try:
    from os import scandir, walk
    scandir_present = True
except ImportError:
    scandir_present = False
if scandir_present == False:
    try:
        from scandir import scandir, walk
        scandir_present = True
    except ImportError:
        from os import walk
        scandir_present = False

# Python 3 urllib import with Python 2 fallback
try:
    import urllib.request as urllib2
except:
    import urllib2


_version_ = 16.1023

# Find out the system's favouite encoding
system_encoding = locale.getpreferredencoding()

path_base = os.path.expanduser('~') + '/.config/dmenu-extended'
path_cache = path_base + '/cache'
path_prefs = path_base + '/config'
path_plugins = path_base + '/plugins'

file_prefs = path_prefs + '/dmenuExtended_preferences.txt'
file_cache = path_cache + '/dmenuExtended_all.txt'
file_cache_binaries = path_cache + '/dmenuExtended_binaries.txt'
file_cache_files = path_cache + '/dmenuExtended_files.txt'
file_cache_folders = path_cache + '/dmenuExtended_folders.txt'
file_cache_aliases = path_cache + '/dmenuExtended_aliases.txt'
file_cache_aliasesLookup = path_cache + '/dmenuExtended_aliases_lookup.json'
file_cache_plugins = path_cache + '/dmenuExtended_plugins.txt'
file_cache_frequentlyUsed_frequency = path_cache + '/dmenuExtended_frequentlyUsed_frequency.json'
file_cache_frequentlyUsed_ordered = path_cache + '/dmenuExtended_frequentlyUsed_ordered.json'

d = None # Global dmenu object - initialised near bottom of script

default_prefs = {
    "valid_extensions": [
        "py",                           # Python script
        "svg",                          # Vector graphics
        "pdf",                          # Portable document format
        "txt",                          # Plain text
        "png",                          # Image file
        "jpg",                          # Image file
        "gif",                          # Image file
        "php",                          # PHP source-code
        "tex",                          # LaTeX document
        "odf",                          # Open document format
        "ods",                          # Open document spreadsheet
        "avi",                          # Video file
        "mpg",                          # Video file
        "mp3",                          # Music file
        "lyx",                          # Lyx document
        "bib",                          # LaTeX bibliograpy
        "iso",                          # CD image
        "ps",                           # Postscript document
        "zip",                          # Compressed archive
        "xcf",                          # Gimp image format
        "doc",                          # Microsoft document format
        "docx"                          # Microsoft document format
        "xls",                          # Microsoft spreadsheet format
        "xlsx",                         # Microsoft spreadsheet format
        "md",                           # Markup document
        "html",                         # HTML document
        "sublime-project"               # Project file for sublime
    ],
    "watch_folders": ["~/"],            # Base folders through which to search
    "follow_symlinks": False,           # Follow links to other locations
    "ignore_folders": [],               # Folders to exclude from the search
    "scan_hidden_folders": False,       # Enter hidden folders while scanning for items
    "include_hidden_files": False,      # Include hidden files in the cache
    "include_hidden_folders": False,    # Include hidden folders in the cache
    "include_items": [],                # Extra items to display - manually added
    "exclude_items": [],                # Items to hide - manually hidden
    "include_binaries": False,
    "filter_binaries": False,            # Only include binaries that have an associated .desktop file
    "include_applications": True,       # Add items from /usr/share/applications
    "alias_applications": True,         # Alias applications with their common names
    "path_aliasFile": "",               # Pointer to an aliases file (if any)
    "frequently_used": 0,               # Number of most frequently used commands to show in the menu
    "alias_display_format": "{name}",
    "path_shellCommand": "~/.dmenuEextended_shellCommand.sh",
    "menu": 'dmenu',                    # Executable for the menu
    "menu_arguments": [
        "-b",                           # Place at bottom of screen
        "-i",                           # Case insensitive searching
        "-nf",                          # Element foreground colour
        "#888888",
        "-nb",                          # Element background colour
        "#1D1F21",
        "-sf",                          # Selected element foreground colour
        "#ffffff",
        "-sb",                          # Selected element background colour
        "#1D1F21",
        "-fn",                          # Font and size
        "terminus",
        "-l",                           # Number of lines to display
        "20"
    ],
    "password_helper": [
        "zenity",
        "--password",
        "--title={prompt}"
    ],
    "fileopener": "xdg-open",           # Program to handle opening files
    "filebrowser": "xdg-open",          # Program to handle opening paths
    "webbrowser": "xdg-open",           # Program to hangle opening urls
    "terminal": "xterm",                # Terminal
    "indicator_submenu": "->",          # Symbol to indicate a submenu item
    "indicator_edit": "*",              # Symbol to indicate an item will launch an editor
    "indicator_alias": "",              # Symbol to indecate an aliased command
    "prompt": "Open:"                   # Prompt
}

def setup_user_files():
    """ Returns nothing

    Create a path for the users prefs files to be stored in their
    home folder. Create default config files and place them in the relevant
    directory.
    """

    print('Setting up dmenu-extended prefs files...')

    try:
        os.makedirs(path_plugins)
        print('Plugins directory created')
    except OSError:
        print('Plugins directory exists - skipped')

    try:
        os.makedirs(path_cache)
        print('Cache directory created')
    except OSError:
        print('Cache directory exists - skipped')

    try:
        os.makedirs(path_prefs)
        print('prefs directory created')
    except OSError:
        print('prefs directory exists - skipped')

    # If relevant binaries exist, swap them out for the more appropriate items

    # It has been decided against setting gnome-open or gvfs-open as a default
    # file handler to prevent intermittent failure to open a text editor
    # required to edit the configuration file.

    if os.path.exists('/usr/bin/gnome-terminal'):
        default_prefs['terminal'] = 'gnome-terminal'
    if os.path.exists('/usr/bin/urxvt'):
        default_prefs['terminal'] = 'urxvt'

    if os.path.exists(os.path.expanduser('~') + '/.bash_aliases'):
        default_prefs['path_aliasFile'] = os.path.expanduser('~') + '/.bash_aliases'
    elif os.path.exists(os.path.expanduser('~') + '/.zsh_aliases'):
        default_prefs['path_aliasFile'] = os.path.expanduser('~') + '/.zsh_aliases'

    # Dump the prefs file
    if os.path.exists(file_prefs) == False:
        with open(file_prefs,'w') as f:
            json.dump(default_prefs, f, sort_keys=True, indent=4)
        print('Preferences file created at: ' + file_prefs)
    else:
        print('Existing preferences file found, will not overwrite.')

    # Create package __init__ - for easy access to the plugins
    with open(path_plugins + '/__init__.py','w') as f:
        f.write('import os\n')
        f.write('import glob\n')
        f.write('__all__ = [ os.path.basename(f)[:-3] for f in glob.glob(os.path.dirname(__file__)+"/*.py")]')


if (os.path.exists(path_plugins + '/__init__.py') and
    os.path.exists(file_cache) and
    os.path.exists(file_prefs)):
    sys.path.append(path_base)
else:
    setup_user_files()
    sys.path.append(path_base)

import plugins


def load_plugins(debug=False):
    if debug:
        print('Loading plugins')

    plugins_loaded = [{"filename": "plugin_settings.py",
                       "plugin": extension()}]

    # Pass the plug-in's version of dmenu the list of launch arguments
    plugins_loaded[0]['plugin'].launch_args = d.launch_args
    if debug:
        plugins_loaded[0]['plugin'].debug = True

    for plugin in plugins.__all__:
        if plugin not in ['__init__', 'plugin_settings.py']:
            try:
                __import__('plugins.' + plugin)
                exec('plugins_loaded.append({"filename": "' + plugin + '.py", "plugin": plugins.' + plugin + '.extension()})')
                # Pass the plug-in's version of dmenu the list of launch arguments
                plugins_loaded[-1]['plugin'].launch_args = d.launch_args
                if debug:
                    plugins_loaded[-1]['plugin'].debug = True
                    print('Loaded plugin ' + plugin)
            except Exception as e:
                if debug:
                    print('Error loading plugin ' + plugin)
                    print(str(e))
                else:
                    print('!! Plugin was deleted to prevent interruption to dmenuExtended')
                    os.remove(path_plugins + '/' + plugin + '.py')

    return plugins_loaded


def frequent_commands_store(command):
    """ Records the user's execution of a command. This involves first adding the command
    to a dictionary, or incrementing the frequency count if it already exists.
    That dictionary is then used to create the frequently used cache by sorting based
    on value (frequency), then writing the sorted commands to the frequency file.
    """
    if os.path.exists(file_cache_frequentlyUsed_frequency) is False:
        if d.debug:
            print("Frequently used items does not exist, starting new...")
        cmds = {}
    else:
        if d.debug:
            print("Frequently used items cache exists, retrieving...")
        cmds = d.load_json(file_cache_frequentlyUsed_frequency)

    if d.debug:
        print("Adding entered command to the cache...")
    if command in cmds.keys():
        cmds[command] += 1
    else:
        cmds[command] = 1

    if d.debug:
        print("Sorting and saving the cache...")

    d.save_json(file_cache_frequentlyUsed_frequency, cmds)
    cmds = sorted(cmds.items(), key=operator.itemgetter(1), reverse=True)

    # Write the full list of commands to storage, only the required number is read
    with open(file_cache_frequentlyUsed_ordered, 'w') as f:
        for cmd in cmds:
            f.write(cmd[0]+'\n')


def frequent_commands_retrieve(number):
    """ Retrieves the list of frequently used commands, sorted by their frequency """
    if os.path.exists(file_cache_frequentlyUsed_ordered) is False:
        if d.debug:
            print("Frequently used items cache does not exist, will return nothing")
        return ""
    else:
        if d.debug:
            print("Frequently used items cache exists, retrieving and clipping to " + str(number) + " items")
        with open(file_cache_frequentlyUsed_ordered, 'r') as f:
            return "".join(f.readlines()[:number])


class dmenu(object):

    plugins_loaded = False
    prefs = False
    debug = False
    preCommand = False
    launch_args = [] # Holds a list of menu items to automatically select


    def get_plugins(self, force=False):
        """ Returns a list of loaded plugins

        This method will load plugins in the plugins directory if they
        havent already been loaded. Optionally, you may force the
        reloading of plugins by setting the parameter 'force' to true.
        """

        if self.plugins_loaded == False:
            self.plugins_loaded = load_plugins(self.debug)
        elif force:
            if self.debug:
                print("Forced reloading of plugins")

            # For Python2/3 compatibility
            try:
                # Python2
                reload(plugins)
            except NameError:
                # Python3
                from imp import reload
                reload(plugins)

            self.plugins_loaded = load_plugins(self.debug)

        return self.plugins_loaded


    def system_path(self):
        """
        Array containing system paths
        """

        # Get the PATH environmental variable
        path = os.environ.get('PATH')

        # If we're in Python <3 (less-than-three), we want this to be a unicode string
        # In python 3, all strings are unicode already, trying to decode gives AttributeError
        try:
            path = path.decode(sys.getfilesystemencoding())
        except AttributeError:
            pass

        # Split and remove duplicates
        path = list(set(path.split(':')))

        # Some paths contain an extra separator, remove the empty path
        try:
            path.remove('')
        except ValueError:
            pass

        return path


    def application_paths(self):
        """ Array containing the paths to application flies

        Based on PyXDG (https://github.com/takluyver/pyxdg)
        """

        # Get the home applications directory (usually ~/.local/share/applications)
        home_folder = os.path.expanduser('~')
        data_home = os.environ.get('XDG_DATA_HOME',os.path.join(home_folder,'.local','share'))
        paths = [os.path.join(data_home,'applications')]

        # Get other directories
        data_other = os.environ.get('XDG_DATADIRS','/usr/local/share:/usr/share').split(":")
        paths.extend([os.path.join(direc,'applications') for direc in data_other])

        # Filter paths that don't exist
        paths = filter(os.path.isdir, paths)

        return paths


    def load_json(self, path):
        """ Loads and retuns the parsed contents of a specified json file

        This method will return 'False' if either the file does not exist
        or the specified file could not be parsed as valid json.
        """

        if os.path.exists(path):
            with codecs.open(path,'r',encoding=system_encoding) as f:
                try:
                    return json.load(f)
                except:
                    if self.debug:
                        print("Error parsing prefs from json file " + path)
                    self.prefs = default_prefs
                    option = "Edit file manually"
                    response = self.menu("There is an error opening " + path + "\n" + option)
                    if response == option:
                        self.open_file(path)
        else:
            if self.debug:
                print('Error opening json file ' + path)
                print('File does not exist')
            return False


    def save_json(self, path, items):
        """ Saves a dictionary to a specified path using the json format"""

        with codecs.open(path, 'w', encoding=system_encoding) as f:
            json.dump(items, f, sort_keys=True, indent=4)


    def load_preferences(self):
        if self.prefs == False:
            self.prefs = self.load_json(file_prefs)

            if self.prefs == False:
                self.open_file(file_prefs)
                sys.exit()
            else:

                # # Check for old display format and update if necessary
                # if 'aliased_applications_format' in self.prefs.keys():
                #     if 'alias_display_format' not in self.prefs.keys():
                #         self.prefs['alias_display_format'] = self.prefs['aliased_applications_format']
                #     self.prefs.pop('aliased_applications_format')

                # If there are things in the default that aren't in the
                # user config, resave the user configuration
                resave = False
                for key, value in default_prefs.items():
                    if key not in self.prefs:
                        if key == 'alias_display_format' and 'aliased_applications_format' in self.prefs.keys():
                            self.prefs['alias_display_format'] = self.prefs['aliased_applications_format']
                            self.prefs.pop('aliased_applications_format')
                        else:
                            self.prefs[key] = value
                        resave = True
                if resave:
                    self.save_preferences()


    def save_preferences(self):
        self.save_json(file_prefs, self.prefs)


    def connect_to(self, url):
        request = urllib2.Request(url)
        response = urllib2.urlopen(request)
        return response.read().decode(system_encoding)


    def download_text(self, url):
        return self.connect_to(url)


    def download_json(self, url):
        return json.loads(self.connect_to(url))


    def message_open(self, message):
        self.load_preferences()
        self.message = subprocess.Popen([self.prefs['menu']] + self.prefs['menu_arguments'],
                                        stdin=subprocess.PIPE,
                                        preexec_fn=os.setsid)
        msg = str(message)
        msg = "Please wait: " + msg
        msg = msg.encode(system_encoding)
        self.message.stdin.write(msg)
        self.message.stdin.close()


    def message_close(self):
        os.killpg(self.message.pid, signal.SIGTERM)


    def get_password(self, helper_text=None):
        prompt = "Password"
        if helper_text is not None:
            prompt += " (" + helper_text + ")"
        prompt += ": "
        command = self.prefs["password_helper"]
        for index, item in enumerate(command):
            if "{prompt}" in item:
                command[index] = item.format(prompt=prompt)
        return subprocess.check_output(command)


    def menu(self, items, prompt=""):
        self.load_preferences()
        # Check the passed commands from launch for a shortcut
        if len(self.launch_args) > 0:
            out = self.launch_args[0]
            self.launch_args = self.launch_args[1:]
            if self.debug:
                print('Menu bypassed with launch argument: ' + out)
            return out
        else:
            p = subprocess.Popen([self.prefs['menu']] + self.prefs['menu_arguments'] + ['-p', prompt],
                                 stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE)

            if type(items) == list:
                items = "\n".join(items)

            # Prevent rofi from closing with no prompt
            if self.prefs['menu'] == 'rofi' and items == '':
                items = " "

            out = p.communicate(items.encode(system_encoding))[0]

            if out.strip() == '':
                sys.exit()
            else:
                return out.decode().strip('\n')


    def select(self, items, prompt="", numeric=False):
        # Check the passed commands from launch for a shortcut
        if len(self.launch_args) > 0:
            result = self.launch_args[0]
            self.launch_args = self.launch_args[1:]
            if self.debug:
                print('Menu bypassed with launch argument: ' + result)
        else:
            result = self.menu(items, prompt)

        for index, item in enumerate(items):
            if result.find(item) != -1:
                if numeric:
                    return index
                else:
                    return item
        return -1


    def sort_shortest(self, items):
        items.sort(key=len)
        return items


    def open_url(self, url):
        self.load_preferences()
        if self.debug:
            print('Opening url: "' + url + '" with ' + self.prefs['webbrowser'])
        self.execute(self.prefs['webbrowser'] + ' ' + url.replace(' ', '%20'))


    def open_directory(self, path):
        self.load_preferences()
        if self.debug:
            print('Opening folder: "' + path + '" with ' + self.prefs['filebrowser'])
        self.execute(self.prefs['filebrowser'] + ' "' + path + '"')


    def open_terminal(self, command, hold=False, direct=False):
        self.load_preferences()
        sh_command_file = os.path.expanduser(self.prefs['path_shellCommand']);
        with open(sh_command_file, 'w') as f:
            f.write("#! /bin/bash\n")
            f.write(command + "\n")

            if hold == True:
                f.write('echo "\n\nPress enter to exit";')
                f.write('read var;')

        os.chmod(os.path.expanduser(sh_command_file), 0o744)
        if direct:
            os.system('sh -e ' + sh_command_file)
        else:
            os.system(self.prefs['terminal'] + ' -e ' + sh_command_file)


    def open_file(self, path):
        self.load_preferences()
        if self.debug:
            print('Opening file with command: ' + self.prefs['fileopener'] + " '" + path + "'")
        exit_code = self.execute(self.prefs['fileopener'] + ' "' + path + '"', fork=False)
        if exit_code is not 0:
            open_failure = False
            offer = None
            if exit_code == 256 and self.prefs['fileopener'] == 'gnome-open':
                open_failure = True
                offer = 'xdg-open'
            elif exit_code == 4 and self.prefs['fileopener'] == 'xdg-open':
                open_failure = True
            if open_failure:
                mimetype = str(self.command_output('xdg-mime query filetype ' + path)[0])
                message = ["Error: " + self.prefs['fileopener'] + " reports no application is associated with this filetype (MIME type: " + mimetype + ")"]
                if offer is not None:
                    option = "Try opening with " + offer + "?"
                message.append(option)

                if self.menu(message) == option:
                    self.prefs['fileopener'] = offer
                    self.open_file(path)


    def execute(self, command, fork=None):
        """
        Execute a command on behalf of dmenu. Will fork into background
        by default unless fork=False. Will prepend the value of
        self.preCommand to the given command, necessary for sudo calls.
        """
        if fork == False:
            extra = ''
        else:
            extra = ' &'
        if self.preCommand:
            command = self.preCommand + command
        return os.system(command + extra)


    def cache_regenerate(self, message=True):
        if message:
            self.message_open('building cache...\nThis may take a while (press enter to run in background).')
        cache = self.cache_build()
        if message:
            self.message_close()
        return cache


    def cache_save(self, items, path):
        try:
            with codecs.open(path, 'w',encoding=system_encoding) as f:
                if type(items) == list:
                    for item in items:
                        f.write(item+"\n")
                else:
                    f.write(items)
            return 1
        except UnicodeEncodeError:
            import string
            tmp = []
            foundError = False
            if self.debug:
                print('Non-printable characters detected in cache: ')
            for item in items:
                clean = True
                for char in item:
                    if char not in string.printable:
                        clean = False
                        foundError = True
                        if self.debug:
                            print('Culprit: ' + item)
                if clean:
                    tmp.append(item)
            if foundError:
                if self.debug:
                    print('')
                    print('Caching performance will be affected while these items remain')
                    print('Offending items have been excluded from cache')
                with codecs.open(path, 'wb', encoding=system_encoding) as f:
                    for item in tmp:
                        f.write(item+"\n")
                return 2
            else:
                if self.debug:
                    print('Unknown error saving data cache')
                return 0


    def cache_open(self, path):
        try:
            if self.debug:
                print('Opening cache at ' + path)
            with codecs.open(path,'r',encoding=system_encoding) as f:
                return f.read()
        except:
            return False


    def cache_load(self, exitOnFail=False):
        cache_frequent = frequent_commands_retrieve(self.prefs['frequently_used'])
        cache_plugins = self.cache_open(file_cache_plugins)
        cache_scanned = self.cache_open(file_cache)

        if cache_plugins == False or cache_scanned == False:
            if exitOnFail:
                sys.exit()
            else:
                if self.cache_regenerate() == False:
                    self.menu(['Error caching data'])
                    sys.exit()
                else:
                    return self.cache_load(exitOnFail=True)

        return cache_plugins + cache_frequent + cache_scanned


    def command_output(self, command, split=True):
        if type(command) != list:
            command = command.split(" ")
        tmp = subprocess.check_output(command)

        out = tmp.decode(system_encoding)

        if split:
            return out.split("\n")
        else:
            return out


    def scan_binaries(self):
        out = []
        for path in self.system_path():
            if not os.path.exists(path):
                continue
            for binary in os.listdir(path):
                if binary[:3] is not 'gpk':
                    out.append(binary)
        return out


    def format_alias(self, name, command):
        if name is not None:
            if self.prefs['indicator_alias'] != '':
                return self.prefs['indicator_alias'] + ' ' + self.prefs['alias_display_format'].format(name=name, command=command)
            else:
                return self.prefs['alias_display_format'].format(name=name, command=command)
        else:
            if self.prefs['indicator_alias'] != '':
                return self.prefs['indicator_alias'] + ' ' + command
            else:
                return command

    def scan_applications(self):
        paths = self.system_path()
        applications = []
        for app_path in self.application_paths():
            for filename in os.listdir(app_path):
                pathname = os.path.join(app_path,filename)
                if os.path.isfile(pathname):
                    # Open the application file using the system's preferred encoding (probably utf-8)
                    with codecs.open(pathname,'r',encoding=system_encoding, errors='ignore') as f:
                        name = None
                        name_generic = None
                        command = None
                        terminal = None
                        for line in f.readlines():
                            if line[0:5] == 'Exec=' and command is None:
                                command_tmp = line[5:-1].split()
                                command = ''
                                space = ''
                                for piece in command_tmp:
                                    if piece.find('%') == -1:
                                        command += space + piece
                                        space = ' '
                                    else:
                                        break
                            elif line[0:5] == 'Name=' and name is None:
                                name = line[5:-1]
                            elif line[0:12] == 'GenericName=' and name_generic is None:
                                name_generic = line[12:-1]
                            elif line[0:9] == 'Terminal=' and terminal is None:
                                if line[9:-1].lower() == 'true':
                                    terminal = True
                                else:
                                    terminal = False

                        if name is not None and command is not None:
                            if terminal is None:
                                terminal = False
                            if name_generic is None:
                                name_generic = name
                            for path in paths:
                                if command[0:len(path)] == path:
                                    if command[len(path)+1:].find('/') == -1:
                                        command = command[len(path)+1:]

                            applications.append({
                                                'name': name,
                                                'name_generic': name_generic,
                                                'command': command,
                                                'terminal': terminal,
                                                'descriptor': filename.replace('.desktop','')
                                                })

        return applications


    def retrieve_aliased_command(self, alias):
        """
        Return the command intended to be executed by the given alias.
        """
        aliases = self.load_json(file_cache_aliasesLookup)
        if self.debug:
            print("Converting '" + str(alias) + "' into its aliased command")

        for item in aliases:
            if item[0] in alias:
                if self.debug:
                    print("Converted " + alias + " to: " + item[1])
                return item[1]
        if self.debug:
            print("No suitable candidate was found")


    def plugins_available(self):
        self.load_preferences()
        if self.debug:
            print('Loading available plugins...')

        plugins = self.get_plugins(True)
        plugin_titles = []
        for plugin in plugins:
            if hasattr(plugin['plugin'], 'is_submenu') and plugin['plugin'].is_submenu:
                plugin_titles.append(self.prefs['indicator_submenu'] + ' ' + plugin['plugin'].title)
            else:
                plugin_titles.append(plugin['plugin'].title)

        if self.debug:
            print('Done!')
            print('Plugins loaded:')
            print('First 5 items: ')
            print(plugin_titles[:5])
            print(str(len(plugin_titles)) + ' loaded in total')
            print('')

        out = self.sort_shortest(plugin_titles)
        self.cache_save(out, file_cache_plugins)
        return out


    def try_remove(self, needle, haystack):
        """
        Gracefully try to remove an item from an array. It not found, fire no
        errors. This is a convenience function to reduce code size.
        """
        try:
            haystack.remove(needle)
        except ValueError:
            pass


    def parse_alias_file(self, path):
        out = []
        with open(path.replace('~', os.path.expanduser('~')), 'r') as f:
            if self.debug:
                print('Opening alias file')
            for line in f.readlines():
                if line[:6].lower() == 'alias ':
                    parts = line[6:].replace('\n','').replace('\'','').replace('"','').split('=')
                    out.append([parts[0], parts[1]])
        return out


    def cache_build(self):
        self.load_preferences()

        if self.debug:
            if scandir_present:
                print("Optimised directory scanning library (scandir) loaded")
            else:
                print("Cound not load optimised directory scanning library (scandir)")
                print("Consider installing scandir: pip install scandir")

        valid_extensions = []
        if 'valid_extensions' in self.prefs:
            for extension in self.prefs['valid_extensions']:
                if extension == '*':
                    valid_extensions = True
                    break
                elif extension == '':
                    valid_extensions.append('')
                elif extension[0] != '.':
                    extension = '.' + extension
                valid_extensions.append(extension.lower())

        applications = []

        # Holds what binaries have been found
        binaries = []

        # Holds the directly searchable "# Htop (htop;)" lines
        aliased_items = []

        # Holds the [command, name] pairs for future lookup
        aliases = []

        # If we're going to include the applications or we want them for
        # filtering purposes, scan the .desktop files and get the applications
        if self.prefs['include_applications'] or self.prefs['filter_binaries']:
            applications = self.scan_applications()

        # Do we want to add binaries into the cache?
        if self.prefs['include_binaries'] is True:
            if self.prefs['filter_binaries'] is True:
                binaries_raw = self.scan_binaries()
                filterlist = [x['command'] for x in applications] + [x['descriptor'] for x in applications]
                for item in filterlist:
                    if item in binaries_raw:
                        binaries.append(item)
            else:
                binaries = self.scan_binaries()

        binaries = list(set(binaries))

        # Do we want to add applications from .desktop files into the cache?
        if self.prefs['include_applications']:
            if self.prefs['alias_applications']:
                if os.path.exists(file_cache_aliases):
                    os.remove(file_cache_aliases)
                for app in applications:
                    command = app['command']
                    if app['terminal']:
                        command += ';'
                    title = self.format_alias(app['name'], command)
                    # Only add this item if an item with the same name has not already been added
                    if title not in aliased_items:
                        aliased_items.append(title)
                        aliases.append([title, command])
                        if app['terminal']:
                            # Remove any non-terminal invoking versions from cache
                            self.try_remove(app['command'], binaries)
                            self.try_remove(app['command'].lower(), binaries)
                            self.try_remove(command, binaries)
                            self.try_remove(command.lower(), binaries)
            else:
                for app in applications:
                    command = app['command']
                    # Add the "run in terminal" indicator to the command
                    if app['terminal']:
                        command += ';'
                    # Only add this item if an item with the same name has not already been added
                    if command not in binaries:
                        # Remove any non-terminal invoking versions from cache
                        if app['terminal']:
                            self.try_remove(app['command'], binaries)
                            self.try_remove(app['command'].lower(), binaries)
                            self.try_remove(command, binaries)
                            self.try_remove(command.lower(), binaries)
                        binaries.append(command)

        binaries = list(set(binaries))

        watch_folders = []
        if 'watch_folders' in self.prefs:
            watch_folders = self.prefs['watch_folders']
        watch_folders = map(lambda x: x.replace('~', os.path.expanduser('~')), watch_folders)

        if self.debug:
            print('Done!')
            print('Watch folders:')
            print('Loading the list of folders to be excluded from the index...')

        ignore_folders = []

        if 'ignore_folders' in self.prefs:
            for exclude_folder in self.prefs['ignore_folders']:
                ignore_folders.append(exclude_folder.replace('~', os.path.expanduser('~')))

        if self.debug:
            print('Done!')
            print('Excluded folders:')
            print('First 5 items: ')
            print(ignore_folders[:5])
            print(str(len(ignore_folders)) + ' ignore_folders loaded in total')
            print('')

        filenames = []
        foldernames = []

        follow_symlinks = False
        try:
            if 'follow_symlinks' in self.prefs:
                follow_symlinks = self.prefs['follow_symlinks']
        except:
            pass

        if self.debug:
            if follow_symlinks:
                print('Indexing will not follow linked folders')
            else:
                print('Indexing will follow linked folders')

            print('Scanning files and folders, this may take a while...')

        for watchdir in watch_folders:
            for root, dirs, files in walk(watchdir, topdown=True, followlinks=follow_symlinks):
                dirs[:] = [d for d in dirs if os.path.join(root,d) not in ignore_folders]
                if self.prefs['scan_hidden_folders'] == False:
                    dirs[:] = [d for d in dirs if d.startswith('.') == False]

                if self.prefs['scan_hidden_folders'] or root.find('/.')  == -1:
                    for name in files:
                        if self.prefs['include_hidden_files'] or name.startswith('.') == False:
                            if valid_extensions == True or os.path.splitext(name)[1].lower() in valid_extensions:
                                filenames.append(os.path.join(root,name))
                    for name in dirs:
                        foldernames.append(os.path.join(root,name) + '/')

        foldernames = list(filter(lambda x: x not in ignore_folders, foldernames))

        include_items = []

        if 'include_items' in self.prefs:
            include_items = []
            for item in self.prefs['include_items']:
                if type(item) == list:
                    if len(item) > 1:
                        aliased_items.append(self.format_alias(item[0], item[1]))
                        aliases.append([item[0], item[1]])
                    else:
                        if self.debug:
                            print("There are aliased items in the configuration with no command.")
                else:
                    include_items.append(item)
        else:
            include_items = []

        # Remove any manually added include items differing by a colon
        # e.g. ["htop", "htop;"] becomes just ["htop;"]
        for item in include_items:
            if item[-1] == ';' and item[0:-1] in binaries:
                binaries.remove(item[0:-1])

        # Look for alias file and include
        if 'path_aliasFile' in self.prefs:
            if self.prefs['path_aliasFile'] != "":
                items = self.parse_alias_file(self.prefs['path_aliasFile'])
                for item in items:
                    title = self.format_alias(item[0], item[1])
                    aliased_items.append(title)
                    aliases.append([title, item[1]])

        plugins = self.plugins_available()

        # Save the alias lookup file and aliased_items
        self.save_json(file_cache_aliasesLookup, aliases)
        self.cache_save(aliased_items, file_cache_aliases)
        self.cache_save(binaries, file_cache_binaries)
        self.cache_save(foldernames, file_cache_folders)
        self.cache_save(filenames, file_cache_files)

        other = self.sort_shortest(include_items + aliased_items + binaries + foldernames + filenames)

        if 'exclude_items' in self.prefs:
            for item in self.prefs['exclude_items']:
                try:
                    other.remove(item)
                except ValueError:
                    pass

        other += ['rebuild cache']
        self.cache_save(other, file_cache)

        out = plugins
        out += other

        if self.debug:
            print('Done!')
            print('Cache building has finished.')
            print('')

        return out


class extension(dmenu):

    title = 'Settings'
    is_submenu = True

    def __init__(self):
        self.load_preferences()

    plugins_index_url = 'https://raw.githubusercontent.com/markjones112358/dmenu-extended-plugins/master/plugins_index.json'

    def rebuild_cache(self):
        time_start = time.time()
        if self.debug:
            print('Counting items in original cache')

        cacheSize = len(self.cache_load().split("\n"))

        if self.debug:
            print('Rebuilding the cache...')
        result = self.cache_regenerate()
        if self.debug:
            print('Cache built')
            print('Counting items in new cache')
        newSize = len(self.cache_load().split("\n"))
        if self.debug:
            print('New cache size = ' + str(newSize))
        cacheSizeChange = newSize - cacheSize
        if self.debug:
            if cacheSizeChange != 0:
                print('This differs from original by ' + str(cacheSizeChange) + ' items')
            else:
                print('Cache size did not change')

        response = []
        if cacheSizeChange != 0:
            if cacheSizeChange == 1:
                status = 'one new item was added.'
            elif cacheSizeChange == -1:
                status = 'one item was removed.'
            elif cacheSizeChange > 0:
                status = str(cacheSizeChange) + ' items were added.'
            elif cacheSizeChange < 0:
                status = str(abs(cacheSizeChange)) + ' items were removed.'
            else:
                status = 'No new items were added'
            response.append('Cache updated successfully; ' + status)
            if result == 2:
                response.append('NOTICE: Performance issues were encountered while caching data')
        else:
            response.append('Cache rebuilt; its size did not change.')
        response.append("The cache contains {count} items and took {time} seconds to build.".format(count=cacheSize, time=round(time.time() - time_start,2)))

        self.menu(response)


    def rebuild_cache_plugin(self):
        self.plugins_loaded = self.get_plugins(True)
        self.cache_regenerate()


    def download_plugins(self):
        self.message_open('Downloading a list of plugins...')

        try:
            plugins = self.download_json(self.plugins_index_url)
        except:
            self.message_close()
            self.menu(["Error: Could not connect to plugin repository.",
                       "Please check your internet connection and try again."])
            sys.exit()

        items = []
        accept = []

        substitute = ('plugin_', '')

        installed_plugins = self.get_plugins()
        installed_pluginFilenames = []

        for tmp in installed_plugins:
            installed_pluginFilenames.append(tmp['filename'])


        for plugin in plugins:
            if plugin + '.py' not in installed_pluginFilenames:
                if "min_version" in plugins[plugin]:
                    if plugins[plugin]["min_version"] <= _version_:
                        items.append(plugin.replace(substitute[0], substitute[1]) + ' - ' + plugins[plugin]['desc'])
                        accept.append(True)
                    else:
                        items.append(plugin.replace(substitute[0], substitute[1]) + ' - Requires dmenu_extended >= v' + str(plugins[plugin]["min_version"]))
                        accept.append(False)

        self.message_close()

        if len(items) == 0:
            self.menu(['There are no new plugins to install'])
        else:
            item = substitute[0] + self.select(items, 'Install:')

            index = items.index(item[len(substitute[0]):])
            if accept[index]:

                if item != -1:
                    self.message_open("Downloading selected plugin...")
                    plugin_name = item.split(' - ')[0]
                    plugin = plugins[plugin_name]
                    fail = False
                    # Check for dependencies
                    if 'dependencies' in plugins[plugin_name]:
                        message = []
                        lookup = []
                        if 'external' in plugins[plugin_name]['dependencies']:
                            for depend in plugins[plugin_name]['dependencies']['external']:
                                line = ""
                                if depend['name'] in d.scan_binaries():
                                    pass
                                else:
                                    line = "External dependancy '" + depend['name'] + "' is MISSING."
                                    fail = True
                                    if 'url' in depend:
                                        line += " See " + depend['url'] + "."
                                        lookup.append(depend['url'])
                                    else:
                                        lookup.append(None)
                                    message.append(line)
                        if 'python' in plugins[plugin_name]['dependencies']:
                            for depend in plugins[plugin_name]['dependencies']['python']:
                                found = True
                                try:
                                    exec("import " + depend)
                                except:
                                    found = False
                                    fail = True
                                if found == False:
                                    message.append("Python library '" + depend + "' MISSING. Please install (python-"+depend+")")
                                    lookup.append('https://pypi.python.org/pypi/'+depend)
                        if fail:
                            self.message_close()
                            outcome = self.select(message, 'Message:', numeric=True)
                            if lookup[outcome] is not None:
                                d.open_url(lookup[outcome])

                    if fail:
                        self.message_close()
                        self.menu(['Plugin has missing dependencies and therefore was not installed'])                    
                    else:
                        plugin_source = self.download_text(plugin['url'])

                        with open(path_plugins + '/' + plugin_name + '.py', 'w') as f:
                            for line in plugin_source:
                                f.write(line)

                        self.get_plugins(True)
                        self.message_close()
                        self.message_open("Rebuilding plugin cache")
                        self.plugins_available()
                        self.message_close()

                        self.menu(['Plugin downloaded and installed successfully'])

                        if self.debug:
                            print("Plugins available:")
                            for plugin in self.plugins_available():
                                print(plugin)
            else:
                self.menu(['The selected plugin cannot be installed as it requires a newer version of dmenu-extended'])


    def installed_plugins(self):
        plugins = []
        for plugin in self.get_plugins():
            if plugin["filename"] != "plugin_settings.py":
                plugins.append(plugin["plugin"].title.replace(':','') + ' (' + plugin["filename"] + ')')
        return plugins


    def remove_plugin(self):
        plugins = self.installed_plugins()
        pluginText = self.select(plugins, prompt='Plugin to remove:')
        if pluginText != -1:
            plugin = pluginText.split('(')[1].replace(')', '')
            path = path_plugins + '/' + plugin
            if os.path.exists(path):
                os.remove(path)
                self.menu(['Plugin "' + plugin + '" was removed.'])
                if self.debug:
                    print("Plugins available:")
                    for plugin in self.plugins_available():
                        print(plugin)
                else:
                    self.plugins_available()
            else:
                if self.debug:
                    print('Error - Plugin not found')
        else:
            if self.debug:
                print('Selection was not understood')


    def update_plugins(self):
        self.message_open('Checking for plugin updates...')
        plugins_here = list(map(lambda x: x['filename'].split('.')[0], self.get_plugins()))
        plugins_here.remove('plugin_settings')
        plugins_there = self.download_json(self.plugins_index_url)
        updated = []
        for here in plugins_here:
            for there in plugins_there:
                if there == here:
                    there_sha = plugins_there[there]['sha1sum']
                    here_sha = self.command_output("sha1sum " + path_plugins + '/' + here + '.py')[0].split()[0]
                    if self.debug:
                        print('Checking ' + here)
                        print('Local copy has sha of ' + here_sha)
                        print('Remote copy has sha of ' + there_sha)
                    if there_sha != here_sha:
                        sys.stdout.write("Hashes do not match, updating...\n")
                        if os.path.exists('/tmp/' + there + '.py'):
                            os.remove('/tmp/' + there + '.py')
                        os.system('wget ' + plugins_there[there]['url'] + ' -P /tmp')
                        download_sha = self.command_output("sha1sum /tmp/" + here + '.py')[0].split()[0]
                        if download_sha != there_sha:
                            if self.debug:
                                print('Downloaded version of ' + there + ' does not verify against package manager sha1sum key')
                                print('SHA1SUM of downloaded version = ' + download_sha)
                                print('SHA1SUM specified by package manager = ' + there_sha)
                                print('Plugin not updated')
                        else:
                            os.remove(path_plugins + '/' + here + '.py')
                            os.system('mv /tmp/' + here + '.py ' + path_plugins + '/' + here + '.py')
                            if self.debug:
                                print('Done!')
                            updated += [here]
                    else:
                        if self.debug:
                            print(here + 'is up-to-date')
        self.message_close()
        if len(updated) == 0:
            self.menu(['There are no new updates for installed plugins'])
        elif len(updated) == 1:
            self.menu([updated[0] + ' was updated to the latest version'])
        else:
            self.menu(['The following plugins were updated:'] + updated)


    # Returns 0 if no systemd or script not installed, 1 if running, 2 if not running
    def get_automatic_rebuild_cache_status(self):
        has_systemd = subprocess.call(['which', 'systemctl'])
        if has_systemd != 0:
            return 0
        subprocess.call(['systemctl', '--user', 'daemon-reload'])
        has_service = subprocess.check_output(['systemctl', '--user', 'list-unit-files', \
                'update-dmenu-extended-db.timer'])
        if 'update-dmenu-extended-db.timer' not in str(has_service):
            return 0
        is_enabled = subprocess.call(['systemctl', '--user', 'is-enabled', 'update-dmenu-extended-db.timer'])
        if is_enabled == 0:
            return 1
        else:
            return 2


    # These two methods presume that we have systemd and the scripts are installed.
    def enable_automatic_rebuild_cache(self):
        subprocess.call(['systemctl', '--user', 'enable', 'update-dmenu-extended-db.timer'])
        subprocess.call(['systemctl', '--user', 'start', 'update-dmenu-extended-db.timer'])
        self.menu(['Successfully enabled systemd service.'])


    def disable_automatic_rebuild_cache(self):
        subprocess.call(['systemctl', '--user', 'stop', 'update-dmenu-extended-db.timer'])
        subprocess.call(['systemctl', '--user', 'disable', 'update-dmenu-extended-db.timer'])
        self.menu(['Successfully disabled systemd service.'])

    def edit_preferences(self):
        self.open_file(file_prefs)
        self.plugins_available() # Refresh the plugin cache

    def run(self, inputText):
        options = [
            'Rebuild cache',
            self.prefs['indicator_submenu'] + ' Download new plugins',
            self.prefs['indicator_submenu'] + ' Remove existing plugins',
            'Update installed plugins',
            'Edit menu preferences',
            'Disable automatic cache rebuilding',
            'Enable automatic cache rebuilding',
        ]

        actions = [
            self.rebuild_cache,
            self.download_plugins,
            self.remove_plugin,
            self.update_plugins,
            self.edit_preferences,
            self.disable_automatic_rebuild_cache,
            self.enable_automatic_rebuild_cache
        ]

        # Build list of available options
        items = [
            options[0],
            options[1]
        ]

        num_plugins_installed = len(self.installed_plugins())
        
        # Add option to remove existing plugins and update existing plugins
        if num_plugins_installed > 0:
            items += [options[2]]
            items += [options[3]]

        # Add option to edit menu preferences
        items += [options[4]]

        # Check to see whether systemd integration is available and add
        automatic_rebuild_status = self.get_automatic_rebuild_cache_status()
        if automatic_rebuild_status != 0:
            if automatic_rebuild_status == 1:
                items += [options[5]]
            else:
                items += [options[6]]

        item = self.select(items, "Action:")
        if item != -1:
            index = options.index(item)
            if index != -1:
                actions[index]()


def is_binary(d, path):
    if os.path.isfile(path) == False:
        return False
    if os.access(path, os.X_OK) == False:
        return False
    for extension in d.prefs['valid_extensions']:
        if path[-len(extension)-1:] == '.' + extension:
            return False
    return True


def handle_command(d, out):
    if out.find('~') != -1:
        out = os.path.expanduser(out)
        if d.debug:
            print("Tilda found, expanding to " + str(out))
    if out[-1] == ';':
        terminal_hold = False
        out = out[:-1]
        if out[-1] == ';':
            terminal_hold = True
            out = out[:-1]
        if d.debug:
            print("Input will be treated as a terminal command")
            if terminal_hold:
                print("Terminal will be held open upon command finishing")
            print("Command is: " + str(out))
        if os.path.isdir(out):
            if d.debug:
                print("This is a path so will open it in the terminal")
            d.open_terminal("cd " + out + " && " + d.prefs['terminal'] + " &", direct=True)
        else:
            d.open_terminal(out, hold=terminal_hold)
    elif out.find('/') != -1:
        if d.debug:
            print("Item has forward slashes, interpret as a path or url")
        # Check if this is a url and launch as such
        if out[:7] == 'http://' or out[:8] == 'https://':
            if d.debug:
                print("Starts with http..., execute as a url")
            d.open_url(out)
        # Check if this is a binary file, with execute permissions, if so, run it.
        elif is_binary(d, out):
            if d.debug:
                print("Item found in binaries, execute its binary")
            d.execute(out)
        elif out.find(' ') != -1:
            if d.debug:
                print("Item contained spaces so is likely a binary acting on x")
            parts = out.split(' ')
            if parts[0] in d.scan_binaries():
                if d.debug:
                    print("Found the binary, executing the command")
                d.execute(out)
            else:
                if d.debug:
                    print("Binary not found, must be a path or file")
                if os.path.isdir(out):
                    d.open_directory(out)
                else:
                    d.open_file(out)
        else:
            if d.debug:
                print("Item assumed not to be a URL or binary")
            if os.path.isdir(out):
                if d.debug:
                    print("Checked item and found it to be a directory, opening as such")
                d.open_directory(out)
            else:
                if d.debug:
                    print("Checked item and found it to be a file, opening as such")
                d.open_file(out)
    else:
        if d.debug:
            print("Executing user input as a command")
        d.execute(out)


def run(*args):
    launch_args = list(args[1:])

    if '--debug' in launch_args:
        d.debug = True
        launch_args.remove('--debug')
        print('Debugging enabled')
        print('Launch arguments: ' + str(launch_args))

    d.launch_args = launch_args
    d.load_preferences()
    cache = d.cache_load()
    prompt = d.prefs['prompt']
    out = d.menu(cache,prompt).strip()
    aliased = False

    if len(out) > 0:
        if d.debug:
            print("First menu closed with user input: " + out)
        # Check if the action relates to a plugin
        plugins = load_plugins(d.debug)
        plugin_hook = False
        for plugin in plugins:
            if hasattr(plugin['plugin'], 'is_submenu') and plugin['plugin'].is_submenu == True:
                pluginTitle = d.prefs['indicator_submenu'] + ' ' + plugin['plugin'].title.strip()
            else:
                pluginTitle = plugin['plugin'].title.strip()

            if out[:len(pluginTitle)] == pluginTitle:
                plugin_hook = (plugin["plugin"], pluginTitle)

        # Check for plugin call
        if plugin_hook != False:
            plugin_hook[0].load_preferences()
            plugin_hook[0].run(out[len(plugin_hook[1]):].strip())
            if d.debug:
                print("This command refers to a plugin")
        else:
            if d.debug:
                print("This command is not related to a plugin")
            # Check to see if the command is an alias for something
            if d.retrieve_aliased_command(out) is not None:
                # If the user wants frequently used items, store this execution (before de-aliasing)
                if d.prefs['frequently_used'] > 0:
                    frequent_commands_store(out)
                out = d.retrieve_aliased_command(out)
                aliased = True
            else:
                # Check for store modifications
                # Dont allow command aliases that add new commands
                if out[0] in "+-":
                    action = out[0]
                    out = out[1:]

                    # tmp is used to split the input into a command and alias (if any)
                    tmp = out.split('#')

                    command = tmp[0]
                    if len(tmp) > 1:
                        alias = ' '.join(tmp[1:]).lstrip().rstrip()
                    else:
                        alias = None

                    if d.debug:
                        print("out = '" + str(out) + "'")
                        print("tmp = '" + str(tmp) + "'")
                        print("action = '" + str(action) + "'")
                        print("command = '" + str(command) + "'")
                        print("alias '= " + str(alias) + "'")

                    # Check to see if the item is in the include_items list
                    found_in_store = False
                    if d.debug:
                        print("Command = '" + str(command) + "', alias = '" + str(alias) + "'")
                        print("Starting to match given command with store elements")

                    for item in d.prefs['include_items']:
                        if action == '+' and type(item) == list:
                            if d.debug:
                                print("Is (+) " + str(item[0]) + " == " + str(alias) + "?")
                            if alias == item[0]:
                                if d.debug:
                                    print("Yes")
                                found_in_store = True
                                break
                            elif d.debug:
                                print("No")

                        # If removing a command - an alias would be detected as a command
                        if action == '-' and type(item) == list:
                            if d.debug:
                                print("Is (-) " + str(d.format_alias(item[0], item[1])) + " == " + str(command) + "?")
                            if command == d.format_alias(item[0], item[1]):
                                found_in_store = True
                                alias = command
                                if d.prefs['indicator_alias'] != '':
                                    alias = alias[len(d.prefs['indicator_alias'])+1:]
                                command = item[1]
                                if d.debug:
                                    print("Yes")
                                    print("Command is now: " + str(command))
                                    print("Alias is now: " + str(alias))
                                break
                            elif d.debug:
                                print("No")

                            if d.debug:
                                print("Is (-) " + str(d.format_alias(item[0], item[1])) + " == " + str(out) + "?")
                            if out == d.format_alias(item[0], item[1]):
                                found_in_store = True
                                alias = item[0]
                                if d.prefs['indicator_alias'] != '':
                                    alias = alias[len(d.prefs['indicator_alias'])+1:]
                                command = item[1]
                                if d.debug:
                                    print("Yes")
                                    print("Command is now: " + str(command))
                                    print("Alias is now: " + str(alias))
                                break
                            elif d.debug:
                                print("No")

                            if d.debug:
                                print("Is (-) " + str(item[0]) + " == " + str(command) + "?")
                            if command == item[0]:
                                found_in_store = True
                                alias = item[0]
                                if d.prefs['indicator_alias'] != '':
                                    alias = alias[len(d.prefs['indicator_alias'])+1:]
                                command = item[1]
                                if d.debug:
                                    print("Yes")
                                    print("Command is now: " + str(command))
                                    print("Alias is now: " + str(alias))
                                break
                            elif d.debug:
                                print("No")

                        if type(item) != list:
                            if d.debug:
                                print("Is " + str(item) + " == " + str(command) + "?")
                            if command == item:
                                if d.debug:
                                    print("Yes")
                                found_in_store = True
                                break
                            elif d.debug:
                                print("No")

                    if action == '+' and found_in_store == True:
                        option = d.prefs['indicator_submenu'] + " Remove from store"
                        if alias is None:
                            answer = d.menu("Command '" + str(command) + "' already in store\n"+option)
                        else:
                            answer = d.menu("Alias '" + str(alias) + "' already in store\n"+option)
                        if answer != option:
                            sys.exit()
                        action = '-'
                    elif action == '-' and found_in_store == False:
                        option = d.prefs['indicator_submenu'] + " Add to store"
                        if alias is None:
                            answer = d.menu("Command '" + str(command) + "' was not found in store\n"+option)
                        else:
                            answer = d.menu("Alias '" + str(alias) + "' was not found in store\n"+option)
                        if answer != option:
                            sys.exit()
                        action = '+'

                    cache_scanned = d.cache_open(file_cache)[:-1]

                    if cache_scanned == False:
                        d.cache_regenerate()
                        d.message_close()
                        sys.exit()
                    else:
                        cache_scanned = cache_scanned.split("\n")

                    if action == '+':

                        if alias is None:
                            if d.debug:
                                print("Adding '" + str(command) + "' to store")
                            d.prefs['include_items'].append(command)
                            d.message_open("Adding item to store: " + str(command))
                            cache_scanned = [command] + cache_scanned
                        else:
                            if d.debug:
                                print("Adding aliased command '" + str([alias, command]) + "' to store")
                            d.prefs['include_items'].append([alias, command])

                            # And add the item to the alias lookup file
                            aliases = d.load_json(file_cache_aliasesLookup)
                            if [alias, command] not in aliases:
                                aliases.append([alias, command])
                                d.save_json(file_cache_aliasesLookup, aliases)

                            d.message_open("Adding aliased item item to store: " + str(d.format_alias(alias, command)))
                            cache_scanned = [d.format_alias(alias, command)] + cache_scanned

                        cache_scanned.sort(key=len)
                    elif action == '-':
                        if alias is None:
                            if d.debug:
                                print("Will try to remove command: '" + str(command) + "' from the included items")
                            d.prefs['include_items'].remove(command)
                            d.message_open("Removing item from store: " + str(command))
                            try:
                                cache_scanned.remove(command)
                            except ValueError:
                                if d.debug:
                                    print("Couldnt remove item from the cache")
                                else:
                                    pass
                        else:
                            to_remove = None
                            for item in d.prefs['include_items']:
                                if item[0] == alias:
                                    to_remove = item
                            if to_remove is not None:
                                if d.debug:
                                    print("Item found and is")
                                    print(to_remove)
                                d.prefs['include_items'].remove(to_remove)
                            else:
                                if d.debug:
                                    print("Couldn't remove the item (item could not be located)")

                            d.message_open("Removing aliased item from store: " + str(d.format_alias(alias, command)))
                            try:
                                cache_scanned.remove(d.format_alias(alias, command))
                            except ValueError:
                                if d.debug:
                                    print("Couldnt remove item from the cache")
                                else:
                                    pass
                    else:
                        d.message_close()
                        d.menu("An error occured while servicing your request.\nYou may need to delete your configuration file.")
                        sys.exit()

                    d.save_preferences()
                    d.cache_save(cache_scanned, file_cache)
                    d.message_close()

                    # Give the user some feedback
                    if action == '+':
                        if alias is None:
                            message = "New item (" + command + ") added to cache."
                        else:
                            message = "New item (" + command + " aliased as '" + alias + "') added to cache."
                    else:
                        if alias is None:
                            message = "Existing item (" + command + ") removed from cache."
                        else:
                            message = "Existing alias (" + alias + ") removed from cache."

                    d.menu(message)
                    sys.exit()

                else:
                    # If the user wants frequently used items, store this execution
                    if d.prefs['frequently_used'] > 0:
                        frequent_commands_store(out)

            # Detect if the command is a web address and pass to handle_command
            if out[:7] == 'http://' or out[:8] == 'https://' or aliased == True:
                handle_command(d, out)
            elif out.find(':') != -1:
                print(out)
                tmp = out.split(':')
                if len(tmp) != 2:
                    if d.debug:
                        print('Input command not understood')
                    sys.exit()
                else:
                    cmds = list(map(lambda x: x.strip(), tmp))

                run_withshell = False
                shell_hold = False
                if cmds[0][-1] == ';':
                    if cmds[0][-2] == ';':
                        shell_hold = True
                        if d.debug:
                            print('Will hold')
                    else:
                        if d.debug:
                            print('Wont hold')
                    cmds[0] = cmds[0].replace(';','')
                    run_withshell = True

                if cmds[0] == '':
                    items = list(filter(lambda x: x.find(cmds[1]) != -1, cache.split('\n')))
                    item = d.menu(items)
                    handle_command(d, item)
                elif cmds[0] in d.scan_binaries():
                    if d.debug:
                        print('Item[0] (' + cmds[0] + ') found in binaries')
                    # Get paths from cache
                    items = list(filter(lambda x: x.find('/') != -1, cache.split('\n')))
                    # If extension passed, filter by this
                    if cmds[1] != '':
                        items = list(filter(lambda x: x.find(cmds[1]) != -1, items))
                    filename = d.menu(items)
                    filename = os.path.expanduser(filename)
                    command = cmds[0] + " '" + filename + "'"

                    if run_withshell:
                        d.open_terminal(command, shell_hold)
                    else:
                        d.execute(command)
                elif cmds[0].find('/') != -1:
                    # Path came first, assume user wants of open it with a bin
                    if cmds[1] != '':
                        command = cmds[1] + " '" + os.path.expanduser(cmds[0]) + "'"
                    else:
                        binary = d.menu(d.scan_binaries())
                        command = binary + " '" + os.path.expanduser(cmds[0]) + "'"

                    d.execute(command)
                else:
                    d.menu(["Cant find " + cmds[0] + ", is it installed?"])
                    if d.debug:
                        print('Input command not understood')
                sys.exit()

            elif out == "rebuild cache":
                result = d.cache_regenerate()
                if result == 0:
                    d.menu(['Cache could not be saved'])
                elif result == 2:
                    d.menu(['Cache rebuilt','Performance issues were detected - some paths contained invalid characters'])
                else:
                    d.menu(['Success!'])

            else:
                handle_command(d, out)

d = dmenu()

if __name__ == "__main__":
    run(*sys.argv)
