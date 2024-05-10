"""
Convenience/shell related utilities

Copyright (c) 2020 Polytechnique Montreal <www.neuro.polymtl.ca>
License: see the file LICENSE
"""

import os
import sys
import re
import shutil
import logging
import argparse
import inspect

from enum import Enum

from .sys import check_exe, printv, removesuffix, ANSIColors16
from .fs import relpath_or_abspath

logger = logging.getLogger(__name__)


def display_open(file, message="Done! To view results"):
    """Print the syntax to open a file based on the platform."""
    cmd_open = None
    if sys.platform.startswith('linux'):
        # If user runs SCT within the official Docker distribution, or in WSL, then the command xdg-open will not be
        # working, therefore we prefer to instruct the user to manually open the file.
        # Source for WSL environment variables: https://stackoverflow.com/a/61036356
        if "DOCKER" not in os.environ and "IS_WSL" not in os.environ and "WSL_DISTRO_NAME" not in os.environ:
            cmd_open = 'xdg-open'
    elif sys.platform.startswith('darwin'):
        cmd_open = 'open'
    elif sys.platform.startswith('win32'):
        cmd_open = 'start'

    if cmd_open:
        printv(f'\n{message}, type:')
        printv(f"{cmd_open} {file}\n", type='info')
    else:
        printv(f'\n{message}, open the following file:')
        printv(f"{file}\n", type='info')


SUPPORTED_VIEWERS = ['fsleyes', 'fslview_deprecated', 'fslview', 'itk-snap', 'itksnap']
# - The 'fsleyes' colormaps are used for 'fsleyes'.
# - The 'fslview' colormaps are used for 'fslview' and 'fslview_deprecated'.
# - For 'itksnap', there are no colormaps. Instead, color behavior is dictated using CLI options '-g', '-o', and '-s'.
#   How imtypes are mapped to CLI options is a bit convoluted, but tl;dr: only 2 image types (gray, seg) are supported.
#   Surprisingly, softseg images can only be properly displayed as grayscale images, hence the use of 'gray' for them.
IMTYPES_COLORMAP = {
    'anat':        {'fsleyes': 'greyscale',      'fslview': 'Greyscale',       'itksnap': 'gray'},
    'seg':         {'fsleyes': 'red',            'fslview': 'Red',             'itksnap': 'seg'},
    'seg-labeled': {'fsleyes': 'subcortical',    'fslview': 'MGH-Subcortical', 'itksnap': 'seg'},
    'softseg':     {'fsleyes': 'red-yellow',     'fslview': 'Red-Yellow',      'itksnap': 'gray'},
    'softseg-alt': {'fsleyes': 'blue-lightblue', 'fslview': 'Blue-Lightblue',  'itksnap': 'gray'},
}


def display_viewer_syntax(files, verbose, im_types=[], minmax=[], opacities=[], mode=''):
    """
    Print the syntax to open a viewer and display images for QC. To use default values, enter empty string: ''
    Parameters
    ----------
    files [list:string]: list of NIFTI file names
    im_types [list:string]: list of image type associated with each file. Available types: see IMTYPE_COLORMAPS
    minmax [list:string]: list of min,max brightness scale associated with each file. Separate with comma.
    opacities [list:string]: list of opacity associated with each file. Between 0 and 1.

    Returns
    -------
    cmd_strings [dict:string]: pairs of viewers and their corresponding syntax strings (that were printed).

    Example
    -------
    display_viewer_syntax([file1, file2, file3])
    display_viewer_syntax([file1, file2], im_types=['anat', 'softseg'], minmax=['', '0,1'], opacities=['', '0.7'])
    """
    # Try to convert the path to one that is relative to the CWD; if not possible, use the abspath instead.
    files = [str(relpath_or_abspath(filepath, parent_path=os.getcwd())) for filepath in files]

    available_viewers = [viewer for viewer in SUPPORTED_VIEWERS if check_exe(viewer)]

    if verbose:
        if len(available_viewers) == 0:
            return
        elif len(available_viewers) == 1:
            printv('\nDone! To view results, type:')
        elif len(available_viewers) >= 2:
            printv('\nDone! To view results, run one of the following commands (depending on your preferred viewer):')

    cmd_strings = {}
    for viewer in available_viewers:
        if viewer in ['fslview', 'fslview_deprecated']:
            cmd = _construct_fslview_syntax(viewer, files, im_types, minmax, opacities, mode)
        elif viewer in ['fsleyes']:
            cmd = _construct_fsleyes_syntax(viewer, files, im_types, minmax, opacities)
        elif viewer in ['itksnap', 'itk-snap']:
            cmd = _construct_itksnap_syntax(viewer, files, im_types)
        else:
            cmd = ""  # This should never be reached, because SUPPORTED_VIEWERS should match the 'if' cases exactly
        cmd_strings[viewer] = cmd

        if verbose:
            printv(cmd + "\n", verbose=1, type='info')

    return cmd_strings


