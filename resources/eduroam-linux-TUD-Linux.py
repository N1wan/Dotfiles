#!/usr/bin/env python3
"""
 * **************************************************************************
 * Contributions to this work were made on behalf of the GÉANT project,
 * a project that has received funding from the European Union’s Framework
 * Programme 7 under Grant Agreements No. 238875 (GN3)
 * and No. 605243 (GN3plus), Horizon 2020 research and innovation programme
 * under Grant Agreements No. 691567 (GN4-1) and No. 731122 (GN4-2).
 * On behalf of the aforementioned projects, GEANT Association is
 * the sole owner of the copyright in all material which was developed
 * by a member of the GÉANT project.
 * GÉANT Vereniging (Association) is registered with the Chamber of
 * Commerce in Amsterdam with registration number 40535155 and operates
 * in the UK as a branch of GÉANT Vereniging.
 *
 * Registered office: Hoekenrode 3, 1102BR Amsterdam, The Netherlands.
 * UK branch address: City House, 126-130 Hills Road, Cambridge CB2 1PQ, UK
 *
 * License: see the web/copyright.inc.php file in the file structure or
 *          <base_url>/copyright.php after deploying the software

Authors:
    Tomasz Wolniewicz <twoln@umk.pl>
    Michał Gasewicz <genn@umk.pl> (Network Manager support)

Contributors:
    Steffen Klemer https://github.com/sklemer1
    ikreb7 https://github.com/ikreb7
    Dimitri Papadopoulos Orfanos https://github.com/DimitriPapadopoulos
    sdasda7777 https://github.com/sdasda7777
Many thanks for multiple code fixes, feature ideas, styling remarks
much of the code provided by them in the form of pull requests
has been incorporated into the final form of this script.

This script is the main body of the CAT Linux installer.
In the generation process configuration settings are added
as well as messages which are getting translated into the language
selected by the user.

The script runs under python3.

"""
import argparse
import base64
import getpass
import os
import platform
import re
import subprocess
import sys
import uuid
from shutil import copyfile
from typing import List, Type, Union

NM_AVAILABLE = True
NEW_CRYPTO_AVAILABLE = True
OPENSSL_CRYPTO_AVAILABLE = False
DEBUG_ON = False

parser = argparse.ArgumentParser(description='eduroam linux installer.')
parser.add_argument('--debug', '-d', action='store_true', dest='debug',
                    default=False, help='set debug flag')
parser.add_argument('--username', '-u', action='store', dest='username',
                    help='set username')
parser.add_argument('--password', '-p', action='store', dest='password',
                    help='set text_mode flag')
parser.add_argument('--silent', '-s', action='store_true', dest='silent',
                    help='set silent flag')
parser.add_argument('--pfxfile', action='store', dest='pfx_file',
                    help='set path to user certificate file')
parser.add_argument("--wpa_conf", action='store_true', dest='wpa_conf',
                    help='generate wpa_supplicant config file without configuring the system')
parser.add_argument("--gui", action='store', dest='gui',
                    help='one of: tty, tkinter, zenity, kdialog, yad - use this GUI system if present, falling back to standard choice if not')
ARGS = parser.parse_args()
if ARGS.debug:
    DEBUG_ON = True
    print("Running debug mode")


def debug(msg) -> None:
    """Print debugging messages to stdout"""
    if not DEBUG_ON:
        return
    print("DEBUG:" + str(msg))


def byte_to_string(barray: List) -> str:
    """conversion utility"""
    return "".join([chr(x) for x in barray])


debug(sys.version_info.major)

try:
    import dbus
except ImportError:
    print("WARNING: Cannot import the dbus module - please install dbus-python!")
    debug("Cannot import the dbus module")
    NM_AVAILABLE = False


try:
    from cryptography.hazmat.primitives.serialization import pkcs12
    from cryptography.hazmat.backends import default_backend
    from cryptography.x509.oid import NameOID
except ImportError:
    NEW_CRYPTO_AVAILABLE = False
    try:
        from OpenSSL import crypto
        crypto.load_pkcs12  # missing in newer versions
        OPENSSL_CRYPTO_AVAILABLE = True
    except (ImportError, AttributeError):  # AttributeError sometimes thrown by old/broken OpenSSL versions
        OPENSSL_CRYPTO_AVAILABLE = False


def detect_desktop_environment() -> str:
    """
    Detect what desktop type is used. This method is prepared for
    possible future use with password encryption on supported distros

    the function below was partially copied from
    https://ubuntuforums.org/showthread.php?t=1139057
    """
    desktop_environment = 'generic'
    if os.environ.get('KDE_FULL_SESSION') == 'true':
        desktop_environment = 'kde'
    elif os.environ.get('GNOME_DESKTOP_SESSION_ID'):
        desktop_environment = 'gnome'
    else:
        try:
            shell_command = subprocess.Popen(['xprop', '-root',
                                              '_DT_SAVE_MODE'],
                                             stdout=subprocess.PIPE,
                                             stderr=subprocess.PIPE)
            out, _ = shell_command.communicate()
            info = out.decode('utf-8').strip()
        except (OSError, RuntimeError):
            pass
        else:
            if ' = "xfce4"' in info:
                desktop_environment = 'xfce'
    return desktop_environment


def get_system() -> List:
    """
    Detect Linux platform. Not used at this stage.
    It is meant to enable password encryption in distros
    that can handle this well.
    """
    system = platform.system_alias(
        platform.system(),
        platform.release(),
        platform.version()
    )
    return [system, detect_desktop_environment()]


def get_config_path() -> str:
    """
    Return XDG_CONFIG_HOME path if exists otherwise $HOME/.config
    """

    xdg_config_home_path = os.environ.get('XDG_CONFIG_HOME')
    if not xdg_config_home_path:
        home_path = os.environ.get('HOME')
        return '{}/.config'.format(home_path)
    return xdg_config_home_path


def run_installer() -> None:
    """
    This is the main installer part. It tests for NM availability
    gets user credentials and starts a proper installer.
    """
    global ARGS
    global NM_AVAILABLE
    username = ''
    password = ''
    silent = False
    pfx_file = ''
    gui = ''
    wpa_conf = False

    if ARGS.username:
        username = ARGS.username
    if ARGS.password:
        password = ARGS.password
    if ARGS.silent:
        silent = ARGS.silent
    if ARGS.pfx_file:
        pfx_file = ARGS.pfx_file
    if ARGS.wpa_conf:
        wpa_conf = ARGS.wpa_conf
    if ARGS.gui:
        gui = ARGS.gui
    debug(get_system())
    debug("Calling InstallerData")
    installer_data = InstallerData(silent=silent, username=username,
                                   password=password, pfx_file=pfx_file, gui=gui)

    if wpa_conf:
        NM_AVAILABLE = False

    # test dbus connection
    if NM_AVAILABLE:
        config_tool = CatNMConfigTool()
        if config_tool.connect_to_nm() is None:
            NM_AVAILABLE = False
    if not NM_AVAILABLE and not wpa_conf:
        # no dbus so ask if the user will want wpa_supplicant config
        if installer_data.ask(Messages.save_wpa_conf, Messages.cont, 1):
            sys.exit(1)
    installer_data.get_user_cred()
    installer_data.save_ca()
    if NM_AVAILABLE:
        config_tool.add_connections(installer_data)
    else:
        wpa_config = WpaConf()
        wpa_config.create_wpa_conf(Config.ssids, installer_data)
    installer_data.show_info(Messages.installation_finished)


class Messages:
    """
    These are initial definitions of messages, but they will be
    overridden with translated strings.
    """
    quit = "Really quit?"
    credentials_prompt = "Please, enter your credentials:"
    username_prompt = "enter your userid"
    enter_password = "enter password"
    enter_import_password = "enter your import password"
    incorrect_password = "incorrect password"
    repeat_password = "repeat your password"
    passwords_differ = "passwords do not match"
    installation_finished = "Installation successful"
    cat_dir_exists = "Directory {} exists; some of its files may be " \
                     "overwritten."
    cont = "Continue?"
    nm_not_supported = "This NetworkManager version is not supported"
    cert_error = "Certificate file not found, looks like a CAT error"
    unknown_version = "Unknown version"
    dbus_error = "DBus connection problem, a sudo might help"
    ok = "OK"
    yes = "Y"
    nay = "N"
    p12_filter = "personal certificate file (p12 or pfx)"
    all_filter = "All files"
    p12_title = "personal certificate file (p12 or pfx)"
    save_wpa_conf = "NetworkManager configuration failed. " \
                    "Ensure you have the dbus-python package for your distro installed on your system. " \
                    "We may generate a wpa_supplicant configuration file " \
                    "if you wish. Be warned that your connection password will be saved " \
                    "in this file as clear text."
    save_wpa_confirm = "Write the file"
    wrongUsernameFormat = "Error: Your username must be of the form " \
                          "'xxx@institutionID' e.g. 'john@example.net'!"
    wrong_realm = "Error: your username must be in the form of 'xxx@{}'. " \
                  "Please enter the username in the correct format."
    wrong_realm_suffix = "Error: your username must be in the form of " \
                         "'xxx@institutionID' and end with '{}'. Please enter the username " \
                         "in the correct format."
    user_cert_missing = "personal certificate file not found"
    # "File %s exists; it will be overwritten."
    # "Output written to %s"


