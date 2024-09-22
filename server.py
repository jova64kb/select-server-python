import signal
import sys
import argparse
import random
import socket
import select

# static http response
def http_response():
    body = (
        '<!doctype html>\r\n'
        '<html>\r\n'
            '\t<head>\r\n'
                '\t\t<title>skall</title>\r\n'
                '\t\t<meta charset="utf-8">\r\n'
            '\t</head>\r\n'
            '\t<body>\r\n'
		        '\t\t<h1>Welcome to skall.dev!</h1>\r\n'
		        '\t\t<p>Coming soon...</p>\r\n'
            '\t</body>\r\n'
        '</html>\r\n'
        ).encode()
    body_len = len(body)
    headers = (
        'Server: skall\r\n'
        'Content-type: text/html; charset=utf-8\r\n'
        f'Content-length: {body_len}\r\n\r\n'
        ).encode()
    start_line = ('HTTP/1.1 200 OK\r\n').encode()
    result = b''.join([start_line, headers, body])
    return result

# args
parser = argparse.ArgumentParser()
parser.add_argument('-p', '--port',
                    type = int,
                    help = 'specifies the port number to be used')
args = parser.parse_args()
port = 0
lowest_port = 1024
highest_port = 65535
if args.port:
    if args.port < lowest_port:
        print('port lower than 1024')
        sys.exit(1)
    elif args.port > highest_port:
        print('port greater than 65535')
        sys.exit(1)
    port = args.port
else:
    port = random.randint(lowest_port, highest_port)

# getaddrinfo() -> returns a list of 5-tuples
addr_info = None
try:
    addr_info = socket.getaddrinfo(
        '127.0.0.1',
        port,
        socket.AF_INET,
        socket.SOCK_STREAM,
        socket.IPPROTO_TCP,
        socket.AI_PASSIVE
        )
except OSError as err_msg:
    print(f'could not get socket address information: ', err_msg)
    sys.exit(1)

# socket()
af, socktype, proto, canonname, sa = addr_info[0]
sock_listen = None
try:
    sock_listen = socket.socket(af, socktype, proto)
except OSError as err_msg:
    print(f'socket could not be created: ', err_msg)
    sys.exit(1)

# setsockopt()
try:
    sock_listen.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
except OSError as err_msg:
    print(f'socket options could not be set: ', err_msg)
    sys.exit(1)

# bind()
try:
    sock_listen.bind(sa)
except OSError as err_msg:
    print(f'socket could not be bound to port {port}: ', err_msg)
    sys.exit(1)

# listen()
try:
    # /proc/sys/net/core/somaxconn => 4096
    sock_listen.listen(128)
except OSError as err_msg:
    print(f'server unable to accept connections: ', err_msg)
    sys.exit(1)
print(f'listening on: {sa[0]}:{sa[1]}')

def sig_handler(sig, frame):
    print('exiting...')
    sock_listen.close()
    sys.exit(0)

# map sig_handler
signal.signal(signal.SIGINT, sig_handler)

# select()
reads = []
reads.append(sock_listen)
while True:
    # return value is a triple of lists of objects that are ready
    rlist, wlist, xlist = select.select(reads, [], [], 0)
    for r in rlist:
        # new connection ready to be established
        if r == sock_listen:
            # accept()
            sock_client, client_addr = sock_listen.accept()
            reads.append(sock_client)
            client_host, client_port = socket.getnameinfo(
                    client_addr,
                    socket.NI_NUMERICHOST)
            print(f'new connection established: {client_host}:{client_port}')
        # socket ready to be read from
        else:
            data = r.recv(4096)
            # client has closed the connection
            if not data:
                client_host, client_port = r.getpeername()
                print(f'closing connection: {client_host}:{client_port}')
                r.shutdown(socket.SHUT_WR) # send FIN
                reads.remove(r)
                continue
            req_split = data.decode('utf-8').split('\r\n')
            close = False
            for s in req_split:
                if s == 'Connection: close':
                    close = True
            print(data.decode())
            if close:
                client_host, client_port = r.getpeername()
                print(f'closing connection: {client_host}:{client_port}')
                r.shutdown(socket.SHUT_WR) # send FIN
                reads.remove(r)
                continue
            else:
                r.sendall(http_response())