def _construct_fslview_syntax(viewer, files, im_types, minmax, opacities, mode):
    cmd = viewer
    # add mode (only supported by fslview for the moment)
    if mode:
        cmd += ' -m ' + mode
    for i in range(len(files)):
        cmd += ' ' + files[i]
        if im_types:
            if im_types[i]:
                cmd += ' -l ' + IMTYPES_COLORMAP[im_types[i]]['fslview']
        if minmax:
            if minmax[i]:
                cmd += ' -b ' + minmax[i]  # a,b
        if opacities:
            if opacities[i]:
                cmd += ' -t ' + opacities[i]
    cmd += ' &'

    return cmd


def _construct_fsleyes_syntax(viewer, files, im_types, minmax, opacities):
    cmd = viewer
    for i in range(len(files)):
        cmd += ' ' + files[i]
        if im_types:
            if im_types[i]:
                cmd += ' -cm ' + IMTYPES_COLORMAP[im_types[i]]['fsleyes']
        if minmax:
            if minmax[i]:
                cmd += ' -dr ' + ' '.join(minmax[i].split(','))  # a b
        if opacities:
            if opacities[i]:
                cmd += ' -a ' + str(float(opacities[i]) * 100)  # in percentage
    cmd += ' &'

    return cmd


def _construct_itksnap_syntax(viewer, files, im_types):
    # Split the image files into two categories: grayscale images (used for `-g`/`-o`) and seg images (used for `-s`)
    gray_images = []
    seg_images = []
    for i in range(len(files)):
        if not im_types:
            gray_images.append(files[i])
        else:
            colormap = IMTYPES_COLORMAP[im_types[i]]['itksnap']
            if colormap == 'gray':
                gray_images.append(files[i])
            elif colormap == 'seg':
                seg_images.append(files[i])
            else:
                raise ValueError(f"ITKSnap does not support colormap '{colormap}'")

    # Construct ITKSnap command based on image types
    # 1. '-g' is the "main image" and it's mandatory: i.e. You can't just display a single seg image ('-s') by itself,
    #    or else itksnap will throw this error:
    #        "Error: Option -s must be used together with option -g"
    # NB: `-g` really should be a grayscale image, but if there are no gray images, we fall back to using a seg image.
    main_image = (gray_images or seg_images).pop(0)
    cmd = f"{viewer} -g {main_image}"
    # 2. '-o' is used for any remaining grayscale images not used as the main image (`-g`)
    if gray_images:
        cmd += f" -o {' '.join(gray_images)}"
    # 3. '-s' is used for any images with 1 value (binary segmentations) or >1 values (labeled segmentations).
    #    NB: There can only be one segmentation per ITKSnap command. (ITKSnap can't toggle segmentations like FSLeyes.)
    #        To get around this, we duplicate the command so that there is one command per segmentation.
    if seg_images:
        cmd = "\n".join([f"{cmd} -s {seg_image}" for seg_image in seg_images])

    return cmd


