#!/usr/bin/env python
#
# Calculate b-value
#
# N.B. SI unit for gyromagnetic ratio is radian per second per tesla, therefore need to multiply by 2pi.
#
# Copyright (c) 2013 Polytechnique Montreal <www.neuro.polymtl.ca>
# License: see the file LICENSE

import sys
import math
from typing import Sequence

from spinalcordtoolbox.utils.sys import init_sct, printv, set_loglevel
from spinalcordtoolbox.utils.shell import Metavar, SCTArgumentParser


def main(argv: Sequence[str]):
    parser = get_parser()
    arguments = parser.parse_args(argv)
    verbose = arguments.v
    set_loglevel(verbose=verbose, caller_module_name=__name__)

    GYRO = float(42.576 * 10 ** 6)  # gyromagnetic ratio (in Hz.T^-1)
    gradamp = []
    bigdelta = []
    smalldelta = []
    gradamp = arguments.g
    bigdelta = arguments.b
    smalldelta = arguments.d

    # printv(arguments)
    printv('\nCheck parameters:')
    printv('  gradient amplitude ..... ' + str(gradamp) + ' mT/m')
    printv('  big delta .............. ' + str(bigdelta) + ' ms')
    printv('  small delta ............ ' + str(smalldelta) + ' ms')
    printv('  gyromagnetic ratio ..... ' + str(GYRO) + ' Hz/T')
    printv('')

    bvalue = (2 * math.pi * GYRO * gradamp * 0.001 * smalldelta * 0.001) ** 2 * (
        bigdelta * 0.001 - smalldelta * 0.001 / 3)

    printv('b-value = ' + str(bvalue / 10 ** 6) + ' mm^2/s\n')
    return bvalue


def get_parser():
    parser = SCTArgumentParser(
        description='Calculate b-value (in mm^2/s).'
    )

    mandatory = parser.add_argument_group("MANDATORY ARGUMENTS")
    mandatory.add_argument(
        "-g",
        type=float,
        required=True,
        help="Amplitude of diffusion gradients (in mT/m). Example: `40`",
        metavar=Metavar.float,
    )
    mandatory.add_argument(
        "-b",
        type=float,
        required=True,
        help="Big delta: time between both diffusion gradients (in ms). Example: `40`",
        metavar=Metavar.float,
    )
    mandatory.add_argument(
        "-d",
        type=float,
        required=True,
        help="Small delta: duration of each diffusion gradient (in ms). Example: `30`",
        metavar=Metavar.float,
    )

    optional = parser.add_argument_group("OPTIONAL ARGUMENTS")
    optional.add_argument(
        "-h",
        "--help",
        action="help",
        help="Show this help message and exit")
    optional.add_argument(
        '-v',
        metavar=Metavar.int,
        type=int,
        choices=[0, 1, 2],
        default=1,
        # Values [0, 1, 2] map to logging levels [WARNING, INFO, DEBUG], but are also used as "if verbose == #" in API
        help="Verbosity. 0: Display only errors/warnings, 1: Errors/warnings + info messages, 2: Debug mode")

    return parser


# =======================================================================================================================
# Start program
# =======================================================================================================================
if __name__ == "__main__":
    init_sct()
    main(sys.argv[1:])
