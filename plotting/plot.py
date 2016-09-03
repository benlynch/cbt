#!/usr/bin/python
import random
import argparse
import fnmatch
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.axes as ax
import pandas as pd
import numpy as np
import hashlib
import os
import re
import sys
import yaml
sys.path.insert(0, "/home/ubuntu/cbt/parsing")
import database

def bar_label(ax, rects, semilog):
    (y_bottom, y_top) = ax.get_ylim()
    y_height = y_top - y_bottom
    for rect in rects:
        height = rect.get_height()
        p_height = (height / y_height)
        if semilog:
            if p_height > 0.95: 
                label_position = height*(0.95)
            else:
                label_position = height*(1.05)
        else: 
            if p_height > 0.95: 
                label_position = height - (y_height * 0.05)
            else:
                label_position = height + (y_height * 0.01)
        ax.text(rect.get_x() + rect.get_width()/2., label_position,
                '%5.2f' % height,
                ha='center', va='bottom')

def check_graph_options (doc):
    if 'radosbench' in doc.keys():
        if isinstance(doc['radosbench']["write"]["x"]["sizes"], list):
            print("looks good")
        else:
            print("Not sure what to plot")
            parser.print_help()
            sys.exit()        
    return;

def create_rados_graphs( params ):
    pcolors = ['#0d3c55', '#c02e1d','#f16c20','#ebc844','#a2b86c','#1395ba']
    semilog = False
    iteration = 0
    if params["write"]["y"]["log"] == True:
      semilog = True
    if 'write' in params.keys():
        y_values = []
        xs = params["write"]["x"]["sizes"]
        concurrent = params["write"]["x"]["concurrent"]
        for testtype in args.archive:
            ys = []
            for size in xs:
                ys.append(rados_get_write_bandwidth(testtype, size))
            y_values.append(ys)
    super_series = []
    for ys in y_values:
        series = pd.Series.from_array(ys)
        super_series.append(series)

  #  plt.figure(figsize=(9, 6))

    if len(super_series) > 1:
    #plot comparison from multiple archives
        rect_refs = []
        width = 0.35
        ind = np.arange(len(xs))
        fig, ax = plt.subplots()
        bar_shift = width/2
        for series in super_series:
            color = pcolors.pop()
            rects = ax.bar(ind + bar_shift, series, width, color=color)
            rect_refs.append(rects[0])
            if semilog:
              ax.set_yscale('log')
            bar_shift += width
            if params["write"]["y"]["bar_label"]:
                bar_label(ax, rects, semilog)
        ax.set_xticks(ind + width*3/2)
        ax.legend(rect_refs, params['legend']['labels'], loc=2)
    else:
        width = 0.5
        color = pcolors.pop()
        ind = np.arange(len(xs))
        fig, ax =  plt.subplots()
        rects = ax.bar(ind + width, series, color=color)
        ax.set_xticks(ind + width*3/2)
        if semilog:
            ax.set_yscale('log')
    
        if params["write"]["y"]["bar_label"]:
            bar_label(ax, rects, semilog)

    fig.set_size_inches(9,6)
    ax.set_xticklabels(xs, rotation=0)
    ax.set_title(args.title)
    ax.set_xlabel("Object Size (Bytes)")
    ax.set_ylabel('MB/s')
    plt.savefig('foo.png')
    return;

def find(pattern, path):
    result = []
    for root, dirs, files in os.walk(path):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                result.append(os.path.join(root, name))
    return result

def getbw(s):
    if "GB/s" in s:
        return float(s[:-4])*1024
    if "MB/s" in s:
        return float(s[:-4])
    if "KB/s" in s:
        return float(s[:-4])/1024

def mkhash(values):
    value_string = ''.join([str(i) for i in values])
    return hashlib.sha256(value_string).hexdigest()

def parse_output( test ):
    if test == 'radosbench':
        database.create_db()
        files = []
        for archive in args.archive:
            print(archive)
            files.extend(find('output.*', archive))
        for inputname in files:
            params = inputname.split("/")
            print(params) 
            # make readahead into an int
            params[3] = int(params[3][7:])
            # Make op_size into an int
            params[4] = int(params[4][8:])
            # Make cprocs into an int
            params[5] = int(params[5][17:])
            params[7] = params[6]
            params[6] = random.random() 
            params_hash = mkhash(params)
            params = [params_hash] + params
            params.extend([0,0])
            print(params)
            database.insert(params)
            pattern = re.compile('Bandwidth \(MB/sec\):\s+(\d+\.\d+)')
            for line in open(inputname):
                m = pattern.match(line)
                if m:
                    bw = float(m.group(1))
                    print params[8]
                    if  params[8] == 'write':
                        database.update_writebw(params_hash, bw)
                    else:
                        database.update_readbw(params_hash, bw)
    if test == 'fio':
        print("soon")
# FORMAT=['hash', 'testname', 'iteration', 'benchmark', 'osdra', 'opsize', 'cprocs', 'iodepth', 'testtype', 'writebw', 'readbw']
# new/00000000/Radosbench/osd_ra-00004096/op_size-00004096/concurrent_ops-00000002/seq

def rados_get_write_bandwidth( testname, size ):
    print testname
    mytable = database.fetch_bw(testname, ['write',size])
    return float(mytable[0][1]); 

def splits(s,d1,d2):
    l,_,r = s.partition(d1)
    m,_,r = r.partition(d2)
    return m


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Graph output from CBT')
    parser.add_argument('--archive', nargs='+', type=str, required=True, help='Archive directory of output')
    parser.add_argument('--config', nargs='?', type=str, required=True, help='YAML descriptin of graph to produce')
    parser.add_argument('--title', nargs='?', type=str, help='Title of the graph')
    args = parser.parse_args()

    for path in (args.archive):
        if os.path.isdir(path):
            print(" ")
        else:
            print("Archive directory does not exist")
            parser.print_help()
            sys.exit()

    with open(args.config, 'r') as f:
        doc = yaml.load(f)

    check_graph_options(doc)

    if 'radosbench' in doc.keys():
        print("Reading RADOS Bench output")
        if 'write' in doc['radosbench'].keys():
            parse_output('radosbench')
            create_rados_graphs( doc['radosbench'] )   


#FORMAT=['hash', 'testname', 'iteration', 'benchmark', 'osdra', 'opsize', 'cprocs', 'iodepth', 'testtype', 'writebw', 'readbw']