class SCTArgumentParser(argparse.ArgumentParser):
    """
        Parser that centralizes initialization steps common across all SCT scripts.

        TODO: Centralize `-v`, `-r`, and `-h` arguments here too, as they're copied
              and pasted across all SCT scripts.
    """
    def __init__(self, *args, **kwargs):
        def update_parent_default(key, value):
            """A polite way of letting a child class have different default values than the parent class."""
            # Source: https://stackoverflow.com/a/41623488
            argspec = inspect.getfullargspec(super(SCTArgumentParser, self).__init__)
            arg_index = argspec.args.index(key)
            if len(args) < arg_index and key not in kwargs:
                kwargs[key] = value

        update_parent_default('formatter_class', SmartFormatter)

        # Update "usage:" message to match how SCT scripts are actually called (no '.py')
        frame = inspect.stack()[1]
        module = inspect.getmodule(frame[0])
        update_parent_default('prog', removesuffix(os.path.basename(module.__file__), ".py"))

        # Disable "add_help", because it won't properly add '-h' to our custom argument groups
        # (We use custom argument groups because of https://stackoverflow.com/a/24181138)
        update_parent_default('add_help', False)

        super(SCTArgumentParser, self).__init__(*args, **kwargs)

    def error(self, message):
        """
            Overridden parent method. Ensures that help is printed when called with invalid args.

            See https://github.com/spinalcordtoolbox/spinalcordtoolbox/issues/3137.
        """
        # Source: https://stackoverflow.com/a/4042861
        self.print_help(sys.stderr)
        message_formatted = (ANSIColors16.Bold + ANSIColors16.LightRed
                             + f'\n{self.prog}: error: {message}\n\n'
                             + ANSIColors16.ResetAll)
        self.exit(2, message_formatted)


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
        folder_name = os.path.normpath(folder_name)
        os.makedirs(folder_name, exist_ok=True)
        return folder_name

    def __call__(self, parser, namespace, values, option_string=None):
        if isinstance(values, list):
            folders = list(map(self.create_folder, values))
        else:
            folders = self.create_folder(values)

        # Add the attribute
        setattr(namespace, self.dest, folders)


def list_type(delimiter, subtype):
    """
        Factory function that returns a list parsing function, which can be
        used with argparse's `type` option. This allows for more complex type
        parsing, and preserves the behavior of the old msct_parser.
    """
    def list_typecast_func(string):
        return [subtype(v) for v in string.split(delimiter)]

    return list_typecast_func


class Metavar(str, Enum):
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


class SmartFormatter(argparse.ArgumentDefaultsHelpFormatter):
    """Custom formatter that inherits from HelpFormatter to apply the same
    tweaks across all of SCT's scripts."""
    def __init__(self, *args, **kw):
        self._add_defaults = None
        super(SmartFormatter, self).__init__(*args, **kw)
        # Tweak: Update argparse's '_width' to match Terminal width
        try:
            self._width = shutil.get_terminal_size()[0]
        except (KeyError, ValueError):
            logger.warning('Not able to fetch Terminal width. Using default: %s', self._width)

    def _get_help_string(self, action):
        """Overrides the default _get_help_string method to skip writing the
        '(default: )' text for arguments that have an empty default value."""
        if action.default not in [None, "", [], (), {}]:
            return super()._get_help_string(action)
        else:
            return action.help

    def _fill_text(self, text, width, indent):
        """Overrides the default _fill_text method. It takes a single string
        (`text`) and rebuilds it so that each line wraps at the specified
        `width`, while also preserving newlines.

        This method is what gets called for the parser's `description` field.
        """
        # NB: We use our overridden split_lines method to apply indentation to the help description
        paragraphs = self._split_lines(text, width)
        return '\n'.join(paragraphs)

    def _split_lines(self, text, width):
        """Overrides the default _split_lines method. It takes a single string
        (`text`) and rebuilds it so that each line wraps at the specified
        `width`, while also preserving newlines, as well as any offsets within
        the text (e.g. indented lists).

        This method is what gets called for each argument's `help` field.
        """
        import textwrap
        # NB: text.splitlines() is what's used by argparse.RawTextHelpFormatter
        #     to preserve newline characters (`\n`) in text.
        lines = text.splitlines()
        # NB: The remaining code is fully custom
        while lines[0] == '':  # Discard empty start lines
            lines = lines[1:]
        offsets = [re.match("^[ \t]*", line).group(0) for line in lines]
        wrapped = []
        for i, li in enumerate(lines):
            li = li.rstrip()  # strip trailing whitespace
            if len(li) > 0:
                # Check for ANSI graphics control sequences, and increase width to compensate
                width_adjusted = width + len("".join(re.findall("\\x1b\[[0-9;]+m", li)))  # noqa: W605
                # Split the line into two parts: the first line, and wrapped lines
                init_wrap = textwrap.fill(li, width_adjusted).splitlines()
                first = init_wrap[0]
                rest = "\n".join(init_wrap[1:])
                # Add an offset to the wrapped lines so that they're indented the same as the first line
                o = offsets[i]
                if re.match(r"^\s+[-*]\s\w.*$", li):  # List matching: " - Text" or " * Text"
                    o += "  "  # If the line is a list item, add extra indentation to the wrapped lines (#2889)
                ol = len(o)
                rest_wrap = textwrap.fill(rest, width_adjusted - ol).splitlines()
                offset_lines = [o + wl for wl in rest_wrap]
                # Merge the first line and the wrapped lines
                wrapped = wrapped + [first] + offset_lines
            else:
                wrapped = wrapped + [li]
        return wrapped


