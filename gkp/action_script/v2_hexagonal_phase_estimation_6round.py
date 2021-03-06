# -*- coding: utf-8 -*-
"""
Created on Sun Jul  5 20:59:13 2020

@author: Vladimir Sivak
"""

import tensorflow as tf
from numpy import sqrt, pi, exp, real, imag

delta = 0.19
eps = 0.19

period = 6

b_amp = sqrt(8*pi/sqrt(3))
a_amp = sqrt(2*pi/sqrt(3))

### Script of actions

# [S_x, trim x, S_y, trim y, S_z,  trim z]
# Trimming and feedback are done in the orthogonal direction to stabilizers
script = {
    'alpha' : [[real(1j*a_amp*exp(-0j*pi/3)), imag(1j*a_amp*exp(-0j*pi/3))], 
               [real(delta*exp(-2j*pi/3)), imag(delta*exp(-2j*pi/3))],
               [real(1j*a_amp*exp(-2j*pi/3)), imag(1j*a_amp*exp(-2j*pi/3))],
               [real(delta*exp(-1j*pi/3)), imag(delta*exp(-1j*pi/3))],
               [real(1j*a_amp*exp(-1j*pi/3)), imag(1j*a_amp*exp(-1j*pi/3))],
               [real(delta*exp(-0j*pi/3)), imag(delta*exp(-0j*pi/3))]],
    'beta'  : [[real(1j*b_amp*exp(-2j*pi/3)), imag(1j*b_amp*exp(-2j*pi/3))],
               [real(-eps*exp(-2j*pi/3)), imag(-eps*exp(-2j*pi/3))],
               [real(1j*b_amp*exp(-1j*pi/3)), imag(1j*b_amp*exp(-1j*pi/3))],
               [real(-eps*exp(-1j*pi/3)), imag(-eps*exp(-1j*pi/3))],
               [real(1j*b_amp*exp(-0j*pi/3)), imag(1j*b_amp*exp(-0j*pi/3))],
               [real(-eps*exp(-0j*pi/3)), imag(-eps*exp(-0j*pi/3))]],
    'phi' : [[pi/2]]*6,
    'theta' : [[0.0]]*6
    }
    

# Mask 1 allows the ActionWrapper to use the learned value of the action on
# that time step, while 0 allows to use the scripted value.
mask = {
    'alpha' : [0, 1]*3,
    'beta'  : [0, 1]*3,
    'phi'   : [1]*6,
    'theta' : [1]*6
    }