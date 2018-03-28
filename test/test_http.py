#!/usr/bin/python3
# -*- coding: utf-8 -*-


import jspcap


extractor = jspcap.Extractor(fin='../sample/http.pcap', nofile=True, auto=False)
# extractor = jspcap.Extractor(fin='../sample/http.pcap', fout='../sample/http', files=True, format='tree', auto=False)

for frame in extractor:
    # check if this frame contains HTTP
    if jspcap.HTTP in frame:
        # print frame number & its protocols chain
        print(f'{frame.name}: {frame.protochain}')
        #
        # # fetch http info dict
        # # http = dict(
        # #     receipt = 'request' | 'response',
        # #     # request header
        # #     request = dict(
        # #         method = METHOD,
        # #         target = TARGET,
        # #         version = '1,0' | '1.1',
        # #     )
        # #     # response header
        # #     response = dict(
        # #         version = '1,0' | '1.1',
        # #         status = STATUS,
        # #         phrase = PHRASE,
        # #     )
        # #     # other fields
        # #     ...
        # # )
        # http = frame[flag]
        #
        # # fetch HTTP type (request/response)
        # http_type = http.receipt    # or http['receipt']
        #
        # # fetch HTTP header fields dict
        # http_header = http.header   # or http['header']
        #
        # # fetch HTTP body
        # http_body = http.body       # or http['body']
        #
        # # or do something else
        # ...