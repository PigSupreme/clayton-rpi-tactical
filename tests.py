#!/usr/bin/env python
#pylint: disable=line-too-long
'''
    Run me for unit tests!
'''
# for python3 compat
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import print_function

import os
import sys
import unittest

import subprocess

class WestWorldTests(unittest.TestCase):
    ''' Test the program for sanity '''

    def test_output(self):
        '''does the sample output look like it should?'''
        proc = subprocess.Popen(['./westworld2.py'],
                                stdout=subprocess.PIPE, 
                                stderr=subprocess.PIPE)
        output, stderrs = proc.communicate()

        sample = ''
        with open('sample_output.txt', 'r') as _fd:
            sample = _fd.read()

        result = False
        if str(sample) == str(output):
            result = False

        self.assertTrue(result, msg="Sample doesn't match output")


if __name__ == '__main__':
    if os.getcwd() not in sys.path:
        sys.path.insert(0, os.getcwd())

    print('------------')
    print('Python Search Path:')
    for PATH in sys.path:
        print("  " + PATH)
    print('------------')

    unittest.main()

