# coding: utf8
# Copyright 2014-2017 CERN. This software is distributed under the
# terms of the GNU General Public License version 3 (GPL Version 3),
# copied verbatim in the file LICENSE.md.
# In applying this license, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental Organization or
# submit itself to any jurisdiction.
# Project website: http://blond.web.cern.ch/

'''
**Function(s) for pre-processing input data**

:Authors: **Helga Timko**, **Alexandre Lasheen**, **Danilo Quartullo**,
    **Simon Albright**
'''

from __future__ import division
from builtins import str, range
import numpy as np
import matplotlib.pyplot as plt
from plots.plot import fig_folder
from scipy.interpolate import splrep, splev


class PreprocessRFParams(object):
    r""" Class to preprocess the RF data (voltage, phase, harmonic) for 
    RFStation, interpolating it to every turn.
    
    Parameters
    ----------
    interpolation : str    
        Interpolation options for the data points. Available options are 
        'linear' (default) and 'cubic'        
    smoothing : float
        Smoothing value for 'cubic' interpolation
    plot : bool
        Option to plot interpolated arrays; default is False
    figdir : str
        Directory to save optional plot; default is 'fig'
    figname : list of str
        Figure name to save optional plot; default is 'data', different arrays
        will have figures with different indices
    sampling : int
        Decimation value for plotting; default is 1
    harmonic : bool
        Switch to pre-process harmonic; default is False
    voltage : bool
        Switch to pre-process RF voltage; default is True
    phi_rf_d : bool
        Switch to pre-process RF phase; default is False
    
    """

    def __init__(self, interpolation = 'linear', smoothing = 0, plot = False, 
                 figdir = 'fig', figname = ['data'], sampling = 1, 
                 harmonic = False, voltage = True, phi_rf_d = False, 
                 omega_rf = False):
    
        if interpolation in ['linear', 'cubic']:
            self.interpolation = str(interpolation)
        else:    
            raise RuntimeError("ERROR: Interpolation scheme in"+
                " PreprocessRFParams not recognised. Aborting...")
        self.smoothing = float(smoothing)
        if plot == True or plot == False:
            self.plot = bool(plot)
        else: 
            raise RuntimeError("ERROR: plot value in PreprocessRamp"+
                               " not recognised. Aborting...")            
        self.figdir = str(figdir)
        self.figname = str(figname)
        if sampling > 0:
            self.sampling = int(sampling)
        else:
            raise RuntimeError("ERROR: sampling value in PreprocessRamp"+
                               " not recognised. Aborting...")
        self.harmonic = harmonic
        self.voltage = voltage
        self.phi_rf_d = phi_rf_d
        self.omega_rf = omega_rf            
    
    
    def preprocess(self, Ring, time_arrays, data_arrays):
        r"""Function to pre-process RF data, interpolating it to every turn.

        Parameters
        ----------
        Ring : class
            A Ring type class
        time_arrays : list of float arrays
            Time corresponding to data points; input one array for each data 
            array
        data_arrays : list of float arrays
            Data arrays to be pre-processed; can have different units
        
        Returns
        -------
        list of float arrays
            Interpolated data [various units]

        """
        
        cumulative_time = Ring.cycle_time
        time_arrays = time_arrays
        data_arrays = data_arrays
 
        # Create list where interpolated data will be appended
        data_interp = []
        
        # Interpolation done here
        for i in range(len(time_arrays)):
            if len(time_arrays[i]) != len(data_arrays[i]):
                raise RuntimeError("ERROR: number of time and data arrays in"+
                                   " PreprocessRFParams do not match!")
            if self.interpolation == 'linear':
                data_interp.append(np.interp(cumulative_time, time_arrays[i], 
                                             data_arrays[i]))
            elif self.interpolation == 'cubic':
                interp_funtion = splrep(time_arrays[i], data_arrays[i], 
                                        s = self.smoothing)
                data_interp.append(splev(cumulative_time, interp_funtion))
                
        # Plot original and interpolated data       
        if self.plot:
            # Directory where plots will be stored
            fig_folder(self.figdir)
            
            # Plot
            for i in range(len(time_arrays)):
                plt.figure(1, figsize=(8,6))
                ax = plt.axes([0.15, 0.1, 0.8, 0.8])
                ax.plot(cumulative_time[::self.sampling], 
                        data_interp[i][::self.sampling], 
                        label = 'Interpolated data')
                ax.plot(time_arrays[i], data_arrays[i], '.', 
                        label = 'Input data', color='r')
                ax.set_xlabel('Time [s]')    
                ax.set_ylabel ("%s" %self.figname[i])
                ax.legend = plt.legend(bbox_to_anchor = (0., 1.02, 1., .102), 
                    loc = 3, ncol = 2, mode = 'expand', borderaxespad = 0.)
    
                # Save figure
                fign = self.figdir + '/preprocess_' "%s" %self.figname + \
                    '_' "%d" %i +'.png'
                plt.savefig(fign)
                plt.clf()     
     
        return data_interp



