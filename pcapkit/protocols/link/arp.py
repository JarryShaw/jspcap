# -*- coding: utf-8 -*-
"""(inverse) address resolution protocol

:mod:`pcapkit.protocols.link.arp` contains
:class:`~pcapkit.protocols.link.arp.ARP` only,
which implements extractor for (Inverse) Address Resolution
Protocol (ARP/InARP) [*]_, whose structure is described as
below:

+========+=======+===============+=========================+
| Octets | Bits  | Name          | Description             |
+========+=======+===============+=========================+
| 0      |     0 | ``arp.htype`` | Hardware Type           |
+--------+-------+---------------+-------------------------+
| 2      |    16 | ``arp.ptype`` | Protocol Type           |
+--------+-------+---------------+-------------------------+
| 4      |    32 | ``arp.hlen``  | Hardware Address Length |
+--------+-------+---------------+-------------------------+
| 5      |    40 | ``arp.plen``  | Protocol Address Length |
+--------+-------+---------------+-------------------------+
| 6      |    48 | ``arp.oper``  | Operation               |
+--------+-------+---------------+-------------------------+
| 8      |    64 | ``arp.sha``   | Sender Hardware Address |
+--------+-------+---------------+-------------------------+
| 14     |   112 | ``arp.spa``   | Sender Protocol Address |
+--------+-------+---------------+-------------------------+
| 18     |   144 | ``arp.tha``   | Target Hardware Address |
+--------+-------+---------------+-------------------------+
| 24     |   192 | ``arp.tpa``   | Target Protocol Address |
+--------+-------+---------------+-------------------------+

.. [*] http://en.wikipedia.org/wiki/Address_Resolution_Protocol

"""
import ipaddress
import re
import textwrap

from pcapkit.const.arp.hardware import Hardware as HRD
from pcapkit.const.arp.operation import Operation as OPER
from pcapkit.const.reg.ethertype import EtherType as ETHERTYPE
from pcapkit.corekit.infoclass import Info
from pcapkit.protocols.link.link import Link

__all__ = ['ARP']


