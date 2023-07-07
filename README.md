# Master of Puppets

### Description
"Master of Puppets" (MOP) is a small project I developed to gain a better understanding of how a botnet could work and
be utilized. Obviously, it's a simple python implementation of the main concept, not an actual botnet. It's all for the
sake of knowledge!

The botnet is divided into the master (of puppets) MOP, which acts as the controller for all the puppets that connect
directly to it.

The communication between the master and puppet is implemented using a custom protocol I created called the Monkey
Communication Protocol (MCP), and its packet structure is as follows:
```
 +------------+
 | METHOD\r\n |
 +------------+
 | json data  | 
 | ...        |
 | ...        |
 | ...\r\n    |
 +------------+

```

### Usage
Start the master for incoming connections
  
_Just call my name, 'cause I'll hear you scream_
 
`python3 src/mop.py <port>`
 
Connect puppet to master
 
_Obey your master!_
 
`python3 src/puppet.py <host> <port>`

### TODO
- [x] Harvest system info
- [x] Monkey Control Protocol (MCP) bare-bones
- [x] MCP packet receive
- [x] MCP packet send (kind of)
- [x] MCP Handshake
- [x] Assign & Execute tasks
- [x] Cmd utility
- [x] List puppets connections command
- [x] OS Execute order
- [x] Puppet info command
- [ ] Orders log command
- [ ] Puppet kill command
- [ ] Total world control (?)
