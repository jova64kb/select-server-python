import signal
import sys
import socket
import select

def sig_handler(sig, frame):
    # close sock_listen ?
    print('exiting...')
    sys.exit(0)

# map sig_handler
signal.signal(signal.SIGINT, sig_handler)

# CHECK FOR ERRORS!

# getaddrinfo() -> returns a list of 5-tuples
addr_info = socket.getaddrinfo(
    '127.0.0.1',
    8080,
    socket.AF_INET,
    socket.SOCK_STREAM,
    socket.IPPROTO_TCP,
    socket.AI_PASSIVE
    )

# socket()
af, socktype, proto, canonname, sa = addr_info[0]
sock_listen = socket.socket(af, socktype, proto)

# setsockopt()
sock_listen.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# bind()
sock_listen.bind(sa)

# listen()
sock_listen.listen(10)
print(f'listening on: {sa[0]}:{sa[1]}')

# select()
reads = []
reads.append(sock_listen)
while True:
    # return value is a triple of lists of objects that are ready
    rlist, wlist, xlist = select.select(reads, [], [], 0)
    for r in rlist:
        # new connection ready to be established
        if r == sock_listen:
            sock_client, client_addr = sock_listen.accept()
            reads.append(sock_client)
            client_host, client_port = socket.getnameinfo(client_addr, socket.NI_NUMERICHOST)
            print(f'new connection established: {client_host}:{client_port}')
        # socket ready to be read from
        else:
            data = r.recv(4096) # improve
            req_split = data.decode('utf-8').split('\r\n')
            close = False
            for s in req_split:
                print(f'split: {s}')
                if s == 'Connection: close':
                    close = True
            if close:
                client_host, client_port = r.getpeername()
                print(f'closing connection: {client_host}:{client_port}')
                r.close()
                reads.remove(r)
                continue
            else:
                r.sendall(bytes('hello world\n', 'utf-8'))

sock_listen.close()

