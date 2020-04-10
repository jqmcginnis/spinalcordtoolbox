#!/usr/bin/env python
# -*- coding: utf-8
# Collection of useful functions


import io
import cgi
import os
import re
import logging
import argparse
import subprocess
import shutil
import tempfile
import tarfile
import zipfile
from enum import Enum
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util import Retry
from tqdm import tqdm

logger = logging.getLogger(__name__)


# TODO: add test


class ActionCreateFolder(argparse.Action):
    """
    Custom action: creates a new folder if it does not exist. If the folder
    already exists, do nothing.

    The action will strip off trailing slashes from the folder's name.
    Source: https://argparse-actions.readthedocs.io/en/latest/
    """
    @staticmethod
    def create_folder(folder_name):
        """
        Create a new directory if not exist. The action might throw
        OSError, along with other kinds of exception
        """
        if not os.path.isdir(folder_name):
            os.mkdir(folder_name)

        folder_name = os.path.normpath(folder_name)
        return folder_name

    def __call__(self, parser, namespace, values, option_string=None):
        if type(values) == list:
            folders = list(map(self.create_folder, values))
        else:
            folders = self.create_folder(values)

        # Add the attribute
        setattr(namespace, self.dest, folders)


class Metavar(Enum):
    """
    This class is used to display intuitive input types via the metavar field of argparse
    """
    file = "<file>"
    str = "<str>"
    folder = "<folder>"
    int = "<int>"
    list = "<list>"
    float = "<float>"

    def __str__(self):
        return self.value


class SmartFormatter(argparse.HelpFormatter):
    """
    Custom formatter that inherits from HelpFormatter, which adjusts the default width to the current Terminal size,
    and that gives the possibility to bypass argparse's default formatting by adding "R|" at the beginning of the text.
    Inspired from: https://pythonhosted.org/skaff/_modules/skaff/cli.html
    """
    def __init__(self, *args, **kw):
        self._add_defaults = None
        super(SmartFormatter, self).__init__(*args, **kw)
        # Update _width to match Terminal width
        try:
            self._width = shutil.get_terminal_size()[0]
        except (KeyError, ValueError):
            logger.warning('Not able to fetch Terminal width. Using default: %s'.format(self._width))

    # this is the RawTextHelpFormatter._fill_text
    def _fill_text(self, text, width, indent):
        # print("splot",text)
        if text.startswith('R|'):
            paragraphs = text[2:].splitlines()
            rebroken = [argparse._textwrap.wrap(tpar, width) for tpar in paragraphs]
            rebrokenstr = []
            for tlinearr in rebroken:
                if (len(tlinearr) == 0):
                    rebrokenstr.append("")
                else:
                    for tlinepiece in tlinearr:
                        rebrokenstr.append(tlinepiece)
            return '\n'.join(rebrokenstr)  # (argparse._textwrap.wrap(text[2:], width))
        return argparse.RawDescriptionHelpFormatter._fill_text(self, text, width, indent)

    # this is the RawTextHelpFormatter._split_lines
    def _split_lines(self, text, width):
        if text.startswith('R|'):
            return text[2:].splitlines()
        return argparse.HelpFormatter._split_lines(self, text, width)


def check_exe(name):
    """
    Ensure that a program exists
    :type name: string
    :param name: name or path to program
    :return: path of the program or None
    """
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(name)
    if fpath and is_exe(name):
        return fpath
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, name)
            if is_exe(exe_file):
                return exe_file

    return None


def __get_branch():
    """
    Fallback if for some reason the value vas no set by sct_launcher
    :return:
    """

    p = subprocess.Popen(["git", "rev-parse", "--abbrev-ref", "HEAD"], stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, cwd=__sct_dir__)
    output, _ = p.communicate()
    status = p.returncode

    if status == 0:
        return output.decode().strip()


def __get_commit():
    """
    :return: git commit ID, with trailing '*' if modified
    """
    p = subprocess.Popen(["git", "rev-parse", "HEAD"], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         cwd=__sct_dir__)
    output, _ = p.communicate()
    status = p.returncode
    if status == 0:
        commit = output.decode().strip()
    else:
        commit = "?!?"

    p = subprocess.Popen(["git", "status", "--porcelain"], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         cwd=__sct_dir__)
    output, _ = p.communicate()
    status = p.returncode
    if status == 0:
        unclean = True
        for line in output.decode().strip().splitlines():
            line = line.rstrip()
            if line.startswith("??"): # ignore ignored files, they can't hurt
               continue
            break
        else:
            unclean = False
        if unclean:
            commit += "*"

    return commit


def _git_info(commit_env='SCT_COMMIT', branch_env='SCT_BRANCH'):

    sct_commit = os.getenv(commit_env, "unknown")
    sct_branch = os.getenv(branch_env, "unknown")
    if check_exe("git") and os.path.isdir(os.path.join(__sct_dir__, ".git")):
        sct_commit = __get_commit() or sct_commit
        sct_branch = __get_branch() or sct_branch

    if sct_commit is not 'unknown':
        install_type = 'git'
    else:
        install_type = 'package'

    with io.open(os.path.join(__sct_dir__, 'version.txt'), 'r') as f:
        version_sct = f.read().rstrip()

    return install_type, sct_commit, sct_branch, version_sct


