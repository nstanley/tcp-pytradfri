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
CONFIG_FILE = "tradfri_standalone_psk.conf"

# Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument(
    "host", metavar="IP", type=str, help="IP Address of your Tradfri gateway"
)
parser.add_argument(
    "-K", "--key", dest="key", required=False, help="Key found on your Tradfri gateway"
)
args = parser.parse_args()

if args.host not in load_json(CONFIG_FILE) and args.key is None:
    print(
        "Please provide the 'Security Code' on the back of your " "Tradfri gateway:",
        end=" ",
    )
    key = input().strip()
    if len(key) != 16:
        raise PytradfriError("Invalid 'Security Code' provided.")
    else:
        args.key = key

# Class definition
class TcpPyTradfri():
    def __init__(self):
        # TCP socket for Crestron
        self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serversocket.bind((ADDR, PORT))
        self.serversocket.listen(1)
        print("Bind to socket on port {}".format(PORT))
    
    async def setup(self):
        # Setup connection to Tradfri
        conf = load_json(CONFIG_FILE)
        try:
            identity = conf[args.host].get("identity")
            psk = conf[args.host].get("key")
            api_factory = await APIFactory.init(host=args.host, psk_id=identity, psk=psk)
        except KeyError:
            identity = uuid.uuid4().hex
            api_factory = await APIFactory.init(host=args.host, psk_id=identity)

            try:
                psk = await api_factory.generate_psk(args.key)
                print("Generated PSK: ", psk)

                conf[args.host] = {"identity": identity, "key": psk}
                save_json(CONFIG_FILE, conf)
            except AttributeError:
                raise PytradfriError(
                    "Please provide the 'Security Code' on the "
                    "back of your Tradfri gateway using the "
                    "-K flag."
                )
        self.api = api_factory.request

        gateway = Gateway()

        devices_command = gateway.get_devices()
        devices_commands = await self.api(devices_command)
        devices = await self.api(devices_commands)
        self.blinds = [dev for dev in devices if dev.has_blind_control]
        for blind in self.blinds:
            print("Found blind {}, \"{}\"".format(blind.id, blind.name))

    async def run(self):
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
                    devId = int(cmd[1])
                    level = int(cmd[2])
                    # blind control
                    if (cmd[0] == 'b'):
                        for blind in self.blinds:
                            if (int(blind.id) == devId):
                                print("Set blind {} to {}%".format(devId, level))
                                blind_command = blind.blind_control.set_state(level)
                                await self.api(blind_command)
                                clientsocket.sendall(data)
                    # get batter charge
                    elif (cmd[0] == 'c'):
                        for blind in self.blinds:
                            if (int(blind.id) == devId):
                                clientsocket.sendall("c,{},{}".format(blind.id, blind.device_info.battery_level).encode())
                    elif (cmd[0] == 'u'):
                        for blind in self.blinds:
                            blind_command = blind.blind_control.set_state(0)
                            await self.api(blind_command)
                            print("Set blind {} to 0 (up)".format(blind.id))
                        clientsocket.sendall(data)
                    elif (cmd[0] == 'd'):
                        for blind in self.blinds:
                            blind_command = blind.blind_control.set_state(100)
                            await self.api(blind_command)
                            print("Set blind {} to 0 (down)".format(blind.id))
                        clientsocket.sendall(data)
                    elif (cmd[0] == 's'):
                        for blind in self.blinds:
                            blind_command = blind.blind_control.trigger_blind()
                            await self.api(blind_command)
                            print("Stop blind {}".format(blind.id))
                        clientsocket.sendall(data)
                
async def main():
    print("TcpPyTradfri Startup!")
    tcpPyTradfri = TcpPyTradfri()
    await(tcpPyTradfri.setup())
    await(tcpPyTradfri.run())

if __name__ == "__main__":
    asyncio.run(main())