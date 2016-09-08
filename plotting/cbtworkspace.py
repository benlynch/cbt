import matplotlib.pyplot as plt
import matplotlib.axes as ax
import pandas as pd
import numpy as np
import os
import re
from os import listdir
import sys
sys.path.append("/home/support/blynch/cbt/parsing")
import parse
class cbtWorkspace:
    def __init__(self, path):
        self.path = path

    def __repr__(self):
        return "cbtWorkspace()"
 
    def __str__(self):
        return self.path

    def ls(self):
        dirlist = []
        for file in listdir(self.path):
            if os.path.isdir(self.path + '/' + file):
                dirlist.append(file)
        return dirlist

    def bar_graph(self, benchmark_runs, test_type, title='Insert Fancy Title Here', object_sizes=[],
            log=True, bar_label=True):
        args = {}
        args['path'] = self.path
        args['archive'] = benchmark_runs
        args['title'] = title
        object_sizes=[ 4096, 16384, 65536, 262144, 1048576, 4194304 ]
        doc = {'radosbench':{'write':{'x':{'sizes':object_sizes, 'concurrent':2},'y':{'log':log,'bar_label':bar_label}}}}
        args['doc'] = doc
        if 'radosbench' in doc.keys():
            if 'write' in doc['radosbench'].keys():
                parse.parse_output('radosbench', args)
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

def create_bar_graph( data=[[[4096, 16384],[21.3, 34.1]]], semilog=False, add_bar_labels=True, title='Insert Fancy Title'):
    pcolors = ['#0f5b78','#ef8b2c','#5ca793','#d94e1f','#117899','#ecaa38', '#0d3c55', '#c02e1d','#f16c20','#ebc844','#a2b86c','#1395ba']
    if len(data) > 1:
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
            if add_bar_labels:
                bar_label(ax, rects, semilog)
        ax.set_xticks(ind + width*3/2)
        ax.legend(rect_refs, args['archive'], loc=2)
    else:
        width = 0.5
        color = pcolors.pop()
        xs = data[0][0]
        ys = data[0][1]
        ind = np.arange(len(xs))
        fig, ax =  plt.subplots()
        rects = ax.bar(ind + width, ys, color=color)
#        ax.set_xticks(ind + width*3/2)
        ax.set_xticks(ind)
        if semilog:
            ax.set_yscale('log')
        if add_bar_labels:
            bar_label(ax, rects, semilog)

    fig.set_size_inches(9,6)
    ax.set_xticklabels(xs, rotation=0)
    ax.set_title(title)
    ax.set_xlabel("Object Size (Bytes)")
    ax.set_ylabel('MB/s')
    plt.show()
    plt.savefig('foo.png')
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
                ys.append(parse.rados_get_write_bandwidth(testtype, size))
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