class ARP(Link):
    """This class implements all protocols in ARP family.

    - Address Resolution Protocol (ARP) [:rfc:`826`]
    - Reverse Address Resolution Protocol (RARP) [:rfc:`903`]
    - Dynamic Reverse Address Resolution Protocol (DRARP) [:rfc:`1931`]
    - Inverse Address Resolution Protocol (InARP) [:rfc:`2390`]

    Attributes:
        name (str): name of corresponding protocol
        info (Info): info dict of current instance
        alias (str): acronym of corresponding protocol
        layer (str): ``'Link'``
        length (int): header length of corresponding protocol
        protocol (EtherType): enumeration of next layer protocol
        protochain (ProtoChain): protocol chain of current instance
        src (Tuple[str, str]): sender hardware & protocol address
        dst (Tuple[str, str]): target hardware & protocol address
        type (Tuple[str, str]): hardware & protocol type

        _file: (io.BytesIO): source data stream
        _info: (Info): info dict of current instance
        _protos: (ProtoChain): protocol chain of current instance
        _acnm: (str): acronym of corresponding protocol
        _name: (str): name of corresponding protocol

    Methods:
        decode_bytes: try to decode bytes into str
        decode_url: decode URLs into Unicode
        read_arp: read Address Resolution Protocol

        _read_protos: read next layer protocol type
        _read_fileng: read file buffer
        _read_unpack: read bytes and unpack to integers
        _read_binary: read bytes and convert into binaries
        _read_packet: read raw packet data
        _decode_next_layer: decode next layer protocol type
        _import_next_layer: import next layer protocol extractor
        _read_addr_resolve: resolve MAC address according to protocol
        _read_proto_resolve: solve IP address according to protocol

    """
    ##########################################################################
    # Properties.
    ##########################################################################

    @property
    def name(self):
        """Name of current protocol."""
        return self._name

    @property
    def alias(self):
        """Acronym of corresponding protocol."""
        return self._acnm

    @property
    def length(self):
        """Header length of current protocol."""
        return self._info.len  # pylint: disable=E1101

    @property
    def src(self):
        """Sender hardware & protocol address."""
        return (self._info.sha, self._info.spa)  # pylint: disable=E1101

    @property
    def dst(self):
        """Target hardware & protocol address."""
        return (self._info.tha, self._info.tpa)  # pylint: disable=E1101

    @property
    def type(self):
        """Hardware & protocol type."""
        return (self._info.htype, self._info.ptype)  # pylint: disable=E1101

    ##########################################################################
    # Methods.
    ##########################################################################

    def read_arp(self, length):
        """Read Address Resolution Protocol.

        Structure of ARP header [:rfc:`826`]:

        +========+=======+===============+=========================+
        | Octets | Bits  | Name          | Description             |
        +========+=======+===============+=========================+
        | 0      |     0 | ``arp.htype`` | Hardware Type           |
        +--------+-------+---------------+-------------------------+
        | 2      |    16 | ``arp.ptype`` | Protocol Type           |
        +--------+-------+---------------+-------------------------+
        | 4      |    32 | ``arp.hlen``  | Hardware Address Length |
        +--------+-------+---------------+-------------------------+
        | 5      |    40 | ``arp.plen``  | Protocol Address Length |
        +--------+-------+---------------+-------------------------+
        | 6      |    48 | ``arp.oper``  | Operation               |
        +--------+-------+---------------+-------------------------+
        | 8      |    64 | ``arp.sha``   | Sender Hardware Address |
        +--------+-------+---------------+-------------------------+
        | 14     |   112 | ``arp.spa``   | Sender Protocol Address |
        +--------+-------+---------------+-------------------------+
        | 18     |   144 | ``arp.tha``   | Target Hardware Address |
        +--------+-------+---------------+-------------------------+
        | 24     |   192 | ``arp.tpa``   | Target Protocol Address |
        +--------+-------+---------------+-------------------------+

        Args:
            length (int): packet length

        Returns:
            dict: Parsed packet data, as following structure::

                class ARP(TypedDict):
                    \"\"\"ARP header.\"\"\"

                    #: hardware type
                    htype: Hardware
                    #: protocol type
                    ptype: Union[EtherType, str]
                    #: hardware address length
                    hlen: int
                    #: protocol address length
                    plen: int
                    #: operation
                    oper: Operation
                    #: sender hardware address
                    sha: str
                    #: sender protocol address
                    spa: Union[IPv4Address, IPv6Address, str]
                    #: target hardware address
                    tha: str
                    #: target protocol address
                    tpa: Union[IPv4Address, IPv6Address, str]

                    #: protocol header length
                    len: int
                    #: protocol packet data
                    packet: bytes

        """
        if length is None:
            length = len(self)

        _hwty = self._read_unpack(2)
        _ptty = self._read_unpack(2)
        _hlen = self._read_unpack(1)
        _plen = self._read_unpack(1)
        _oper = self._read_unpack(2)
        _shwa = self._read_addr_resolve(_hlen, _hwty)
        _spta = self._read_proto_resolve(_plen, _ptty)
        _thwa = self._read_addr_resolve(_hlen, _hwty)
        _tpta = self._read_proto_resolve(_plen, _ptty)

        if _oper in (5, 6, 7):
            self._acnm = 'DRARP'
            self._name = 'Dynamic Reverse Address Resolution Protocol'
        elif _oper in (8, 9):
            self._acnm = 'InARP'
            self._name = 'Inverse Address Resolution Protocol'
        elif _oper in (3, 4):
            self._acnm = 'RARP'
            self._name = 'Reverse Address Resolution Protocol'
        else:
            self._acnm = 'ARP'
            self._name = 'Address Resolution Protocol'

        _htype = HRD.get(_hwty)
        if re.match(r'.*Ethernet.*', _htype, re.IGNORECASE):
            _ptype = ETHERTYPE.get(_ptty)
        else:
            _ptype = f'Unknown [{_ptty}]'

        arp = dict(
            htype=_htype,
            ptype=_ptype,
            hlen=_hlen,
            plen=_plen,
            oper=OPER.get(_oper),
            sha=_shwa,
            spa=_spta,
            tha=_thwa,
            tpa=_tpta,
            len=8 + _hlen * 2 + _plen * 2,
        )

        length -= arp['len']
        arp['packet'] = self._read_packet(header=arp['len'], payload=length)

        return self._decode_next_layer(arp, None, length)

    ##########################################################################
    # Data models.
    ##########################################################################

    def __init__(self, file, length=None, **kwargs):  # pylint: disable=super-init-not-called
        """Initialisation.

        Args:
            file (io.BytesIO): Source packet stream.
            length (int): Packet length.

        Keyword Args:
            **kwargs: Arbitrary keyword arguments.

        """
        self._file = file
        self._info = Info(self.read_arp(length))

    def __length_hint__(self):
        """Return an estimated length (28) for the object."""
        return 28

    @classmethod
    def __index__(cls):
        """Index of the protocol.

        Returns:
            Tuple[Literal['ARP'], Literal['InARP']]: Index of the protocol.

        See Also:
            :meth:`pcapkit.protocols.protocol.Protocol.__getitem__`

        """
        return ('ARP', 'InARP')

    ##########################################################################
    # Utilities.
    ##########################################################################

    def _read_addr_resolve(self, length, htype):
        """Resolve headware address according to protocol.

        Arguments:
            length (int): Hardware address length.
            htype (int): Hardware type.

        Returns:
            str: Hardware address. If ``htype`` is ``1``, i.e. MAC address,
            returns ``:`` seperated *hex* encoded MAC address.

        """
        if htype == 1:  # Ethernet
            _byte = self._read_fileng(6)
            _addr = ':'.join(textwrap.wrap(_byte.hex(), 2))
        else:
            _addr = self._read_fileng(length)
        return _addr

    def _read_proto_resolve(self, length, ptype):
        """Resolve protocol address according to protocol.

        Positional arguments:
            length (int): Protocol address length.
            ptype (int): Protocol type.

        Returns:
            Union[IPv4Address, IPv6Address, str]: Protocol address. If ``ptype`` is ``0x0800``,
            i.e. IPv4 adddress, returns an :class:`~ipaddress.IPv4Address` object; if ``ptype``
            is ``0x86dd``, i.e. IPv6 address, returns an :class:`~ipaddress.IPv6Address` object;
            otherwise, returns a raw :data:`str` representing the protocol address.

        """
        if ptype == 0x0800:  # IPv4
            return ipaddress.ip_address(self._read_fileng(4))
        if ptype == 0x86dd:  # IPv6
            return ipaddress.ip_address(self._read_fileng(16))
        return self._read_fileng(length)