class Config:
    """
    This is used to prepare settings during installer generation.
    """
    instname = ""
    profilename = ""
    url = ""
    email = ""
    title = "eduroam CAT"
    servers = []
    ssids = []
    del_ssids = []
    eap_outer = ''
    eap_inner = ''
    use_other_tls_id = False
    server_match = ''
    anonymous_identity = ''
    CA = ""
    init_info = ""
    init_confirmation = ""
    tou = ""
    sb_user_file = ""
    verify_user_realm_input = False
    user_realm = ""
    hint_user_input = False


class InstallerData:
    """
    General user interaction handling, supports zenity, KDialog, yad and
    standard command-line interface
    """

    def __init__(self, silent: bool = False, username: str = '',
                 password: str = '', pfx_file: str = '', gui: str = '') -> None:
        self.graphics = ''
        self.username = username
        self.password = password
        self.silent = silent
        self.pfx_file = pfx_file
        if gui in ('tty', 'tkinter', 'yad', 'zenity', 'kdialog'):
            self.gui = gui
        else:
            self.gui = ''
        debug("starting constructor")
        if silent:
            self.graphics = 'tty'
        else:
            self.__get_graphics_support()
        self.show_info(Config.init_info.format(Config.instname,
                                               Config.email, Config.url))
        if self.ask(Config.init_confirmation.format(Config.instname,
                                                    Config.profilename),
                    Messages.cont, 1):
            sys.exit(1)
        if Config.tou != '':
            if self.ask(Config.tou, Messages.cont, 1):
                sys.exit(1)
        if os.path.exists(get_config_path() + '/cat_installer'):
            if self.ask(Messages.cat_dir_exists.format(
                    get_config_path() + '/cat_installer'),
                    Messages.cont, 1):
                sys.exit(1)
        else:
            os.mkdir(get_config_path() + '/cat_installer', 0o700)

    @staticmethod
    def save_ca() -> None:
        """
        Save CA certificate to cat_installer directory
        (create directory if needed)
        """
        certfile = get_config_path() + '/cat_installer/ca.pem'
        debug("saving cert")
        with open(certfile, 'w') as cert:
            cert.write(Config.CA + "\n")

    def ask(self, question: str, prompt: str = '', default: bool = None) -> int:
        """
        Prompt user for a Y/N reply, possibly supplying a default answer
        """
        if self.silent:
            return 0
        if self.graphics == 'tty':
            yes = Messages.yes[:1].upper()
            nay = Messages.nay[:1].upper()
            print("\n-------\n" + question + "\n")
            while True:
                tmp = prompt + " (" + Messages.yes + "/" + Messages.nay + ") "
                if default == 1:
                    tmp += "[" + yes + "]"
                elif default == 0:
                    tmp += "[" + nay + "]"
                inp = input(tmp)
                if inp == '':
                    if default == 1:
                        return 0
                    if default == 0:
                        return 1
                i = inp[:1].upper()
                if i == yes:
                    return 0
                if i == nay:
                    return 1
        elif self.graphics == 'tkinter':
            from tkinter import messagebox
            return 0 if messagebox.askyesno(Config.title, question + "\n\n" + prompt) else 1
        else:
            command = []
            if self.graphics == "zenity":
                command = ['zenity', '--title=' + Config.title, '--width=500',
                           '--question', '--text=' + question + "\n\n" + prompt]
            elif self.graphics == 'kdialog':
                command = ['kdialog', '--yesno', question + "\n\n" + prompt,
                           '--title=' + Config.title]
            elif self.graphics == 'yad':
                command = ['yad', '--image="dialog-question"',
                           '--button=gtk-yes:0',
                           '--button=gtk-no:1',
                           '--width=500',
                           '--wrap',
                           '--text=' + question + "\n\n" + prompt,
                           '--title=' + Config.title]
            returncode = subprocess.call(command, stderr=subprocess.DEVNULL)
            return returncode

    def show_info(self, data: str) -> None:
        """
        Show a piece of information
        """
        if self.silent:
            return
        if self.graphics == 'tty':
            print(data)
        elif self.graphics == 'tkinter':
            from tkinter import messagebox
            messagebox.showinfo(Config.title, data)
        else:
            if self.graphics == "zenity":
                command = ['zenity', '--info', '--width=500', '--text=' + data]
            elif self.graphics == "kdialog":
                command = ['kdialog', '--msgbox', data, '--title=' + Config.title]
            elif self.graphics == "yad":
                command = ['yad', '--button=OK', '--width=500', '--text=' + data]
            else:
                sys.exit(1)
            subprocess.call(command, stderr=subprocess.DEVNULL)

    def confirm_exit(self) -> None:
        """
        Confirm exit from installer
        """
        ret = self.ask(Messages.quit)
        if ret == 0:
            sys.exit(1)

    def alert(self, text: str) -> None:
        """Generate alert message"""
        if self.silent:
            return
        if self.graphics == 'tty':
            print(text)
        elif self.graphics == 'tkinter':
            from tkinter import messagebox
            messagebox.showwarning(Config.title, text)
        else:
            if self.graphics == 'zenity':
                command = ['zenity', '--warning', '--text=' + text]
            elif self.graphics == "kdialog":
                command = ['kdialog', '--sorry', text, '--title=' + Config.title]
            elif self.graphics == "yad":
                command = ['yad', '--text=' + text]
            else:
                sys.exit(1)
            subprocess.call(command, stderr=subprocess.DEVNULL)

    def prompt_nonempty_string(self, show: int, prompt: str, val: str = '') -> str:
        """
        Prompt user for input
        """
        if self.graphics == 'tty':
            if show == 0:
                while True:
                    inp = str(getpass.getpass(prompt + ": "))
                    output = inp.strip()
                    if output != '':
                        return output
            while True:
                inp = input(prompt + ": ")
                output = inp.strip()
                if output != '':
                    return output
        elif self.graphics == 'tkinter':
            from tkinter import simpledialog
            while True:
                output = simpledialog.askstring(Config.title, prompt,
                                                initialvalue=val,
                                                show="*" if show == 0 else "")
                if output:
                    return output

        else:
            command = []
            if self.graphics == 'zenity':
                if val == '':
                    default_val = ''
                else:
                    default_val = '--entry-text=' + val
                if show == 0:
                    hide_text = '--hide-text'
                else:
                    hide_text = ''
                command = ['zenity', '--entry', hide_text, default_val,
                           '--width=500', '--text=' + prompt]
            elif self.graphics == 'kdialog':
                if show == 0:
                    hide_text = '--password'
                else:
                    hide_text = '--inputbox'
                command = ['kdialog', hide_text, prompt, '--title=' + Config.title]
            elif self.graphics == 'yad':
                if show == 0:
                    hide_text = ':H'
                else:
                    hide_text = ''
                command = ['yad', '--form', '--field=' + hide_text,
                           '--text=' + prompt, val]

            output = ''
            while not output:
                shell_command = subprocess.Popen(command, stdout=subprocess.PIPE,
                                                 stderr=subprocess.PIPE)
                out, _ = shell_command.communicate()
                output = out.decode('utf-8')
                if self.graphics == 'yad':
                    output = output[:-2]
                output = output.strip()
                if shell_command.returncode == 1:
                    self.confirm_exit()
            return output

    def __get_username_password_atomic(self) -> None:
        """
        use single form to get username, password and password confirmation
        """
        output_fields_separator = "\n\n\n\n\n"
        while True:
            password = "a"
            password1 = "b"
            if self.graphics == 'tkinter':
                import tkinter as tk

                root = tk.Tk()
                root.title(Config.title)

                desc_label = tk.Label(root, text=Messages.credentials_prompt)
                desc_label.grid(row=0, column=0, columnspan=2, sticky=tk.W)

                username_label = tk.Label(root, text=Messages.username_prompt)
                username_label.grid(row=1, column=0, sticky=tk.W)

                username_entry = tk.Entry(root, textvariable=tk.StringVar(root, value=self.username))
                username_entry.grid(row=1, column=1)

                password_label = tk.Label(root, text=Messages.enter_password)
                password_label.grid(row=2, column=0, sticky=tk.W)

                password_entry = tk.Entry(root, show="*")
                password_entry.grid(row=2, column=1)

                password1_label = tk.Label(root, text=Messages.repeat_password)
                password1_label.grid(row=3, column=0, sticky=tk.W)

                password1_entry = tk.Entry(root, show="*")
                password1_entry.grid(row=3, column=1)

                def submit(installer):
                    def inner():
                        nonlocal password, password1
                        (installer.username, password, password1) = (username_entry.get(), password_entry.get(), password1_entry.get())
                        root.destroy()
                    return inner

                login_button = tk.Button(root, text=Messages.ok, command=submit(self))
                login_button.grid(row=4, column=0, columnspan=2)

                root.mainloop()
            else:
                if self.graphics == 'zenity':
                    command = ['zenity', '--forms', '--width=500',
                               f"--title={Config.title}",
                               f"--text={Messages.credentials_prompt}",
                               f"--add-entry={Messages.username_prompt}",
                               f"--add-password={Messages.enter_password}",
                               f"--add-password={Messages.repeat_password}",
                               "--separator", output_fields_separator]
                elif self.graphics == 'yad':
                    command = ['yad', '--form',
                               f"--title={Config.title}",
                               f"--text={Messages.credentials_prompt}",
                               f"--field={Messages.username_prompt}", self.username,
                               f"--field={Messages.enter_password}:H",
                               f"--field={Messages.repeat_password}:H",
                               "--separator", output_fields_separator]

                output = ''
                while not output:
                    shell_command = subprocess.Popen(command, stdout=subprocess.PIPE,
                                                     stderr=subprocess.PIPE)
                    out, _ = shell_command.communicate()
                    output = out.decode('utf-8')
                    if self.graphics == 'yad':
                        output = output[:-(len(output_fields_separator)+1)]
                    output = output.strip()
                    if shell_command.returncode == 1:
                        self.confirm_exit()

                if self.graphics in ('zenity', 'yad'):
                    self.username, password, password1 = output.split(output_fields_separator)

            if not self.__validate_user_name():
                continue
            if password != password1:
                self.alert(Messages.passwords_differ)
                continue
            self.password = password
            break

    def get_user_cred(self) -> None:
        """
        Get user credentials both username/password and personal certificate
        based
        """
        if Config.eap_outer in ('PEAP', 'TTLS'):
            self.__get_username_password()
        elif Config.eap_outer == 'TLS':
            self.__get_p12_cred()

    def __get_username_password(self) -> None:
        """
        read user password and set the password property
        do nothing if silent mode is set
        """
        if self.silent:
            return
        if self.graphics in ('tkinter', 'zenity', 'yad'):
            self.__get_username_password_atomic()
        else:
            password = "a"
            password1 = "b"
            if self.username:
                user_prompt = self.username
            elif Config.hint_user_input:
                user_prompt = '@' + Config.user_realm
            else:
                user_prompt = ''
            while True:
                self.username = self.prompt_nonempty_string(
                    1, Messages.username_prompt, user_prompt)
                if self.__validate_user_name():
                    break
            while password != password1:
                password = self.prompt_nonempty_string(
                    0, Messages.enter_password)
                password1 = self.prompt_nonempty_string(
                    0, Messages.repeat_password)
                if password != password1:
                    self.alert(Messages.passwords_differ)
            self.password = password

    def __check_graphics(self, command) -> bool:
        shell_command = subprocess.Popen(['which', command],
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)
        shell_command.wait()
        if shell_command.returncode == 0:
            self.graphics = command
            debug("Using "+command)
            return True
        return False

    def __get_graphics_support(self) -> None:
        self.graphics = 'tty'
        if self.gui == 'tty':
            return
        if os.environ.get('DISPLAY') is None:
            return
        if self.gui != 'tkinter':
            if self.__check_graphics(self.gui):
                return
            try:
                import tkinter
                self.graphics = 'tkinter'
                return
            except Exception:
                pass
            for cmd in ('yad', 'zenity', 'kdialog'):
                if self.__check_graphics(cmd):
                    return

    def __process_p12(self) -> bool:
        debug('process_p12')
        pfx_file = get_config_path() + '/cat_installer/user.p12'
        if NEW_CRYPTO_AVAILABLE:
            debug("using new crypto")
            try:
                p12 = pkcs12.load_key_and_certificates(
                                        open(pfx_file,'rb').read(),
                                        self.password, backend=default_backend())
            except Exception as error:
                debug("Incorrect password ({}).".format(error))
                return False
            else:
                if Config.use_other_tls_id:
                    return True
                try:
                    self.username = p12[1].subject.\
                        get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
                except crypto.Error:
                    self.username = p12[1].subject.\
                        get_attributes_for_oid(NameOID.EMAIL_ADDRESS)[0].value
                return True
        if OPENSSL_CRYPTO_AVAILABLE:
            debug("using openssl crypto")
            try:
                p12 = crypto.load_pkcs12(open(pfx_file, 'rb').read(),
                                         self.password)
            except crypto.Error as error:
                debug("Incorrect password ({}).".format(error))
                return False
            else:
                if Config.use_other_tls_id:
                    return True
                try:
                    self.username = p12.get_certificate(). \
                        get_subject().commonName
                except crypto.Error:
                    self.username = p12.get_certificate().\
                        get_subject().emailAddress
                return True
        debug("using openssl")
        command = ['openssl', 'pkcs12', '-in', pfx_file, '-passin',
                   'pass:' + self.password, '-nokeys', '-clcerts']
        shell_command = subprocess.Popen(command, stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)
        out, _ = shell_command.communicate()
        if shell_command.returncode != 0:
            debug("first password run failed")
            command1 = ['openssl', 'pkcs12', '-legacy', '-in', pfx_file, '-passin',
                        'pass:' + self.password, '-nokeys', '-clcerts']
            shell_command1 = subprocess.Popen(command1, stdout=subprocess.PIPE,
                                              stderr=subprocess.PIPE)
            out, err = shell_command1.communicate()
            if shell_command1.returncode != 0:
                return False
        if Config.use_other_tls_id:
            return True
        out_str = out.decode('utf-8').strip()
        # split only on commas that are not inside double quotes
        subject = re.split(r'\s*[/,]\s*(?=([^"]*"[^"]*")*[^"]*$)',
                           re.findall(r'subject=/?(.*)$',
                                      out_str, re.MULTILINE)[0])
        cert_prop = {}
        for field in subject:
            if field:
                cert_field = re.split(r'\s*=\s*', field)
                cert_prop[cert_field[0].lower()] = cert_field[1]
        if cert_prop['cn'] and re.search(r'@', cert_prop['cn']):
            debug('Using cn: ' + cert_prop['cn'])
            self.username = cert_prop['cn']
        elif cert_prop['emailaddress'] and \
                re.search(r'@', cert_prop['emailaddress']):
            debug('Using email: ' + cert_prop['emailaddress'])
            self.username = cert_prop['emailaddress']
        else:
            self.username = ''
            self.alert("Unable to extract username "
                       "from the certificate")
        return True

    def __select_p12_file(self) -> str:
        """
        prompt user for the PFX file selection
        this method is not being called in the silent mode
        therefore there is no code for this case
        """
        if self.graphics == 'tty':
            my_dir = os.listdir(".")
            p_count = 0
            pfx_file = ''
            for my_file in my_dir:
                if my_file.endswith(('.p12', '*.pfx', '.P12', '*.PFX')):
                    p_count += 1
                    pfx_file = my_file
            prompt = "personal certificate file (p12 or pfx)"
            default = ''
            if p_count == 1:
                default = '[' + pfx_file + ']'

            while True:
                inp = input(prompt + default + ": ")
                output = inp.strip()

                if default != '' and output == '':
                    return pfx_file
                default = ''
                if os.path.isfile(output):
                    return output
                print("file not found")

        cert = ""
        if self.graphics == 'zenity':
            command = ['zenity', '--file-selection',
                       '--file-filter=' + Messages.p12_filter +
                       ' | *.p12 *.P12 *.pfx *.PFX', '--file-filter=' +
                       Messages.all_filter + ' | *',
                       '--title=' + Messages.p12_title]
            shell_command = subprocess.Popen(command, stdout=subprocess.PIPE,
                                             stderr=subprocess.PIPE)
            cert, _ = shell_command.communicate()
        if self.graphics == 'kdialog':
            command = ['kdialog', '--getopenfilename', '.',
                       '--title=' + Messages.p12_title]
            shell_command = subprocess.Popen(command, stdout=subprocess.PIPE,
                                             stderr=subprocess.DEVNULL)
            cert, _ = shell_command.communicate()
        if self.graphics == 'yad':
            command = ['yad', '--file',
                       '--file-filter=*.p12 *.P12 *.pfx *.PFX',
                       '-file-filter=*', '--title=' + Messages.p12_title]
            shell_command = subprocess.Popen(command, stdout=subprocess.PIPE,
                                             stderr=subprocess.DEVNULL)
            cert, _ = shell_command.communicate()
        if self.graphics == 'tkinter':
            from tkinter import filedialog as fd
            return fd.askopenfilename(title=Messages.p12_title,
                                      filetypes=(("Certificate file",
                                                  ("*.p12", "*.P12", "*.pfx",
                                                   "*.PFX")),))
        return cert.decode('utf-8').strip()

    @staticmethod
    def __save_sb_pfx() -> None:
        """write the user PFX file"""
        cert_file = get_config_path() + '/cat_installer/user.p12'
        with open(cert_file, 'wb') as cert:
            cert.write(base64.b64decode(Config.sb_user_file))

    def __get_p12_cred(self):
        """get the password for the PFX file"""
        if Config.eap_inner == 'SILVERBULLET':
            self.__save_sb_pfx()
        else:
            if not self.silent:
                self.pfx_file = self.__select_p12_file()
            try:
                copyfile(self.pfx_file, get_config_path() +
                         '/cat_installer/user.p12')
            except (OSError, RuntimeError):
                print(Messages.user_cert_missing)
                sys.exit(1)
        if self.silent:
            username = self.username
            if not self.__process_p12():
                sys.exit(1)
            if username:
                self.username = username
        else:
            while not self.password:
                self.password = self.prompt_nonempty_string(
                    0, Messages.enter_import_password).encode('utf-8')
                if not self.__process_p12():
                    self.alert(Messages.incorrect_password)
                    self.password = ''
            if not self.username:
                self.username = self.prompt_nonempty_string(
                    1, Messages.username_prompt)

    def __validate_user_name(self) -> bool:
        # locate the @ character in username
        pos = self.username.find('@')
        debug("@ position: " + str(pos))
        # trailing @
        if pos == len(self.username) - 1:
            debug("username ending with @")
            self.alert(Messages.wrongUsernameFormat)
            return False
        # no @ at all
        if pos == -1:
            if Config.verify_user_realm_input:
                debug("missing realm")
                self.alert(Messages.wrongUsernameFormat)
                return False
            debug("No realm, but possibly correct")
            return True
        # @ at the beginning
        if pos == 0:
            debug("missing user part")
            self.alert(Messages.wrongUsernameFormat)
            return False
        pos += 1
        if Config.verify_user_realm_input:
            if Config.hint_user_input:
                if self.username.endswith('@' + Config.user_realm, pos - 1):
                    debug("realm equal to the expected value")
                    return True
                debug("incorrect realm; expected:" + Config.user_realm)
                self.alert(Messages.wrong_realm.format(Config.user_realm))
                return False
            if self.username.endswith(Config.user_realm, pos):
                debug("realm ends with expected suffix")
                return True
            debug("realm suffix error; expected: " + Config.user_realm)
            self.alert(Messages.wrong_realm_suffix.format(
                Config.user_realm))
            return False
        pos1 = self.username.find('@', pos)
        if pos1 > -1:
            debug("second @ character found")
            self.alert(Messages.wrongUsernameFormat)
            return False
        pos1 = self.username.find('.', pos)
        if pos1 == pos:
            debug("a dot immediately after the @ character")
            self.alert(Messages.wrongUsernameFormat)
            return False
        debug("all passed")
        return True


