import socket
import sys

from pytradfri import Gateway
from pytradfri.api.aiocoap_api import APIFactory
from pytradfri.error import PytradfriError
from pytradfri.util import load_json, save_json

import asyncio
import uuid
import argparse

ADDR = ""
PORT = 8675
DATA_SIZE = 1024

# async def setup():
#     serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     serversocket.bind((socket.gethostname(), PORT))
#     serversocket.listen(1)

#     CONFIG_FILE = "tradfri_standalone_psk.conf"
#     conf = load_json(CONFIG_FILE)
#     try:
#         identity = conf[args.host].get("identity")
#         psk = conf[args.host].get("key")
#         api_factory = await APIFactory.init(host=args.host, psk_id=identity, psk=psk)
#     except KeyError:
#         identity = uuid.uuid4().hex
#         api_factory = await APIFactory.init(host=args.host, psk_id=identity)

#         try:
#             psk = await api_factory.generate_psk(args.key)
#             print("Generated PSK: ", psk)

#             conf[args.host] = {"identity": identity, "key": psk}
#             save_json(CONFIG_FILE, conf)
#         except AttributeError:
#             raise PytradfriError(
#                 "Please provide the 'Security Code' on the "
#                 "back of your Tradfri gateway using the "
#                 "-K flag."
#             )
#     api = api_factory.request

#     gateway = Gateway()

#     devices_command = gateway.get_devices()
#     devices_commands = await api(devices_command)
#     devices = await api(devices_commands)
    # blinds = [dev for dev in devices if dev.has_blind_control]



class TcpPyTradfri():
    def __init__(self):
        self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serversocket.bind((ADDR, PORT))
        self.serversocket.listen(1)

    def run(self):
        while True:
            (clientsocket, address) = self.serversocket.accept()
            with clientsocket:
                print('Connection from', address)
                while True:
                    # protocol - [device type],[address],[level]
                    data = clientsocket.recv(DATA_SIZE)
                    print(data.decode('utf-8'))
                    if not data:
                        break
                    cmd = data.decode('utf-8').split(',')
                    if (cmd[0] == 'b'):
                        # for (blind in blinds):
                        #     if (blind.id == cmd[1]):
                        #         blind_command = blind.blind_control.set_state(cmd[2])
                        #         await api(blind_command)
                        print("Set blind {} to {}%".format(cmd[1], cmd[2]))
                        clientsocket.sendall(data)
                
def main():
    print("TcpPyTradfri Startup!")
    tcpPyTradfri = TcpPyTradfri()
    tcpPyTradfri.run()

if __name__ == "__main__":
    main()