import matplotlib.pyplot as plt
import matplotlib.axes as ax
import pandas as pd
import numpy as np
import os
from os import listdir
import re
import sys
import database
import parse
import fiologparser as nh
import functools

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

    def geomean(self, test_name, test_type, object_sizes=[4096, 16384, 65536, 262144, 1048576, 4194304]):
        values = []
        if (test_type == 'rados_write'):
            test_type = 'write'
        if (test_type == 'rados_read_seq'):
            test_type = 'seq'
        if (test_type == 'rados_read_rand'):
            test_type = 'rand'
        if not test_name:
            print('EEROR')
        if not test_type:
            print('EEROR')
        for size in object_sizes:
                values.append(parse.get_rados_bandwidth(test_name, test_type, size))
        return (functools.reduce(lambda x, y: x*y, values))**(1.0/len(values))

    def ls(self,filters=[]):
        dirlist = []
        if len(filters) == 0:
            for file in listdir(self.path):
                if os.path.isdir(self.path + '/' + file):
                    if os.path.isdir(self.path + '/' + file + '/00000000'): 
                       dirlist.append(file)
        else:
            self.parse_all()
            parsed_filters = []
            for filter in filters:
                [key, value] = filter.split('=')
                parsed_filters.append(key + "='" + value + "'")
            dirlist.extend(database.list_archives(parsed_filters))
        return dirlist

    def describe(self, archives=False):
        if not archives:
            archives = self.ls()
        if not isinstance(archives, list):
            archives = [archives]
        for arc in archives:
            # skip parsing any directory that we've already parsed once
            if not self.arc_parsed[arc]:
                parse.parse_output(archives=[arc], path=self.path )
            self.arc_parsed[arc] = True 
        pd.set_option('display.notebook_repr_html', True)
        description = pd.DataFrame(database.fetch_desc(archives), columns=['Archive','Benchmark','Size','Test', 'Read', 'Write'])
        print(description)

    def parse_all(self):
        archives = self.ls()
        if not isinstance(archives, list):
            archives = [archives]
        for arc in archives:
            # skip parsing any directory that we've already parsed once
            if not self.arc_parsed[arc]:
                parse.parse_output(archives=[arc], path=self.path )
            self.arc_parsed[arc] = True

    def bar_graph(self, benchmark_runs, test_type, title='Insert Fancy Title Here', object_sizes=[4096, 16384, 65536, 262144, 1048576, 4194304],
            log=True, bar_label=True, bar_colors=[], legend_labels=[]):
        if test_type == 'rados_write':
            bname = 'radosbench'
            tname = 'write'
        if test_type == 'rados_read_seq':
            bname = 'radosbench'
            tname = 'seq'
        if test_type == 'rados_read_rand':
            bname = 'radosbench'
            tname = 'rand'
        if test_type == 'rbdfio_randread':
            bname = 'rbdfio'
            tname = 'randread'
        args = {}
        args['path'] = self.path
        args['archive'] = benchmark_runs
        args['title'] = title
        args['bar_colors'] = bar_colors
        args['legend_labels'] = legend_labels
        doc = {bname:{tname:{'x':{'sizes':object_sizes, 'concurrent':2},'y':{'log':log,'bar_label':bar_label}}}}
        args['doc'] = doc
        if 'radosbench' in doc.keys():
            for arc in benchmark_runs:
                 if not self.arc_parsed[arc]:
                     parse.parse_output(archives=[arc], path=self.path)
                 self.arc_parsed[arc] = True
            create_rados_graphs(args)
        if 'rbdfio' in doc.keys():
            for arc in benchmark_runs:
                 if not self.arc_parsed[arc]:
                     parse.parse_output(archives=[arc], path=self.path)
                 self.arc_parsed[arc] = True
            
    def line_graph(self, plot_series, plot_value='iops', title='Insert Fancy Title Here', 
                   plot_markers=['g^','bs','r--']):
        series = []
        for fn in ['fio1/00000000/RbdFio/rbdfio/osd_ra-00004096/client_ra-00000128/op_size-00004096/concurrent_procs-001/iodepth-032/randrw/output_iops.1.log.stratus-osd01']:
            ctx = setting(fn)
            series.append(nh.TimeSeries(ctx, fn))
        table = nh.print_sums(ctx, series)
        io1 = []
        for i in range(0,len(table)):
            io1.append(table[i][1])
 
        t  = np.arange(0, len(table), 1)
        plt.plot(t,io1, 'r--')
#        plt.plot(t,io1, 'r--', t, io2, 'g^', t, io3, 'bs')
        plt.xlabel('time (s)')
        plt.ylabel('IOPs')
        plt.show()
        return;                    

class setting():
    def __init__(self, fn):
        self.FILE = [fn]
        self.interval = 1000
        self.divisor = 1
        self.full = False
        self.average = False
        sum = True
        

def bar_label(ax, rects, semilog):
    (y_bottom, y_top) = ax.get_ylim()
    y_height = y_top - y_bottom
    for rect in rects:
        height = rect.get_height()
        p_height = (height / y_height)
# just put all labels above bars
        if semilog:
            if p_height > 1.95:
                label_position = height*(0.95)
            else:
                label_position = height*(1.05)
        else:
            if p_height > 1.95:
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

def create_bar_graph(data=[[[1, 2],[10, 20]]], semilog=False, add_bar_labels=True, title='Insert Fancy Title', 
                     add_legend=False, bar_colors=[], legend_labels=[]): 
    import matplotlib.patches as mpatches
    from collections import deque
    if not bar_colors:
        bar_color_deque=deque(['#1395ba','#a2b86c','#ebc844','#f16c20','#c02e1d','#0d3c55','#ecaa38',
                               '#117899','#d94e1f','#5ca793','#ef8b2c','#0f5b78'])
    else:
        bar_color_deque=deque(bar_colors)
    width = 0.33
    xs = data[0][0]
    legend_labels_queue = deque(legend_labels)
    handles = []
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
            color = bar_color_deque.popleft()
            if legend_labels:
                legend_label = legend_labels_queue.popleft()
            else:
                legend_label = label
            handles.append(mpatches.Patch(color=color, label=legend_label))
            index = 0
            labeled_yet = False
            for ex in sorted(all_unique_x.keys()):
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
            plt.legend(handles=handles, loc=2)
    else:
        color = bar_color_deque.popleft()
        ys = data[0][1]
        ind = np.arange(len(xs))
        fig, ax =  plt.subplots()
        rects = ax.bar(ind + width,  ys, color=color)
        ax.set_xticks(ind + width*2)
        if semilog:
            ax.set_yscale('log')
        if add_bar_labels:
            bar_label(ax, rects, semilog)
    fig.set_size_inches(15,8)
    ax.set_xticklabels(xs, rotation=0)
    ax.set_title(title)
    ax.set_xlabel("Object Size (Bytes)")
    ax.set_ylabel('MB/s')
    plt.show()
    plt.savefig('foo.png')
    return;

def lightning_line_graph(data=[[[1, 2],[10, 20]]], semilog=False, add_bar_labels=True, title='Insert Fancy Title',
                      add_legend=False, bar_colors=[]):
    series = [[0,1,2,3,4,5,6],[1.1,-2.1]] 
    return series;

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
    create_bar_graph(data=data, semilog=semilog, add_bar_labels=add_bar_labels, title=args['title'], 
                     bar_colors=args['bar_colors'], add_legend=True, legend_labels=args['legend_labels'])
    return;


def create_rbdfio_graphs( args ):
    add_bar_labels = True
    semilog = False
    data = []
    return;