def parse_num_list(str_num):
    """
    Parse numbers in string based on delimiter ',' or ':'

    .. note::
        Examples:
        '' -> []
        '1,2,3' -> [1, 2, 3]
        '1:3,4' -> [1, 2, 3, 4]
        '1,1:4' -> [1, 2, 3, 4]

    :param str_num: str
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
            list_num += [x for x in range(a, b + 1) if x not in list_num]
            continue
        raise ValueError("unexpected group element {} group spec {}".format(element, str_num))

    return list_num


def get_interpolation(program, interp):
    """
    Get syntax on interpolation field depending on program. Supported programs: ants, flirt, WarpImageMultiTransform
    :param program:
    :param interp:
    :return:
    """
    # TODO: check if field and program exists
    interp_program = ''
    # FLIRT
    if program == 'flirt':
        if interp == 'nn':
            interp_program = ' -interp nearestneighbour'
        elif interp == 'linear':
            interp_program = ' -interp trilinear'
        elif interp == 'spline':
            interp_program = ' -interp spline'
    # ANTs
    elif program == 'ants' or program == 'ants_affine' or program == 'isct_antsApplyTransforms' \
            or program == 'isct_antsSliceRegularizedRegistration' or program == 'isct_antsRegistration':
        if interp == 'nn':
            interp_program = ' -n NearestNeighbor'
        elif interp == 'linear':
            interp_program = ' -n Linear'
        elif interp == 'spline':
            interp_program = ' -n BSpline[3]'
    # check if not assigned
    if interp_program == '':
        logger.warning('%s: interp_program not assigned. Using linear for ants_affine.', os.path.basename(__file__))
        interp_program = ' -n Linear'
    # return
    return interp_program.strip().split()


def parse_num_list_inv(list_int):
    """
    Take a list of numbers and output a string that reduce this list based on delimiter ';' or ':'

    .. note::
        Note: we use ; instead of , for compatibility with csv format.
        Examples:
        [] -> ''
        [1, 2, 3] --> '1:3'
        [1, 2, 3, 5] -> '1:3;5'

    :param list_int: list: list of ints
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
        if list_int[i] == list_int[i - 1] + 1:
            # if ":" already there, update the last chars (based on the number of digits)
            if colon_is_present:
                str_num = str_num[:-len(str(list_int[i - 1]))] + str(list_int[i])
            # if not, add it along with the new int value
            else:
                str_num += ':' + str(list_int[i])
                colon_is_present = True
        # I(i-1) != I(i)-1
        else:
            str_num += ';' + str(list_int[i])
            colon_is_present = False

    return str_num
