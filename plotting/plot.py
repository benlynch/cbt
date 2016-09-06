#!/usr/bin/python
import matplotlib as mpl
mpl.use('Agg')
import cbtworkspace
import yaml
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Graph output from CBT')
    parser.add_argument('--archive', nargs='+', type=str, required=True, help='One or more archive directory to parse')
    parser.add_argument('--config', nargs='?', type=str, required=True, help='YAML descriptin of graph to produce')
    parser.add_argument('--title', nargs='?', type=str, help='Title of the graph')
    parser.add_argument('--output',  nargs='?', type=str, help='Name of output image file(s)')
    
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