class WpaConf:
    """
    Prepare and save wpa_supplicant config file
    """

    @staticmethod
    def __prepare_network_block(ssid: str, user_data: Type[InstallerData]) -> str:
        interface = """network={
        ssid=\"""" + ssid + """\"
        key_mgmt=WPA-EAP
        pairwise=CCMP
        group=CCMP TKIP
        eap=""" + Config.eap_outer + """
        ca_cert=\"""" + get_config_path() + """/cat_installer/ca.pem\"""""""
        identity=\"""" + user_data.username + """\"""""""
        altsubject_match=\"""" + ";".join(Config.servers) + """\"
        """

        if Config.eap_outer in ('PEAP', 'TTLS'):
            interface += f"phase2=\"auth={Config.eap_inner}\"\n" \
                         f"\tpassword=\"{user_data.password}\"\n"
            if Config.anonymous_identity != '':
                interface += f"\tanonymous_identity=\"{Config.anonymous_identity}\"\n"

        elif Config.eap_outer == 'TLS':
            interface += f"\tprivate_key_passwd=\"{user_data.password}\"\n" \
                         f"\tprivate_key=\"{os.environ.get('HOME')}/.cat_installer/user.p12"

        interface += "\n}"
        return interface

    def create_wpa_conf(self, ssids, user_data: Type[InstallerData]) -> None:
        """Create and save the wpa_supplicant config file"""
        wpa_conf = get_config_path() + '/cat_installer/cat_installer.conf'
        with open(wpa_conf, 'w') as conf:
            for ssid in ssids:
                net = self.__prepare_network_block(ssid, user_data)
                conf.write(net)


