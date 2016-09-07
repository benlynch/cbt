import random
import fnmatch
#import matplotlib as mpl
#mpl.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.axes as ax
import pandas as pd
import numpy as np
import hashlib
import os
import re
import yaml
from os import listdir
import sys
sys.path.append("/home/support/blynch/cbt/parsing")
import database
import parsing
class cbtWorkspace:
    def __init__(self, path):
        self.path = path

    def __repr__(self):
        return "cbtWorkspace()"
 
    def __str__(self):
        return self.path

    def ls(self):
        return listdir(self.path)

    def plot_compare(self, benchmark_runs, test_type, fancy_title):
        args = {}
        args['path'] = self.path
        args['archive'] = benchmark_runs
        args['title'] = fancy_title
        doc = {'radosbench':{'write':{'x':{'sizes':[ 4096, 16384, 65536, 262144, 1048576, 4194304 ], 'concurrent':2},'y':{'log':True,'bar_label':True}}}}
   
        args['doc'] = doc

        if 'radosbench' in doc.keys():
            if 'write' in doc['radosbench'].keys():
                parse_output('radosbench', args)
                create_rados_graphs( doc['radosbench'], args)

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
            print("")
        else:
            print("Not sure what to plot")
            parser.print_help()
            sys.exit()
    return;

def create_rados_graphs( params, args ):
    pcolors = ['#0f5b78','#ef8b2c','#5ca793','#d94e1f','#117899','#ecaa38', '#0d3c55', '#c02e1d','#f16c20','#ebc844','#a2b86c','#1395ba']
    semilog = False
    iteration = 0
    if params["write"]["y"]["log"] == True:
      semilog = True
    if 'write' in params.keys():
        y_values = []
        xs = params["write"]["x"]["sizes"]
        concurrent = params["write"]["x"]["concurrent"]
        for testtype in args['archive']:
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
        ax.legend(rect_refs, args['archive'], loc=2)
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
    ax.set_title(args['title'])
    ax.set_xlabel("Object Size (Bytes)")
    ax.set_ylabel('MB/s')
    plt.show()
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
    value_string = (''.join([str(i) for i in values])).encode('utf-8')
    return hashlib.sha256(value_string).hexdigest()

def rados_get_write_bandwidth( testname, size ):
    mytable = database.fetch_bw(testname, ['write',size])
    return float(mytable[0][1]);




