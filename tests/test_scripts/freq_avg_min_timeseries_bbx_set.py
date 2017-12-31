#! /usr/bin/env python

'''
construct a time series of the data set by taking the average power in a frequency band
and taking the minimum value over a 5 minutes time span.
'''

import sys, os
import matplotlib
import numpy as np
matplotlib.use('agg')
import matplotlib.pyplot as plt
from lofasm.bbx import bbx
from lofasm.parse_data import freq2bin
from glob import glob
from copy import deepcopy

def freq_average_file(filename, freqs, bw=1.):
    '''
    take a list of frequency bands of width bw centered at freq from 
    each filterbank sample calculate the average over time.
    the minimum value of this averaged time series will be returned.

    Parameters
    ----------
    filename : str
        the data file to process
    freq : list
        list of the selected center frequencies in MHz
    bw : float, optional
        the bandwidth to include in the frequency averaging

    Returns
    -------
    freq_avg : numpy.array
                       array of frequency averaged time series minimum values,
                       each corresponding to its respective center
                       frequency at input
    '''

    lfx = bbx.LofasmFile(filename)
    lfx.read_data()
    freq_avg_list = []
    if isinstance(freqs, list):
        freqs.sort()
        for i in range(len(freqs)):
            lfbin = freq2bin(freqs[i] - bw / 2.)
            hfbin = freq2bin(freqs[i] + bw / 2.)
            num_fbins = hfbin - lfbin
            num_tbins = np.shape(lfx.data)[1]        
            avg_ts = np.average(lfx.data[lfbin:hfbin,:], axis=0)
            freq_avg_list.append(deepcopy(avg_ts))
        rows = len(freq_avg_list)
        cols = max([len(x) for x in freq_avg])
        data = np.zeros((rows,cols), dtype=np.float64)
        for i in range(rows):
            data[i,:] = freq_avg_list[i]
    else:
        lfbin = freq2bin(freqs - bw / 2.)
        hfbin = freq2bin(freqs + bw / 2.)
        num_fbins = hfbin - lfbin
        avg_ts = np.average(lfx.data[lfbin:hfbin,:], axis=0)
        data = avg_ts
        
    lfx.close()
    return data


def freq_averaged_minimum(filename, freqs, bw=1.):
    '''
    take a list of frequency bands of width bw centered at freq from 
    each filterbank sample calculate the average over time.
    the minimum value of this averaged time series will be returned.

    Parameters
    ----------
    filename : str
        the data file to process
    freq : list
        list of the selected center frequencies in MHz
    bw : float, optional
        the bandwidth to include in the frequency averaging

    Returns
    -------
    freq_avg_min_list : list
                       list of frequency averaged time series minimum values,
                       each corresponding to its respective center
                       frequency at input
    '''
    
    freq_avg = freq_average_file(filename, freqs, bw)
    if isinstance(freqs, list):
        mins = np.zeros(np.shape(freq_avg)[0], dtype=np.float64)
        for i in range(len(freqs)):
            mins[i] = np.min(freq_avg[i,:])
    else:
        mins = np.min(freq_avg)
    return mins

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('dataDir', type=str, help='path to data directory')
    p.add_argument('frequency', nargs='+', help='center frequency')
    p.add_argument('bandwidth', type=float, help='bandwidth to average')
    p.add_argument('--savedata', action='store_true',
                   help='save data as numpy file')
    args = p.parse_args()

    freqlist = [float(x) for x in args.frequency]
    freqlist.sort()
    flist = glob(os.path.join(args.dataDir, '*.bbx.gz'))
    flist.sort()

    N = len(flist)

    # get polarization from first bbx file header
    lfx = bbx.LofasmFile(flist[0])
    pol = lfx.header['channel']
    lfx.close()
    
    freqVTime = np.zeros((len(freqlist), N), dtype=np.float64)

    # loop over files
    for i in range(N):
        re = "Processing {}/{}".format(i+1, N)
        sys.stdout.write('\r'+re)
        sys.stdout.flush()
        freqVTime[:,i] = freq_averaged_minimum(flist[i], freqlist, args.bandwidth)

    if args.savedata:
        for i in range(len(freqlist)):
            d = freqVTime[i]
            d.tofile('freqAvgMinTimeSeries{}MHz_{}.numpy'.format(str(freqlist[i]), pol))


    plt.figure()
    for freq in freqlist:
        plt.title('frequency averaged timeseries {}MHz {}'.format(str(freq),pol))
        plt.plot(10*np.log10(freqVTime[freqlist.index(freq),:]), label='averaged time series')
        plt.legend()
        plt.savefig('frequency_averaged_minimum_timeseries_{}MHz_{}.png'.format(freq, pol), format='png')
        plt.clf()
