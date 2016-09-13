import os
import database
import fnmatch
import re
import random
import hashlib
import sys

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
    if len(mytable) < 1:
        print("Error: no data found")
        sys.exit()
    if testtype == 'write':
        myreturn = mytable[0][1]
    if testtype == 'seq':
        myreturn = mytable[0][0]
    if testtype == 'rand':
        myreturn = mytable[0][0]
    return float(myreturn);

def parse_output( test, args ):
    if test == 'radosbench':
        database.create_db()
        files = []
        for archive in args['archive']:
            directory = args['path'] + '/'+ archive
            files.extend(find('output.*', directory))
        for inputname in files:
            filepattern = re.compile(args['path'] + '/' + '(.+)')
            m = filepattern.match(inputname)
            mydirectory = m.group(1)
            params = mydirectory.split("/")
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
            database.insert(params)
            pattern = re.compile('Bandwidth \(MB/sec\):\s+(\d+\.\d+)')
#            print(params)
            for line in open(inputname):
                m = pattern.match(line)
                if m:
                    bw = float(m.group(1))
                    if  params[8] == 'write':
                        database.update_writebw(params_hash, bw)
                    else:
                        database.update_readbw(params_hash, bw)
    if test == 'fio':
        print("soon")