class IwdConfiguration:
    """ support the iNet wireless daemon by Intel """
    def __init__(self):
        self.config = ""

    def write_config(self) -> None:
        for ssid in Config.ssids:
            with open('/var/lib/iwd/{}.8021x'.format(ssid), 'w') as config_file:
                config_file.write(self.config)

    def _create_eap_pwd_config(self, ssid: str, user_data: Type[InstallerData]) -> None:
        """ create EAP-PWD configuration """
        self.conf = """
        [Security]
        EAP-Method=PWD
        EAP-Identity={username}
        EAP-Password={password}

        [Settings]
        AutoConnect=True
        """.format(username=user_data.username,
                   password=user_data.password)

    def _create_eap_peap_config(self, ssid: str, user_data: Type[InstallerData]) -> None:
        """ create EAP-PEAP configuration """
        self.conf = """
        [Security]
        EAP-Method=PEAP
        EAP-Identity={anonymous_identity}
        EAP-PEAP-CACert={ca_cert}
        EAP-PEAP-ServerDomainMask={servers}
        EAP-PEAP-Phase2-Method=MSCHAPV2
        EAP-PEAP-Phase2-Identity={username}@{realm}
        EAP-PEAP-Phase2-Password={password}

        [Settings]
        AutoConnect=true
        """.format(anonymous_identity=Config.anonymous_identity,
                   ca_cert=Config.CA, servers=Config.servers,
                   username=user_data.username,
                   realm=Config.user_realm,
                   password=user_data.password)

    def _create_ttls_pap_config(self, ssid: str, user_data: Type[InstallerData]) -> None:
        """ create TTLS-PAP configuration"""
        self.conf = """
        [Security]
        EAP-Method=TTLS
        EAP-Identity={anonymous_identity}
        EAP-TTLS-CACert={ca_cert}
        EAP-TTLS-ServerDomainMask={servers}
        EAP-TTLS-Phase2-Method=Tunneled-PAP
        EAP-TTLS-Phase2-Identity={username}@{realm}
        EAP-TTLS-Phase2-Password={password}

        [Settings]
        AutoConnect=true
        """.format(anonymous_identity=Config.anonymous_identity,
                   ca_cert=Config.CA, servers=Config.servers,
                   username=user_data.username,
                   realm=Config.user_realm,
                   password=user_data.password)


