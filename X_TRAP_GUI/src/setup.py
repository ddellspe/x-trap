'''
Created on Feb 21, 2011

@author: Collin
'''

from distutils.core import setup
from py2exe import *
import sys

#setup(windows=['Driver.py'])
sys.argv.append('py2exe')
setup(
windows = [
{
"script": 'guiStuff.py',
"icon_resources": [(1, "iowa_logo.ico")]
}
],
)