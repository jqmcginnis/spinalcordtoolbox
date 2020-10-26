#!/usr/bin/env python
#########################################################################################
#
# Test function for sct_label_vertebrae
#
# ---------------------------------------------------------------------------------------
# Copyright (c) 2017 Polytechnique Montreal <www.neuro.polymtl.ca>
# Author: Julien Cohen-Adad
#
# About the license: see the file LICENSE.TXT
#########################################################################################


def init(param_test):
    """
    Initialize class: param_test
    """
    # initialization
    default_args = ['-i t2/t2.nii.gz -s t2/t2_seg-manual.nii.gz -c t2 -initfile t2/init_label_vertebrae.txt -t template -qc testing-qc',
                    '-i t2/t2.nii.gz -s t2/t2_seg-manual.nii.gz -c t2 -discfile t2/labels.nii.gz']
    # assign default params
    if not param_test.args:
        param_test.args = default_args
    return param_test


def test_integrity(param_test):
    """
    Test integrity of function
    """
    param_test.output += '\nNot implemented.'
    # TODO: implement integrity testing
    return param_test