class CatNMConfigTool:
    """
    Prepare and save NetworkManager configuration
    """

    def __init__(self):
        self.cacert_file = None
        self.settings_service_name = None
        self.connection_interface_name = None
        self.system_service_name = "org.freedesktop.NetworkManager"
        self.nm_version = None
        self.pfx_file = None
        self.settings = None
        self.user_data = None
        self.bus = None

    def connect_to_nm(self) -> Union[bool, None]:
        """
        connect to DBus
        """
        try:
            self.bus = dbus.SystemBus()
        except AttributeError:
            # since dbus existed but is empty we have an empty package
            # this gets shipped by pyqt5
            print("DBus not properly installed")
            return None
        except dbus.exceptions.DBusException:
            print("Can't connect to DBus")
            return None
        # check NM version
        self.__check_nm_version()
        debug("NM version: " + self.nm_version)
        if self.nm_version in ("0.9", "1.0"):
            self.settings_service_name = self.system_service_name
            self.connection_interface_name = \
                "org.freedesktop.NetworkManager.Settings.Connection"
            # settings proxy
            sysproxy = self.bus.get_object(
                self.settings_service_name,
                "/org/freedesktop/NetworkManager/Settings")
            # settings interface
            self.settings = dbus.Interface(sysproxy, "org.freedesktop."
                                                     "NetworkManager.Settings")
        elif self.nm_version == "0.8":
            self.settings_service_name = "org.freedesktop.NetworkManager"
            self.connection_interface_name = "org.freedesktop.NetworkMana" \
                                             "gerSettings.Connection"
            # settings proxy
            sysproxy = self.bus.get_object(
                self.settings_service_name,
                "/org/freedesktop/NetworkManagerSettings")
            # settings interface
            self.settings = dbus.Interface(
                sysproxy, "org.freedesktop.NetworkManagerSettings")
        else:
            print(Messages.nm_not_supported)
            return None
        debug("NM connection worked")
        return True

    def __check_opts(self) -> None:
        """
        set certificate files paths and test for existence of the CA cert
        """
        self.cacert_file = get_config_path() + '/cat_installer/ca.pem'
        self.pfx_file = get_config_path() + '/cat_installer/user.p12'
        if not os.path.isfile(self.cacert_file):
            print(Messages.cert_error)
            sys.exit(2)

    def __check_nm_version(self) -> None:
        """
        Get the NetworkManager version
        """
        try:
            proxy = self.bus.get_object(
                self.system_service_name, "/org/freedesktop/NetworkManager")
            props = dbus.Interface(proxy, "org.freedesktop.DBus.Properties")
            version = props.Get("org.freedesktop.NetworkManager", "Version")
        except dbus.exceptions.DBusException:
            version = ""
        if re.match(r'^1\.', version):
            self.nm_version = "1.0"
            return
        if re.match(r'^0\.9', version):
            self.nm_version = "0.9"
            return
        if re.match(r'^0\.8', version):
            self.nm_version = "0.8"
            return
        self.nm_version = Messages.unknown_version

    def __delete_existing_connection(self, ssid: str) -> None:
        """
        checks and deletes earlier connection
        """
        try:
            conns = self.settings.ListConnections()
        except dbus.exceptions.DBusException:
            print(Messages.dbus_error)
            exit(3)
        for each in conns:
            con_proxy = self.bus.get_object(self.system_service_name, each)
            connection = dbus.Interface(
                con_proxy,
                "org.freedesktop.NetworkManager.Settings.Connection")
            try:
                connection_settings = connection.GetSettings()
                if connection_settings['connection']['type'] == '802-11-' \
                                                                'wireless':
                    conn_ssid = byte_to_string(
                        connection_settings['802-11-wireless']['ssid'])
                    if conn_ssid == ssid:
                        debug("deleting connection: " + conn_ssid)
                        connection.Delete()
            except dbus.exceptions.DBusException:
                pass

    def __add_connection(self, ssid: str) -> None:
        debug("Adding connection: " + ssid)
        server_alt_subject_name_list = dbus.Array(Config.servers)
        server_name = Config.server_match
        if self.nm_version in ("0.9", "1.0"):
            match_key = 'altsubject-matches'
            match_value = server_alt_subject_name_list
        else:
            match_key = 'subject-match'
            match_value = server_name
        s_8021x_data = {
            'eap': [Config.eap_outer.lower()],
            'identity': self.user_data.username,
            'ca-cert': dbus.ByteArray(
                "file://{0}\0".format(self.cacert_file).encode('utf8')),
            match_key: match_value}
        if Config.eap_outer in ('PEAP', 'TTLS'):
            s_8021x_data['password'] = self.user_data.password
            s_8021x_data['phase2-auth'] = Config.eap_inner.lower()
            if Config.anonymous_identity != '':
                s_8021x_data['anonymous-identity'] = Config.anonymous_identity
            s_8021x_data['password-flags'] = 0
        elif Config.eap_outer == 'TLS':
            s_8021x_data['client-cert'] = dbus.ByteArray(
                "file://{0}\0".format(self.pfx_file).encode('utf8'))
            s_8021x_data['private-key'] = dbus.ByteArray(
                "file://{0}\0".format(self.pfx_file).encode('utf8'))
            s_8021x_data['private-key-password'] = self.user_data.password
            s_8021x_data['private-key-password-flags'] = 0
        s_con = dbus.Dictionary({
            'type': '802-11-wireless',
            'uuid': str(uuid.uuid4()),
            'permissions': ['user:' + os.environ.get('USER')],
            'id': ssid
        })
        s_wifi = dbus.Dictionary({
            'ssid': dbus.ByteArray(ssid.encode('utf8')),
            'security': '802-11-wireless-security'
        })
        s_wsec = dbus.Dictionary({
            'key-mgmt': 'wpa-eap',
            'proto': ['rsn'],
            'pairwise': ['ccmp'],
            'group': ['ccmp', 'tkip']
        })
        s_8021x = dbus.Dictionary(s_8021x_data)
        s_ip4 = dbus.Dictionary({'method': 'auto'})
        s_ip6 = dbus.Dictionary({'method': 'auto'})
        con = dbus.Dictionary({
            'connection': s_con,
            '802-11-wireless': s_wifi,
            '802-11-wireless-security': s_wsec,
            '802-1x': s_8021x,
            'ipv4': s_ip4,
            'ipv6': s_ip6
        })
        self.settings.AddConnection(con)

    def add_connections(self, user_data: Type[InstallerData]):
        """Delete and then add connections to the system"""
        self.__check_opts()
        self.user_data = user_data
        for ssid in Config.ssids:
            self.__delete_existing_connection(ssid)
            self.__add_connection(ssid)
        for ssid in Config.del_ssids:
            self.__delete_existing_connection(ssid)


Messages.quit = "Really quit?"
Messages.username_prompt = "enter your userid"
Messages.enter_password = "enter password"
Messages.enter_import_password = "enter your import password"
Messages.credentials_prompt = "Please, enter your credentials:"
Messages.incorrect_password = "incorrect password"
Messages.repeat_password = "repeat your password"
Messages.passwords_differ = "passwords do not match"
Messages.installation_finished = "Installation successful"
Messages.cat_dir_exisits = "Directory {} exists; some of its files may " \
    "be overwritten."
Messages.cont = "Continue?"
Messages.nm_not_supported = "This NetworkManager version is not " \
    "supported"
Messages.cert_error = "Certificate file not found, looks like a CAT " \
    "error"
Messages.unknown_version = "Unknown version"
Messages.dbus_error = "DBus connection problem, a sudo might help"
Messages.yes = "Y"
Messages.no = "N"
Messages.ok = "OK"
Messages.p12_filter = "personal certificate file (p12 or pfx)"
Messages.all_filter = "All files"
Messages.p12_title = "personal certificate file (p12 or pfx)"
Messages.save_wpa_conf = "DBus module not found - please install " \
    "dbus-python! NetworkManager configuration failed, but we may generate " \
    "a wpa_supplicant configuration file if you wish. Be warned that your " \
    "connection password will be saved in this file as clear text."
Messages.save_wpa_confirm = "Write the file"
Messages.wrongUsernameFormat = "Error: Your username must be of the " \
    "form 'xxx@institutionID' e.g. 'john@example.net'!"
Messages.wrong_realm = "Error: your username must be in the form of " \
    "'xxx@{}'. Please enter the username in the correct format."
Messages.wrong_realm_suffix = "Error: your username must be in the " \
    "form of 'xxx@institutionID' and end with '{}'. Please enter the " \
    "username in the correct format."
Messages.user_cert_missing = "personal certificate file not found"
Messages.cat_dir_exists = "Directory {} exists; some of its files may " \
    "be overwritten"
Config.instname = "Technische Universiteit Delft"
Config.profilename = "Linux"
Config.url = "your local eduroam® support page"
Config.email = "your local eduroam® support"
Config.title = "eduroam CAT"
Config.server_match = "radius.tudelft.nl"
Config.eap_outer = "TTLS"
Config.eap_inner = "PAP"
Config.init_info = "This installer has been prepared for {0}\n\nMore " \
    "information and comments:\n\nEMAIL: {1}\nWWW: {2}\n\nInstaller created " \
    "with software from the GEANT project."
Config.init_confirmation = "This installer will only work properly if " \
    "you are a member of {0} and the user group: {1}."
