import matplotlib.pyplot as plt
import numpy as np
from lofasm.bbx import bbx
from glob import glob
import os, sys
from copy import deepcopy


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('-o', '--output', type=str,
            help="path to output file. '-' to output to stdout", nargs='?',
            default='a.out', const='a.out')
    p.add_argument('infiles', action="extend", nargs="+", type=str,
            help="list of input files to be processed")
    p.add_argument('-s', '--stepsize', type=int, default=10,
            help='downsample cadence') 
    p.add_argument('-v', '--verbose', action='count', default=0, help='verbose')
    args = p.parse_args()
    def logmsg(x):
        if args.verbose:
            sys.stderr.write(str(x))

    stepSize = args.stepsize #collect every Nth sample
    if args.output == '-':
        outfile = sys.stdout.buffer
    else:
        outfile = args.output
    flist = args.infiles
    logmsg("stepsize: {}".format(stepSize))
    logmsg("type: {}".format(type(stepSize)))
    logmsg("Sorting {} input files".format(len(args.infiles)))
    flist.sort()

    # initialize lofasm file objects
    lfxs = [bbx.LofasmFile(f) for f in flist]
    Ntotal = 0
    totalDim1Span = 0.0
    # get total number of rows and dim1 span
    for f in lfxs:
        N = f.dim1_len
        Ntotal += N
        totalDim1Span += float(f.header['dim1_span'])
    logmsg("Starting with {} samples spanning {}s".format(Ntotal, totalDim1Span))

    NtotalSteps = Ntotal // stepSize
    NstepCount = 0
    hdr = deepcopy(lfxs[0].header)
    hdr['dim1_span'] = str(totalDim1Span)
    logmsg("Total span: {}s".format(totalDim1Span))
    hdr['metadata']['dim1_len'] = NtotalSteps
    logmsg("HEADER: {}".format(hdr))
    lfout = bbx.LofasmFile(outfile, header=hdr, mode='write', verbose=bool(args.verbose))
    logmsg("lfout HEADER: {}".format(lfout.header))
    dt = float(lfxs[0].dim1_span) / int(lfxs[0].dim1_len)

    # get number of columns from first file in list
    Ncols = lfxs[0].header['metadata']['dim2_len']
    dtype = np.float64 if lfxs[0].header['metadata']['complex']=='1' else np.complex128
    buf = np.zeros((1, Ncols), dtype=dtype)
    offset = 0
    for lfx in lfxs:
        logmsg("Starting file {}".format(lfx.fname))
        NrowsInFile = lfx.header['metadata']['dim1_len']
        logmsg("Rows in file: {}".format(NrowsInFile))
        lfx.read_data()
        data = lfx.get_data()
        lfx.close() # free resources
        ii = offset
        logmsg("offset: {}".format(offset))
        while True:
            drow = data[ii,:]
            lfout.add_data(drow)
            ii += stepSize
            if ii > NrowsInFile - 1:
                #EOF
                offset = ii - NrowsInFile
                logmsg("EOF offset: {}".format(offset))
                break
    else:
        # correct time span if there's an offset
        if offset:
            totalDim1Span = totalDim1Span - dt*(NrowsInFile-(stepSize-offset))
        logmsg('initial span: {}'.format(totalDim1Span))
        logmsg('dt: {}'.format(dt))
        logmsg('NrowsInFile: {}'.format(NrowsInFile))
        logmsg('offset: {}'.format(offset))
        logmsg("Total Span: {} seconds".format(totalDim1Span))
        lfout.header['dim1_span'] = str(totalDim1Span)

    logmsg(lfout.header)
    lfout.write()
    lfout.close()
