# coding: utf8
# Copyright 2014-2017 CERN. This software is distributed under the
# terms of the GNU General Public Licence version 3 (GPL Version 3), 
# copied verbatim in the file LICENCE.md.
# In applying this licence, CERN does not waive the privileges and immunities 
# granted to it by virtue of its status as an Intergovernmental Organization or
# submit itself to any jurisdiction.
# Project website: http://blond.web.cern.ch/

"""
Example for llrf.filters and llrf.cavity_feedback

:Authors: **Helga Timko**
"""

import numpy as np
from numpy.random import randn
from scipy.constants import e
import matplotlib.pyplot as plt 

from llrf.signal_processing import moving_average

n = 10000
n_ma = 100
iterations = 10

time = np.linspace(0, 10.e-6, n)
tau = 1.e-6
signal = 1 - np.exp(-time/tau) + 0.01*(np.random.randn(n) - 0.5)
time = np.linspace(0, 20.e-6, 2*n)
signal = np.concatenate((signal, signal))

plt.figure()
plt.plot(time, signal)
prev = 0.

for i in range(iterations):
    print("Average of end of previous signal", prev)
    signal = moving_average(signal, n_ma, prev)
    prev = np.mean(signal[-n_ma:])
    print("Length of signal", len(signal))
    plt.plot(time, signal)

plt.show()