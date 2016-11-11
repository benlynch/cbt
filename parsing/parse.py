import os
import database
import fnmatch
import re
import random
import hashlib
import sys
import json

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

def get_rados_bandwidth( testname, testtype, size ):
    mytable = database.fetch_bw(testname, [testtype,size])
    myreturn = 0.0
    if len(mytable) < 1:
        print(mytable, "Error: no data found")
        sys.exit()
    if testtype == 'write':
        index = 1
    else:
        index = 0
    for i in range(0, len(mytable)):
        myreturn += mytable[i][index]
    return float(myreturn);

def parse_output( archives=[], path='.' ):
    database.create_db()
    #FIXME the database structure should be updated to include all the 
    # fields currently produced by CBT. The code below ignores client readahead.
    # The Rbdfio/rbdfio structure produced by CBT seems redundant.
    #
    #start by parsing the Radosbench output
    files = []
    for archive in archives:
        directory = path + '/'+ archive + '/00000000/Radosbench'
        files.extend(find('output.*.*', directory))
    for inputname in files:
        filepattern = re.compile(path + '/' + '(.+)')
        m = filepattern.match(inputname)
        mydirectory = m.group(1)
        params = mydirectory.split("/")
        baselist=params[:]
        baselist.pop()
        basedir = '/'.join(baselist)
        settings = []
        settings.extend(find('ceph_settings.out.*', basedir))
        # make readahead into an int
        params[3] = int(params[3][7:])
        # Make op_size into an int
        params[4] = int(params[4][8:])
        # Make cprocs into an int
        params[5] = int(params[5][17:])
        outputname = params[7]
        params[7] = params[6]
#       I'm not sure what iodepth should be for radosbench. Setting to 1
        params[6] = 1
        params = [outputname] + params 
        params_hash = mkhash(params)
        params = [params_hash] + params
        params.extend([0,0])
        database.partial_insert(params)

        if len(settings) > 0:
            with open(settings[0]) as ceph_cluster_settings:
                cluster_settings = json.load(ceph_cluster_settings)
            database.update_columns(params[0],cluster_settings)

        pattern = re.compile('Bandwidth \(MB/sec\):\s+(\d+\.\d+)')
        for line in open(inputname):
            m = pattern.match(line)
            if m:
                bw = float(m.group(1))
                if  params[9] == 'write':
                    database.update_writebw(params_hash, bw)
                else:
                    database.update_readbw(params_hash, bw)
    #repeat with fio output
    files = []
    for archive in archives:
        directory = path + '/'+ archive + '/00000000/RbdFio'
        files.extend(find('output.*', directory))
    for inputname in files:
        filepattern = re.compile(path + '/' + '(.+)')
        m = filepattern.match(inputname)
        mydirectory = m.group(1)
        params = mydirectory.split("/")
#        print(params)
        # make readahead into an int
        params[3] = int(params[4][7:])
        # Make op_size into an int
        params[4] = int(params[6][8:])
        # Make cprocs into an int
        params[5] = int(params[7][17:])
        # Make iodepth into an int
        params[6] = int(params[8][8:])
        params[7] = params[9]
        params[8] = 0.0
        params[9] = 0.0
        outputname = params.pop()
        params = [outputname] + params
        params_hash = mkhash(params)
        params = [params_hash] + params
#        print(params)
        database.insert(params)
        for line in open(inputname):
            if "aggrb" in line:
                 bw = getbw(splits(line, 'aggrb=', ','))
                 if "READ" in line:
                     database.update_readbw(params_hash, bw)
                 elif "WRITE" in line:
                     database.update_writebw(params_hash, bw)

def splits(s,d1,d2):
    l,_,r = s.partition(d1)
    m,_,r = r.partition(d2)
    return m

