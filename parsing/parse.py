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

