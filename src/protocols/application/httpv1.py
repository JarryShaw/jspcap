"""hypertext transfer protocol (HTTP/1.*)

``jspcap.protocols.application.httpv1`` contains ``HTTPv1``
only, which implements extractor for Hypertext Transfer
Protocol (HTTP/1.*), whose structure is described as
below.

METHOD URL HTTP/VERSION\r\n :==: REQUEST LINE
<key> : <value>\r\n         :==: REQUEST HEADER
............  (Elipsis)     :==: REQUEST HEADER
\r\n                        :==: REQUEST SEPERATOR
<body>                      :==: REQUEST BODY (optional)

HTTP/VERSION CODE DESP \r\n :==: RESPONSE LINE
<key> : <value>\r\n         :==: RESPONSE HEADER
............  (Elipsis)     :==: RESPONSE HEADER
\r\n                        :==: RESPONSE SEPERATOR
<body>                      :==: RESPONSE BODY (optional)

"""
import chardet
import re


# Hypertext Transfer Protocol (HTTP/1.*)
# Analyser for HTTP/1.* request & response


from jspcap.exceptions import ProtocolError
from jspcap.utilities import Info
from jspcap.protocols.application.http import HTTP


__all__ = ['HTTPv1']


# utility regular expressions
_RE_METHOD = re.compile(rb'GET|HEAD|POST|PUT|DELETE|CONNECT|OPTIONS|TRACE')
_RE_VERSION = re.compile(rb'HTTP/(?P<version>\d\.\d)')
_RE_STATUS = re.compile(rb'\d{3}')


class HTTPv1(HTTP):
    """This class implements Hypertext Transfer Protocol (HTTP/1.*).

    Properties:
        * name -- str, name of corresponding procotol
        * info -- Info, info dict of current instance
        * alias -- str, acronym of corresponding procotol
        * layer -- str, `Application`
        * protocol -- str, name of next layer protocol
        * protochain -- ProtoChain, protocol chain of current instance

    Methods:
        * read_http -- read Hypertext Transfer Protocol (HTTP/1.*)

    Attributes:
        * _file -- BytesIO, bytes to be extracted
        * _info -- Info, info dict of current instance
        * _protos -- ProtoChain, protocol chain of current instance

    Utilities:
        * _read_protos -- read next layer protocol type
        * _read_fileng -- read file buffer
        * _read_unpack -- read bytes and unpack to integers
        * _read_binary -- read bytes and convert into binaries
        * _make_protochain -- make ProtoChain instance for corresponding protocol
        * _read_http_header -- read HTTP/1.* header
        * _read_http_body -- read HTTP/1.* body

    """
    ##########################################################################
    # Properties.
    ##########################################################################

    @property
    def alias(self):
        """Acronym of current protocol."""
        return f'HTTP/{self._info.header[self._info.receipt].version}'

    ##########################################################################
    # Methods.
    ##########################################################################

    def read_http(self, length):
        """Read Hypertext Transfer Protocol (HTTP/1.*).

        Structure of HTTP/1.* packet [RFC 7230]:
            HTTP-message    :==:    start-line
                                    *( header-field CRLF )
                                    CRLF
                                    [ message-body ]

        """
        packet = self._file.read(length)
        try:
            header, body = packet.split(b'\r\n\r\n', 1)
        except ValueError:
            raise ProtocolError('HTTP: invalid format', quiet=True)

        header_unpacked, http_receipt = self._read_http_header(header)
        body_unpacked = self._read_http_body(body) or None

        http = dict(
            receipt = http_receipt,
            header = header_unpacked,
            body = body_unpacked,
        )

        return http

    ##########################################################################
    # Utilities.
    ##########################################################################

    def _read_http_header(self, header):
        """Read HTTP/1.* header.

        Structure of HTTP/1.* header [RFC 7230]:
            start-line      :==:    request-line / status-line
            request-line    :==:    method SP request-target SP HTTP-version CRLF
            status-line     :==:    HTTP-version SP status-code SP reason-phrase CRLF
            header-field    :==:    field-name ":" OWS field-value OWS

        """
        try:
            startline, headerfield = header.split(b'\r\n', 1)
            para1, para2, para3 = re.split(b'\s+', startline, 2)
            fields = headerfield.split(b'\r\n')
            lists = ( re.split(b'\s*:\s*', field, 1) for field in fields )
        except ValueError:
            raise ProtocolError('HTTP: invalid format', quiet=True)

        match1 = re.match(_RE_METHOD, para1)
        match2 = re.match(_RE_VERSION, para3)
        match3 = re.match(_RE_VERSION, para1)
        match4 = re.match(_RE_STATUS, para2)
        if match1 and match2:
            receipt = 'request'
            header = dict(
                request = dict(
                    method = para1.decode(),
                    target = para2.decode(),
                    version = match2.group('version').decode(),
                ),
            )
        elif match3 and match4:
            receipt = 'response'
            header = dict(
                response = dict(
                    version = match3.group('version').decode(),
                    status = int(para2.decode()),
                    phrase = para3.decode(),
                ),
            )
        else:
            raise ProtocolError('HTTP: invalid format', quiet=True)

        try:
            for item in lists:
                key = item[0].decode().strip().replace('request', 'request_field').replace('response', 'response_field')
                value = item[1].decode().strip()
                if key in header:
                    if isinstance(header[key], tuple):
                        header[key] += (value,)
                    else:
                        header[key] = (header[key], value)
                else:
                    header[key] = value
        except IndexError:
            raise ProtocolError('HTTP: invalid format', quiet=True)

        return header, receipt

    def _read_http_body(self, body):
        """Read HTTP/1.* body."""
        charset = chardet.detect(body)['encoding']
        if charset:
            try:
                return body.decode(charset)
            except UnicodeDecodeError:
                return body