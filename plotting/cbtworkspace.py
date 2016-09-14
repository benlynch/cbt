import matplotlib.pyplot as plt
import matplotlib.axes as ax
import pandas as pd
import numpy as np
import os
import re
from os import listdir
import sys
sys.path.append("/home/support/blynch/cbt/parsing")
import database
import parse
class cbtWorkspace:
    def __init__(self, path):
        self.path = path
        self.arclist = self.ls()
        self.arc_parsed = {} 
        for arc in  self.arclist:
            self.arc_parsed[arc] = False

    def __repr__(self):
        return "cbtWorkspace()"
 
    def __str__(self):
        return self.path

    def ls(self):
        dirlist = []
        for file in listdir(self.path):
            if os.path.isdir(self.path + '/' + file):
                if os.path.isdir(self.path + '/' + file + '/00000000'): 
                    dirlist.append(file)
        return dirlist

    def describe(self, archives=False):
        if not archives:
            archives = self.ls()
        for arc in archives:
            # skip parsing any directory that we've already parsed once
            if not self.arc_parsed[arc]:
                parse.parse_output(archives=[arc], path=self.path )
            self.arc_parsed[arc] = True 
        pd.set_option('display.notebook_repr_html', True)
        description = pd.DataFrame(database.fetch_desc(archives), columns=['Archive','Benchmark','Size','Test'])
        print(description)

    def bar_graph(self, benchmark_runs, test_type, title='Insert Fancy Title Here', object_sizes=[],
            log=True, bar_label=True):
        args = {}
        args['path'] = self.path
        args['archive'] = benchmark_runs
        args['title'] = title
        object_sizes=[ 4096, 16384, 65536, 262144, 1048576, 4194304 ]
        if test_type == 'rados_write':
            doc = {'radosbench':{'write':{'x':{'sizes':object_sizes, 'concurrent':2},'y':{'log':log,'bar_label':bar_label}}}}
        if test_type == 'rados_read_seq':
            doc = {'radosbench':{'seq':{'x':{'sizes':object_sizes, 'concurrent':2},'y':{'log':log,'bar_label':bar_label}}}}
        if test_type == 'rados_read_rand':
            doc = {'radosbench':{'rand':{'x':{'sizes':object_sizes, 'concurrent':2},'y':{'log':log,'bar_label':bar_label}}}}
        args['doc'] = doc
        if 'radosbench' in doc.keys():
            for arc in benchmark_runs:
                 if not self.arc_parsed[arc]:
                     parse.parse_output(archives=[arc], path=self.path)
                 self.arc_parsed[arc] = True
            create_rados_graphs(args)
        

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
                '%5.1f' % height,
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

def create_bar_graph( data=[[[1, 2],[10, 20]]], semilog=False, add_bar_labels=True, title='Insert Fancy Title', add_legend=False):
    pcolors = ['#0f5b78','#ef8b2c','#5ca793','#d94e1f','#117899','#ecaa38', '#0d3c55', '#c02e1d','#f16c20','#ebc844','#a2b86c','#1395ba']
    width = 0.33
    xs = data[0][0]
    if len(data) > 1:
        width = 0.33*2/len(data)
    #plot comparison from multiple archives
        all_unique_x = {}
        for series in data:
            for size in series[0]:
                all_unique_x[size] = True
        ind = np.arange(len(all_unique_x.keys()))
        rect_refs = []
        fig, ax = plt.subplots()
        bar_shift = width/2
        #plot individual bars to allow for sparse data plots
        for series in data:
            if len(series) > 2:
                label = series[2]
            color = pcolors.pop()
            index = 0
            labeled_yet = False
            for ex in all_unique_x.keys():
                for i in range(0, len(series[0])):
                    if series[0][i] == ex:
                        if 'label' in locals() and not labeled_yet:
                            rects = ax.bar(index + bar_shift, series[1][i], width, color=color, label=label)
                            labeled_yet = True
                        else:
                            rects = ax.bar(index + bar_shift, series[1][i], width, color=color)
                        rect_refs.append(rects[0])
                        if add_bar_labels:
                            bar_label(ax, rects, semilog)
                index += 1
            bar_shift += width
        if semilog:
            ax.set_yscale('log')
        ax.set_xticks(ind + 0.59 - 0.045*len(data))
        if add_legend:
            plt.legend(loc=2)
    else:
        color = pcolors.pop()
        ys = data[0][1]
        ind = np.arange(len(xs))
        fig, ax =  plt.subplots()
        rects = ax.bar(ind + width,  ys, color=color)
        ax.set_xticks(ind + width*2)
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


 
def create_rados_graphs( args ):
    add_bar_labels = True 
    semilog = False
    data = []
    params = args['doc']['radosbench']
    for testkey, test in params.items():
        if test["y"]["log"] == True:
            semilog = True
        if 'y' in params[testkey].keys():
            if 'bar_label' in test['y'].keys():
                add_bar_labels = test['y']["bar_label"]
        y_values = []
        xs = test["x"]["sizes"]
        concurrent = test["x"]["concurrent"]
        for testname in args['archive']:
            ys = []
            for size in xs:
                ys.append(parse.get_rados_bandwidth(testname, testkey, size))
            y_values.append(ys)
            data.append([xs,ys,testname])
    create_bar_graph(data=data, semilog=semilog, add_bar_labels=add_bar_labels, title=args['title'], add_legend=True)
    return;