def _version_string():
    install_type, sct_commit, sct_branch, version_sct = _git_info()
    if install_type == "package":
        return version_sct
    else:
        return "{install_type}-{sct_branch}-{sct_commit}".format(**locals())


__sct_dir__ = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
__version__ = _version_string()
__data_dir__ = os.path.join(__sct_dir__, 'data')


def download_data(urls):
    """Download the binaries from a URL and return the destination filename

    Retry downloading if either server or connection errors occur on a SSL
    connection
    urls: list of several urls (mirror servers) or single url (string)
    """

    # if urls is not a list, make it one
    if not isinstance(urls, (list, tuple)):
        urls = [urls]

    # loop through URLs
    for url in urls:
        try:
            logger.info('\nTrying URL: %s' % url)
            retry = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 503, 504])
            session = requests.Session()
            session.mount('https://', HTTPAdapter(max_retries=retry))
            response = session.get(url, stream=True)

            if "Content-Disposition" in response.headers:
                _, content = cgi.parse_header(response.headers['Content-Disposition'])
                filename = content["filename"]
            else:
                logger.warning("Unexpected: link doesn't provide a filename")
                continue

            tmp_path = os.path.join(tempfile.mkdtemp(), filename)
            logger.info('Downloading %s...' % filename)

            with open(tmp_path, 'wb') as tmp_file:
                total = int(response.headers.get('content-length', 1))
                tqdm_bar = tqdm(total=total, unit='B', unit_scale=True,
                                desc="Status", ascii=True)

                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        tmp_file.write(chunk)
                        dl_chunk = len(chunk)
                        tqdm_bar.update(dl_chunk)

                tqdm_bar.close()
            return tmp_path

        except Exception as e:
            logger.warning("Link download error, trying next mirror (error was: %s)" % e)
    else:
        logger.error('\nDownload error')


def parse_num_list(str_num):
    """
    Parse numbers in string based on delimiter: , or :
    Examples:
      '' -> []
      '1,2,3' -> [1, 2, 3]
      '1:3,4' -> [1, 2, 3, 4]
      '1,1:4' -> [1, 2, 3, 4]
    :param str_num: string
    :return: list of ints
    """
    list_num = list()

    if not str_num:
        return list_num

    elements = str_num.split(",")
    for element in elements:
        m = re.match(r"^\d+$", element)
        if m is not None:
            val = int(element)
            if val not in list_num:
                list_num.append(val)
            continue
        m = re.match(r"^(?P<first>\d+):(?P<last>\d+)$", element)
        if m is not None:
            a = int(m.group("first"))
            b = int(m.group("last"))
            list_num += [ x for x in range(a, b+1) if x not in list_num ]
            continue
        raise ValueError("unexpected group element {} group spec {}".format(element, str_num))

    return list_num


def parse_num_list_inv(list_int):
    """
    Take a list of numbers and output a string that reduce this list based on delimiter: ; or :
    Note: we use ; instead of , for compatibility with csv format.
    Examples:
      [] -> ''
      [1, 2, 3] --> '1:3'
      [1, 2, 3, 5] -> '1:3;5'
    :param list_int: list of ints
    :return: str_num: string
    """
    # deal with empty list
    if not list_int or list_int is None:
        return ''
    # Sort list in increasing number
    list_int = sorted(list_int)
    # initialize string
    str_num = str(list_int[0])
    colon_is_present = False
    # Loop across list elements and build string iteratively
    for i in range(1, len(list_int)):
        # if previous element is the previous integer: I(i-1) = I(i)-1
        if list_int[i] == list_int[i-1] + 1:
            # if ":" already there, update the last chars (based on the number of digits)
            if colon_is_present:
                str_num = str_num[:-len(str(list_int[i-1]))] + str(list_int[i])
            # if not, add it along with the new int value
            else:
                str_num += ':' + str(list_int[i])
                colon_is_present = True
        # I(i-1) != I(i)-1
        else:
            str_num += ';' + str(list_int[i])
            colon_is_present = False

    return str_num


def unzip(compressed, dest_folder):
    """
    Extract compressed file to the dest_folder. Can handle .zip, .tar.gz.
    """
    logger.info('\nUnzip data to: %s' % dest_folder)
    if compressed.endswith('zip'):
        try:
            zf = zipfile.ZipFile(compressed)
            zf.extractall(dest_folder)
            return
        except (zipfile.BadZipfile):
            logger.error("ZIP package corrupted. Please try downloading again.")
    elif compressed.endswith('tar.gz'):
        try:
            tar = tarfile.open(compressed)
            tar.extractall(path=dest_folder)
            return
        except tarfile.TarError:
            logger.error("ZIP package corrupted. Please try again.")
    else:
        logger.error("The file %s is of wrong format" % compressed)