def combine_rf_functions(function_list, merge_type='linear', resolution=1e-3, 
                         Ring=None, main_h=True):


    r"""Function to combine different RF programs. Each program is passed in a
    tuple with complete function (single valued or numpy array) and 2-list
    [start_time, stop_time].

    Parameters
    ----------
    function_list : list of tuples
        each tuple has form (function, [start_time, stop_time])
        function can be a numpy.ndarray of format [time, value] or single valued
        if function is single valued it will be assumed constant from start_time to stop_time
        if function is numpy.ndarray it will be truncated to start_time, stop_time
    merge_type : str
        string signifying type of merge available, options are:
            linear : function will be linearly interpolated from function_1[stop_time] to function_2[start_time]
            isoadiabatic : designed for voltage functions and intended to maintain adiabaticity during change of voltage, best suited to flat momentum sections
            linear_tune : for use with voltages, provides a linear change in the tune from function_1[stop_time] to function_2[start_time]
    resolution : float
        the time in seconds between points of the interpolation
    Ring : class
        A Ring type class, only used with linear_tune merge_type
    main_h : boolean
        if main_h is True dE is considered in linear_tune merge_type, otherwise dE is set to 0

    Returns
    -------
    2 dimensional numpy.ndarray containing [time, value] of merged functions

        """

    nFunctions = len(function_list)

    if not isinstance(merge_type, list):
        merge_type = (nFunctions-1)*[merge_type]
    if not isinstance(resolution, list):
        resolution = (nFunctions-1)*[resolution]
   
    if len(merge_type) != nFunctions:
        raise RuntimeError("ERROR: merge_type list wrong length")
    if len(resolution) != nFunctions:
        raise RuntimeError("ERROR: resolution list wrong length")
 
    timePoints = []
    for i in range(nFunctions):
        timePoints += function_list[i][1]
    if not np.all(np.diff(timePoints)) > 0:
        raise RuntimeError("ERROR: in combine_rf_functions, times are not"+
                           " monotonically increasing!")
    
    fullFunction = []
    fullTime = []
   

    #Determines if 1st function is single valued or array and stores values
    if not isinstance(function_list[0][0], np.ndarray):
        fullFunction += 2*[function_list[0][0]]
        fullTime += function_list[0][1]
    
    else:
        start = np.where(function_list[0][0][0] > function_list[0][1][0])[0][0]
        stop = np.where(function_list[0][0][0] > function_list[0][1][1])[0][0]

        funcTime = [function_list[0][1][0]] + \
            function_list[0][0][0][start:stop].tolist() + \
            [function_list[0][1][1]]
        funcProg = np.interp(funcTime, function_list[0][0][0], 
                             function_list[0][0][1])
        
        fullFunction += funcProg.tolist()
        fullTime += funcTime

    
    #Loops through remaining functions merging them as requested and storing results
    for i in range(1, nFunctions):
        
        if merge_type[i-1] == 'linear':
            
            if not isinstance(function_list[i][0], np.ndarray):
                fullFunction += 2*[function_list[i][0]]
                fullTime += function_list[i][1]
                
            else:
                start = np.where(function_list[i][0][0] >= 
                                 function_list[i][1][0])[0][0]
                stop = np.where(function_list[i][0][0] >= 
                                function_list[i][1][1])[0][0]
                
                funcTime = [function_list[i][1][0]] + \
                    function_list[i][0][0][start:stop].tolist() + \
                    [function_list[i][1][1]]
                funcProg = np.interp(funcTime, function_list[i][0][0], 
                                     function_list[i][0][1])
                
                fullFunction += funcProg.tolist()
                fullTime += funcTime
                
        elif merge_type[i-1] == 'isoadiabatic':
            
            if not isinstance(function_list[i][0], np.ndarray):
                
                tDur = function_list[i][1][0] - fullTime[-1]
                Vinit = fullFunction[-1]
                Vfin = function_list[i][0]
                k = (1./tDur)*(1-(1.*Vinit/Vfin)**0.5)
                
                nSteps = int(tDur/resolution[i-1])
                time = np.linspace(fullTime[-1], function_list[i][1][0], 
                                   nSteps)
                volts = Vinit/((1-k*(time-time[0]))**2)
                
                fullFunction += volts.tolist() + 2*[function_list[i][0]]
                fullTime += time.tolist() + function_list[i][1]
                
            else:
                
                start = np.where(function_list[i][0][0] >= 
                                 function_list[i][1][0])[0][0]
                stop = np.where(function_list[i][0][0] >= 
                                function_list[i][1][1])[0][0]
                
                funcTime = [function_list[i][1][0]] + \
                    function_list[i][0][0][start:stop].tolist() + \
                    [function_list[i][1][1]]
                funcProg = np.interp(funcTime, function_list[i][0][0], 
                                     function_list[i][0][1])
                
                tDur = funcTime[0] - fullTime[-1]
                Vinit = fullFunction[-1]
                Vfin = funcProg[0]
                k = (1./tDur)*(1-(1.*Vinit/Vfin)**0.5)
                
                nSteps = int(tDur/resolution[i-1])
                time = np.linspace(fullTime[-1], funcTime[0], nSteps)
                volts = Vinit/((1-k*(time-time[0]))**2)
                
                fullFunction += volts.tolist() + funcProg.tolist()
                fullTime += time.tolist() + funcTime
                
        elif merge_type[i-1] == 'linear_tune':
            
            #harmonic, charge and 2pi are constant so can be ignored
            if not isinstance(function_list[i][0], np.ndarray):
                
                initPars = Ring.parameters_at_time(fullTime[-1])
                finalPars = Ring.parameters_at_time(function_list[i][1][0])
                
                vInit = fullFunction[-1]
                vFin = function_list[i][0]
                
                if main_h is False:
                    initPars['delta_E'] = 0.
                    finalPars['delta_E'] = 0.
                    
                initTune = np.sqrt( (vInit * np.abs(initPars['eta_0']) * 
                    np.sqrt(1 - (initPars['delta_E']/vInit)**2)) / 
                    (initPars['beta']**2 * initPars['energy']) )
                finalTune = np.sqrt( (vFin * np.abs(finalPars['eta_0']) *
                    np.sqrt(1 - (finalPars['delta_E']/vFin)**2)) /
                    (finalPars['beta']**2 * finalPars['energy']) )
                
                tDur = function_list[i][1][0] - fullTime[-1]
                nSteps = int(tDur/resolution[i-1])
                time = np.linspace(fullTime[-1], function_list[i][1][0],
                                   nSteps)
                tuneInterp = np.linspace(initTune, finalTune, nSteps)
                
                mergePars = Ring.parameters_at_time(time)
                
                if main_h is False:
                    mergePars['delta_E'] *= 0
                    
                volts = np.sqrt( ((tuneInterp**2 * mergePars['beta']**2 * 
                    mergePars['energy']) / (np.abs(mergePars['eta_0'])))**2 + 
                    mergePars['delta_E']**2)
                
                fullFunction += volts.tolist() + 2*[function_list[i][0]]
                fullTime += time.tolist() + function_list[i][1]
                
            else:
                
                start = np.where(function_list[i][0][0] >= 
                                 function_list[i][1][0])[0][0]
                stop = np.where(function_list[i][0][0] >= 
                                function_list[i][1][1])[0][0]
                
                funcTime = [function_list[i][1][0]] + \
                    function_list[i][0][0][start:stop].tolist() + \
                    [function_list[i][1][1]]
                funcProg = np.interp(funcTime, function_list[i][0][0], 
                                     function_list[i][0][1])
                
                tDur = funcTime[0] - fullTime[-1]
                nSteps = int(tDur/resolution[i-1])
                time = np.linspace(fullTime[-1], funcTime[0], nSteps)
                
                initPars = Ring.parameters_at_time(fullTime[-1])
                finalPars = Ring.parameters_at_time(funcTime[0])
                
                if main_h is False:
                    initPars['delta_E'] = 0.
                    finalPars['delta_E'] = 0.
                    
                vInit = fullFunction[-1]
                vFin = funcProg[0]
                
                initTune = np.sqrt( (vInit * np.abs(initPars['eta_0']) * 
                    np.sqrt(1 - (initPars['delta_E']/vInit)**2)) / 
                    (initPars['beta']**2 * initPars['energy']) )
                finalTune = np.sqrt( (vFin * np.abs(finalPars['eta_0']) * 
                    np.sqrt(1 - (finalPars['delta_E']/vFin)**2)) / 
                    (finalPars['beta']**2 * finalPars['energy']) )
                tuneInterp = np.linspace(initTune, finalTune, nSteps)
                
                mergePars = Ring.parameters_at_time(time)
                
                if main_h is False:
                    mergePars['delta_E'] *= 0
                    
                volts = np.sqrt( ((tuneInterp**2 * mergePars['beta']**2 * 
                    mergePars['energy']) / (np.abs(mergePars['eta_0'])))**2 + 
                    mergePars['delta_E']**2)
                
                fullFunction += volts.tolist() + funcProg.tolist()
                fullTime += time.tolist() + funcTime

        else:
            raise RuntimeError("ERROR: merge_type not recognised")
                
                
    returnFunction = np.zeros([2, len(fullTime)])
    returnFunction[0] = fullTime
    returnFunction[1] = fullFunction
    
    return returnFunction

