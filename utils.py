import socket
import random
import pickle

def client_send(sock, data):
    sock.send(b"OILOPAKETSTART!" + data)

def send(socks, data):
    for sock in socks:
        try:
            sock.send(b"OILOPAKETSTART!" + data)
        except Exception as ex:
            print(ex)
            socks.remove(sock)