Config.user_realm = "tudelft.nl"
Config.ssids = ['eduroam']
Config.del_ssids = []
Config.servers = ['DNS:radius.tudelft.nl']
Config.use_other_tls_id = False
Config.anonymous_identity = "anonymous@tudelft.nl"
Config.hint_user_input = True
Config.verify_user_realm_input = True
Config.tou = ""
Config.CA = """-----BEGIN CERTIFICATE-----
MIIF3jCCA8agAwIBAgIQAf1tMPyjylGoG7xkDjUDLTANBgkqhkiG9w0BAQwFADCB
iDELMAkGA1UEBhMCVVMxEzARBgNVBAgTCk5ldyBKZXJzZXkxFDASBgNVBAcTC0pl
cnNleSBDaXR5MR4wHAYDVQQKExVUaGUgVVNFUlRSVVNUIE5ldHdvcmsxLjAsBgNV
BAMTJVVTRVJUcnVzdCBSU0EgQ2VydGlmaWNhdGlvbiBBdXRob3JpdHkwHhcNMTAw
MjAxMDAwMDAwWhcNMzgwMTE4MjM1OTU5WjCBiDELMAkGA1UEBhMCVVMxEzARBgNV
BAgTCk5ldyBKZXJzZXkxFDASBgNVBAcTC0plcnNleSBDaXR5MR4wHAYDVQQKExVU
aGUgVVNFUlRSVVNUIE5ldHdvcmsxLjAsBgNVBAMTJVVTRVJUcnVzdCBSU0EgQ2Vy
dGlmaWNhdGlvbiBBdXRob3JpdHkwggIiMA0GCSqGSIb3DQEBAQUAA4ICDwAwggIK
AoICAQCAEmUXNg7D2wiz0KxXDXbtzSfTTK1Qg2HiqiBNCS1kCdzOiZ/MPans9s/B
3PHTsdZ7NygRK0faOca8Ohm0X6a9fZ2jY0K2dvKpOyuR+OJv0OwWIJAJPuLodMkY
tJHUYmTbf6MG8YgYapAiPLz+E/CHFHv25B+O1ORRxhFnRghRy4YUVD+8M/5+bJz/
Fp0YvVGONaanZshyZ9shZrHUm3gDwFA66Mzw3LyeTP6vBZY1H1dat//O+T23LLb2
VN3I5xI6Ta5MirdcmrS3ID3KfyI0rn47aGYBROcBTkZTmzNg95S+UzeQc0PzMsNT
79uq/nROacdrjGCT3sTHDN/hMq7MkztReJVni+49Vv4M0GkPGw/zJSZrM233bkf6
c0Plfg6lZrEpfDKEY1WJxA3Bk1QwGROs0303p+tdOmw1XNtB1xLaqUkL39iAigmT
Yo61Zs8liM2EuLE/pDkP2QKe6xJMlXzzawWpXhaDzLhn4ugTncxbgtNMs+1b/97l
c6wjOy0AvzVVdAlJ2ElYGn+SNuZRkg7zJn0cTRe8yexDJtC/QV9AqURE9JnnV4ee
UB9XVKg+/XRjL7FQZQnmWEIuQxpMtPAlR1n6BB6T1CZGSlCBst6+eLf8ZxXhyVeE
Hg9j1uliutZfVS7qXMYoCAQlObgOK6nyTJccBz8NUvXt7y+CDwIDAQABo0IwQDAd
BgNVHQ4EFgQUU3m/WqorSs9UgOHYm8Cd8rIDZsswDgYDVR0PAQH/BAQDAgEGMA8G
A1UdEwEB/wQFMAMBAf8wDQYJKoZIhvcNAQEMBQADggIBAFzUfA3P9wF9QZllDHPF
Up/L+M+ZBn8b2kMVn54CVVeWFPFSPCeHlCjtHzoBN6J2/FNQwISbxmtOuowhT6KO
VWKR82kV2LyI48SqC/3vqOlLVSoGIG1VeCkZ7l8wXEskEVX/JJpuXior7gtNn3/3
ATiUFJVDBwn7YKnuHKsSjKCaXqeYalltiz8I+8jRRa8YFWSQEg9zKC7F4iRO/Fjs
8PRF/iKz6y+O0tlFYQXBl2+odnKPi4w2r78NBc5xjeambx9spnFixdjQg3IM8WcR
iQycE0xyNN+81XHfqnHd4blsjDwSXWXavVcStkNr/+XeTWYRUc+ZruwXtuhxkYze
Sf7dNXGiFSeUHM9h4ya7b6NnJSFd5t0dCy5oGzuCr+yDZ4XUmFF0sbmZgIn/f3gZ
XHlKYC6SQK5MNyosycdiyA5d9zZbyuAlJQG03RoHnHcAP9Dc1ew91Pq7P8yF1m9/
qS3fuQL39ZeatTXaw2ewh0qpKJ4jjv9cJ2vhsE/zB+4ALtRZh8tSQZXq9EfX7mRB
VXyNWQKV3WKdwrnuWih0hKWbt5DHDAff9Yk2dDLWKMGwsAvgnEzDHNb842m1R0aB
L6KCq9NjRHDEjf8tM7qtj3u1cIiuPhnPQCjY/MiQu12ZIvVS5ljFH4gxQ+6IHdfG
jjxDah2nGN59PRbxYvnKkKj9
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
MIIFpDCCA4ygAwIBAgIQOcqTHO9D88aOk8f0ZIk4fjANBgkqhkiG9w0BAQsFADBs
MQswCQYDVQQGEwJHUjE3MDUGA1UECgwuSGVsbGVuaWMgQWNhZGVtaWMgYW5kIFJl
c2VhcmNoIEluc3RpdHV0aW9ucyBDQTEkMCIGA1UEAwwbSEFSSUNBIFRMUyBSU0Eg
Um9vdCBDQSAyMDIxMB4XDTIxMDIxOTEwNTUzOFoXDTQ1MDIxMzEwNTUzN1owbDEL
MAkGA1UEBhMCR1IxNzA1BgNVBAoMLkhlbGxlbmljIEFjYWRlbWljIGFuZCBSZXNl
YXJjaCBJbnN0aXR1dGlvbnMgQ0ExJDAiBgNVBAMMG0hBUklDQSBUTFMgUlNBIFJv
b3QgQ0EgMjAyMTCCAiIwDQYJKoZIhvcNAQEBBQADggIPADCCAgoCggIBAIvC569l
mwVnlskNJLnQDmT8zuIkGCyEf3dRywQRNrhe7Wlxp57kJQmXZ8FHws+RFjZiPTgE
4VGC/6zStGndLuwRo0Xua2s7TL+MjaQenRG56Tj5eg4MmOIjHdFOY9TnuEFE+2uv
a9of08WRiFukiZLRgeaMOVig1mlDqa2YUlhu2wr7a89o+uOkXjpFc5gH6l8Cct4M
pbOfrqkdtx2z/IpZ525yZa31MJQjB/OCFks1mJxTuy/K5FrZx40d/JiZ+yykgmvw
Kh+OC19xXFyuQnspiYHLA6OZyoieC0AJQTPb5lh6/a6ZcMBaD9YThnEvdmn8kN3b
LW7R8pv1GmuebxWMevBLKKAiOIAkbDakO/IwkfN4E8/BPzWr8R0RI7VDIp4BkrcY
AuUR0YLbFQDMYTfBKnya4dC6s1BG7oKsnTH4+yPiAwBIcKMJJnkVU2DzOFytOOqB
AGMUuTNe3QvboEUHGjMJ+E20pwKmafTCWQWIZYVWrkvL4N48fS0ayOn7H6NhStYq
E613TBoYm5EPWNgGVMWX+Ko/IIqmhaZ39qb8HOLubpQzKoNQhArlT4b4UEV4AIHr
W2jjJo3Me1xR9BQsQL4aYB16cmEdH2MtiKrOokWQCPxrvrNQKlr9qEgYRtaQQJKQ
CoReaDH46+0N0x3GfZkYVVYnZS6NRcUk7M7jAgMBAAGjQjBAMA8GA1UdEwEB/wQF
MAMBAf8wHQYDVR0OBBYEFApII6ZgpJIKM+qTW8VX6iVNvRLuMA4GA1UdDwEB/wQE
AwIBhjANBgkqhkiG9w0BAQsFAAOCAgEAPpBIqm5iFSVmewzVjIuJndftTgfvnNAU
X15QvWiWkKQUEapobQk1OUAJ2vQJLDSle1mESSmXdMgHHkdt8s4cUCbjnj1AUz/3
f5Z2EMVGpdAgS1D0NTsY9FVqQRtHBmg8uwkIYtlfVUKqrFOFrJVWNlar5AWMxaja
H6NpvVMPxP/cyuN+8kyIhkdGGvMA9YCRotxDQpSbIPDRzbLrLFPCU3hKTwSUQZqP
JzLB5UkZv/HywouoCjkxKLR9YjYsTewfM7Z+d21+UPCfDtcRj88YxeMn/ibvBZ3P
zzfF0HvaO7AWhAw6k9a+F9sPPg4ZeAnHqQJyIkv3N3a6dcSFA1pj1bF1BcK5vZSt
jBWZp5N99sXzqnTPBIWUmAD04vnKJGW/4GKvyMX6ssmeVkjaef2WdhW+o45WxLM0
/L5H9MG0qPzVMIho7suuyWPEdr6sOBjhXlzPrjoiUevRi7PzKzMHVIf6tLITe7pT
BGIBnfHAT+7hOtSLIBD6Alfm78ELt5BGnBkpjNxvoEppaZS3JGWg/6w/zgH7IS79
aPib8qXPMThcFarmlwDB31qlpzmq6YR/PFGoOtmUW4y/Twhx5duoXNTSpv4Ao8YW
xw/ogM4cKGR0GQjTQuPOAF1/sdwTsOEFy9EgqoZ0njnnkf3/W9b3raYvAwtt41dU
63ZTGI0RmLo=
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
MIIG5TCCBM2gAwIBAgIRANpDvROb0li7TdYcrMTz2+AwDQYJKoZIhvcNAQEMBQAw
gYgxCzAJBgNVBAYTAlVTMRMwEQYDVQQIEwpOZXcgSmVyc2V5MRQwEgYDVQQHEwtK
ZXJzZXkgQ2l0eTEeMBwGA1UEChMVVGhlIFVTRVJUUlVTVCBOZXR3b3JrMS4wLAYD
VQQDEyVVU0VSVHJ1c3QgUlNBIENlcnRpZmljYXRpb24gQXV0aG9yaXR5MB4XDTIw
MDIxODAwMDAwMFoXDTMzMDUwMTIzNTk1OVowRDELMAkGA1UEBhMCTkwxGTAXBgNV
BAoTEEdFQU5UIFZlcmVuaWdpbmcxGjAYBgNVBAMTEUdFQU5UIE9WIFJTQSBDQSA0
MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEApYhi1aEiPsg9ZKRMAw9Q
r8Mthsr6R20VSfFeh7TgwtLQi6RSRLOh4or4EMG/1th8lijv7xnBMVZkTysFiPmT
PiLOfvz+QwO1NwjvgY+Jrs7fSoVA/TQkXzcxu4Tl3WHi+qJmKLJVu/JOuHud6mOp
LWkIbhODSzOxANJ24IGPx9h4OXDyy6/342eE6UPXCtJ8AzeumTG6Dfv5KVx24lCF
TGUzHUB+j+g0lSKg/Sf1OzgCajJV9enmZ/84ydh48wPp6vbWf1H0O3Rd3LhpMSVn
TqFTLKZSbQeLcx/l9DOKZfBCC9ghWxsgTqW9gQ7v3T3aIfSaVC9rnwVxO0VjmDdP
FNbdoxnh0zYwf45nV1QQgpRwZJ93yWedhp4ch1a6Ajwqs+wv4mZzmBSjovtV0mKw
d+CQbSToalEUP4QeJq4Udz5WNmNMI4OYP6cgrnlJ50aa0DZPlJqrKQPGL69KQQz1
2WgxvhCuVU70y6ZWAPopBa1ykbsttpLxADZre5cH573lIuLHdjx7NjpYIXRx2+QJ
URnX2qx37eZIxYXz8ggM+wXH6RDbU3V2o5DP67hXPHSAbA+p0orjAocpk2osxHKo
NSE3LCjNx8WVdxnXvuQ28tKdaK69knfm3bB7xpdfsNNTPH9ElcjscWZxpeZ5Iij8
lyrCG1z0vSWtSBsgSnUyG/sCAwEAAaOCAYswggGHMB8GA1UdIwQYMBaAFFN5v1qq
K0rPVIDh2JvAnfKyA2bLMB0GA1UdDgQWBBRvHTVJEGwy+lmgnryK6B+VvnF6DDAO
BgNVHQ8BAf8EBAMCAYYwEgYDVR0TAQH/BAgwBgEB/wIBADAdBgNVHSUEFjAUBggr
BgEFBQcDAQYIKwYBBQUHAwIwOAYDVR0gBDEwLzAtBgRVHSAAMCUwIwYIKwYBBQUH
AgEWF2h0dHBzOi8vc2VjdGlnby5jb20vQ1BTMFAGA1UdHwRJMEcwRaBDoEGGP2h0
dHA6Ly9jcmwudXNlcnRydXN0LmNvbS9VU0VSVHJ1c3RSU0FDZXJ0aWZpY2F0aW9u
QXV0aG9yaXR5LmNybDB2BggrBgEFBQcBAQRqMGgwPwYIKwYBBQUHMAKGM2h0dHA6
Ly9jcnQudXNlcnRydXN0LmNvbS9VU0VSVHJ1c3RSU0FBZGRUcnVzdENBLmNydDAl
BggrBgEFBQcwAYYZaHR0cDovL29jc3AudXNlcnRydXN0LmNvbTANBgkqhkiG9w0B
AQwFAAOCAgEAUtlC3e0xj/1BMfPhdQhUXeLjb0xp8UE28kzWE5xDzGKbfGgnrT2R
lw5gLIx+/cNVrad//+MrpTppMlxq59AsXYZW3xRasrvkjGfNR3vt/1RAl8iI31lG
hIg6dfIX5N4esLkrQeN8HiyHKH6khm4966IkVVtnxz5CgUPqEYn4eQ+4eeESrWBh
AqXaiv7HRvpsdwLYekAhnrlGpioZ/CJIT2PTTxf+GHM6cuUnNqdUzfvrQgA8kt1/
ASXx2od/M+c8nlJqrGz29lrJveJOSEMX0c/ts02WhsfMhkYa6XujUZLmvR1Eq08r
48/EZ4l+t5L4wt0DV8VaPbsEBF1EOFpz/YS2H6mSwcFaNJbnYqqJHIvm3PLJHkFm
EoLXRVrQXdCT+3wgBfgU6heCV5CYBz/YkrdWES7tiiT8sVUDqXmVlTsbiRNiyLs2
bmEWWFUl76jViIJog5fongEqN3jLIGTG/mXrJT1UyymIcobnIGrbwwRVz/mpFQo0
vBYIi1k2ThVh0Dx88BbF9YiP84dd8Fkn5wbE6FxXYJ287qfRTgmhePecPc73Yrzt
apdRcsKVGkOpaTIJP/l+lAHRLZxk/dUtyN95G++bOSQqnOCpVPabUGl2E/OEyFrp
Ipwgu2L/WJclvd6g+ZA/iWkLSMcpnFb+uX6QBqvD6+RNxul1FaB5iHY=
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
MIIGBTCCA+2gAwIBAgIQFNV782kiKCGaVWf6kWUbIjANBgkqhkiG9w0BAQsFADBs
MQswCQYDVQQGEwJHUjE3MDUGA1UECgwuSGVsbGVuaWMgQWNhZGVtaWMgYW5kIFJl
c2VhcmNoIEluc3RpdHV0aW9ucyBDQTEkMCIGA1UEAwwbSEFSSUNBIFRMUyBSU0Eg
Um9vdCBDQSAyMDIxMB4XDTI1MDEwMzExMTUwMFoXDTM5MTIzMTExMTQ1OVowYDEL
MAkGA1UEBhMCR1IxNzA1BgNVBAoMLkhlbGxlbmljIEFjYWRlbWljIGFuZCBSZXNl
YXJjaCBJbnN0aXR1dGlvbnMgQ0ExGDAWBgNVBAMMD0dFQU5UIFRMUyBSU0EgMTCC
AaIwDQYJKoZIhvcNAQEBBQADggGPADCCAYoCggGBAKEEaZSzEzznAPk8IEa17GSG
yJzPTj4cwRY7/vcq2BPT5+IRGxQtaCdgLXIEl2cdPdIkj2eyakFmgMjAtyeju8V8
dRayQCD/bWjJ7thDlowgLljQaXirxnYbT8bzRHAhCZqBakYgi5KWw9dANLyDHGpX
UdY259ab0lWEaFE5Uu6IzQSMJOAy4l/Twym8GUiy0qMDEBFSlm31C9BXpdHKKAlh
vIjMiKoDeTWl5vZaLB2MMRGY1yW2ftPgIP0/MkX1uFITlvHmmMTngxplH1nybEIJ
FiwHg1KiLk1TprcZgeO2gxE5Lz3wTFWrsUlAzrh5xWmscWkjNi/4BpeuiT5+NExF
czboLnXOfjuci/7bsnPi1/aZN/iKNbJRnngFoLaKVMmqCS7Xo34f+BITatryQZFE
u2oDKExQGlxDBCfYMLgLucX/onpLzUSgeQITNLx6i5tGGbUYH+9Dy3GI66L/5tPj
qzlOsydki8ZYGE5SBJeWCZ2IrhUe0WzZ2b6Zhk6JAQIDAQABo4IBLTCCASkwEgYD
VR0TAQH/BAgwBgEB/wIBADAfBgNVHSMEGDAWgBQKSCOmYKSSCjPqk1vFV+olTb0S
7jBNBggrBgEFBQcBAQRBMD8wPQYIKwYBBQUHMAKGMWh0dHA6Ly9jcnQuaGFyaWNh
LmdyL0hBUklDQS1UTFMtUm9vdC0yMDIxLVJTQS5jZXIwEQYDVR0gBAowCDAGBgRV
HSAAMB0GA1UdJQQWMBQGCCsGAQUFBwMCBggrBgEFBQcDATBCBgNVHR8EOzA5MDeg
NaAzhjFodHRwOi8vY3JsLmhhcmljYS5nci9IQVJJQ0EtVExTLVJvb3QtMjAyMS1S
U0EuY3JsMB0GA1UdDgQWBBSGAXI/jKlw4jEGUxbOAV9becg8OzAOBgNVHQ8BAf8E
BAMCAYYwDQYJKoZIhvcNAQELBQADggIBABkssjQzYrOo4GMsKegaChP16yNe6Sck
cWBymM455R2rMeuQ3zlxUNOEt+KUfgueOA2urp4j6TlPbs/XxpwuN3I1f09Luk5b
+ZgRXM7obE6ZLTerVQWKoTShyl34R2XlK8pEy7+67Ht4lcJzt+K6K5gEuoPSGQDP
ef+fUfmXrFcgBMcMbtfDb9dubFKNZZxo5nAXiqhFMOIyByag3H+tOTuH8zuId9pH
RDsUpAIHJ9/W2WBfLcKav7IKRlNBRD/sPBy903J9WHPKwl8kQSDA+aa7XCYk7bJt
Eyf+7GM9F5cZ7+YyknXqnv/rtQEkTKZdQo5Us18VFe9qqj94tXbLdk7PejJYNB4O
Zlli44Ld7rtqfFlUych7gIxFOmiyxMQQYrYmUi+74lEZvfoNhuref0CupuKpz6O3
dLv6kO9T10uNdDBoBQTkge3UzHafTIe3R2o3ujXKUGPwyc9m7/FETyKLUCwSU/5O
AVOeBCU8QtkKKjM8AmbpKpe3pHWcyq3R7B3LmIALkMPTydyDfxen65IDqREbVq8N
xjhkJThUz40JqOlN6uqKqeDISj/IoucYwsqW24AlO7ZzNmohQmMi8ep23H4hBSh0
GBTe2XvkuzaNf92syK8l2HzO+13GLCjzYLTPvXTO9UpK8DGyfGZOuamuwbAnbNpE
3RfjV9IaUQGJ
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
MIIGCzCCA/OgAwIBAgIBADANBgkqhkiG9w0BAQsFADCBpjELMAkGA1UEBhMCR1Ix
DzANBgNVBAcTBkF0aGVuczFEMEIGA1UEChM7SGVsbGVuaWMgQWNhZGVtaWMgYW5k
IFJlc2VhcmNoIEluc3RpdHV0aW9ucyBDZXJ0LiBBdXRob3JpdHkxQDA+BgNVBAMT
N0hlbGxlbmljIEFjYWRlbWljIGFuZCBSZXNlYXJjaCBJbnN0aXR1dGlvbnMgUm9v
dENBIDIwMTUwHhcNMTUwNzA3MTAxMTIxWhcNNDAwNjMwMTAxMTIxWjCBpjELMAkG
A1UEBhMCR1IxDzANBgNVBAcTBkF0aGVuczFEMEIGA1UEChM7SGVsbGVuaWMgQWNh
ZGVtaWMgYW5kIFJlc2VhcmNoIEluc3RpdHV0aW9ucyBDZXJ0LiBBdXRob3JpdHkx
QDA+BgNVBAMTN0hlbGxlbmljIEFjYWRlbWljIGFuZCBSZXNlYXJjaCBJbnN0aXR1
dGlvbnMgUm9vdENBIDIwMTUwggIiMA0GCSqGSIb3DQEBAQUAA4ICDwAwggIKAoIC
AQDC+Kk/G4n8PDwEXT2QNrCROnk8ZlrvbTkBSRq0t89/TSNTt5AA4xMqKKYx8ZEA
4yjsriFBzh/a/X0SWwGDD7mwX5nh8hKDgE0GPt+sr+ehiGsxr/CL0BgzuNtFajT0
AoAkKAoCFZVedioNmToUW/bLy1O8E00BiDeUJRtCvCLYjqOWXjrZMts+6PAQZe10
4S+nfK8nNLspfZu2zwnI5dMK/IhlZXQK3HMcXM1AsRzUtoSMTFDPaI6oWa7CJ06C
ojXdFPQf/7J31Ycvqm59JCfnxssm5uX+Zwdj2EUN3TpZZTlYepKZcj2chF6IIbjV
9Cz82XBST3i4vTwri5WY9bPRaM8gFH5MXF/ni+X1NYEZN9cRCLdmvtNKzoNXADrD
gfgXy5I2XdGj2HUb4Ysn6npIQf1FGQatJ5lOwXBH3bWfgVMS5bGMSF0xQxfjjMZ6
Y5ZLKTBOhE5iGV48zpeQpX8B653g+IuJ3SWYPZK2fu/Z8VFRfS0myGlZYeCsargq
NhEEelC9MoS+L9xy1dcdFkfkR2YgP/SWxa+OAXqlD3pk9Q0Yh9muiNX6hME6wGko
LfINaFGq46V3xqSQDqE3izEjR8EJCOtu93ib14L8hCCZSRm2Ekax+0VVFqmjZayc
Bw/qa9wfLgZy7IaIEuQt218FL+TwA9MmM+eAws1CoRc0CwIDAQABo0IwQDAPBgNV
HRMBAf8EBTADAQH/MA4GA1UdDwEB/wQEAwIBBjAdBgNVHQ4EFgQUcRVnyMjJvXVd
ctA4GGqd83EkVAswDQYJKoZIhvcNAQELBQADggIBAHW7bVRLqhBYRjTyYtcWNl0I
XtVsyIe9tC5G8jH4fOpCtZMWVdyhDBKg2mF+D1hYc2Ryx+hFjtyp8iY/xnmMsVMI
M4GwVhO+5lFc2JsKT0ucVlMC6U/2DWDqTUJV6HwbISHTGzrMd/K4kPFox/la/vot
9L/J9UUbzjgQKjeKeaO04wlshYaT/4mWJ3iBj2fjRnRUjtkNaeJK9E10A/+yd+2V
Z5fkscWrv2oj6NSU4kQoYsRL4vDY4ilrGnB+JGGTe08DMiUNRSQrlrRGar9KC/ea
j8GsGsVn82800vpzY4zvFrCopEYq+OsS7HK07/grfoxSwIuEVPkvPuNVqNxmsdnh
X9izjFk0WaSrT2y7HxjbdavYy5LNlDhhDgcGH0tGEPEVvo2FXDtKK4F5D7Rpn0lQ
l033DlZdwJVqwjbDG2jJ9SrcR5q+ss7FJej6A7na+RZukYT1HCjI/CbM1xyQVqdf
bzoEvM14iQuODy+jqk+iGxI9FghAD/FGTNeqewjBCvVtJ94Cj8rDtSvK6evIIVM4
pcw72Hc3MKJP2W/R8kCtQXoXxdZKNYm3QdV8hn9VTYNKpXMgwDqvkPGaJI7ZjnHK
e7iG2rKPmT4dEw0SEe7Uq/DpFXYC5ODfqiAeW2GFZECpkJcNrVPSWh2HagCXZWK0
vm9qp/UsQu0yrbYhnr68
-----END CERTIFICATE-----
"""


if __name__ == '__main__':
    run_installer()
