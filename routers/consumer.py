from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import List
import json, re

ws_rounter = APIRouter() # domain rounter

# Instantiate variables
class Pattern:
    def __init__(self):
        self.val = "^[0-9|a-z|A-Z|ㄱ-ㅎ|ㅏ-ㅣ|가-힣]*$"

class PIN:
    def __init__(self):
        self.status = {
            "red" : [21, 21, 21, 21],
            "blue" : [21, 21, 21, 21],
            "green" : [21, 21, 21, 21],
            "fan" : [21, 21],
        }

class LED:
    def __init__(self):
        self.status = {
            "type": True,
            "red": [False, False, False, False],
            "green": [False, False, False, False],
            "blue": [False, False, False, False]
        }

class RAS:
    def __init__(self):
        self.status = {
            "type" : True,
            "speed" : '50',
            "string" : ''
        }
        self.client_ip = {} # ip
        

led = LED()
ras = RAS()
pin = PIN()

# led panel handshake
@ws_rounter.websocket("/ws/led")
async def websocket_endpoint_led(websocket: WebSocket):
    
    # accept signal
    await websocket.accept()
    await websocket.send_text(json.dumps(led.status))

    try:
        while True:
            # wait receive data
            data = await websocket.receive_text()
            data = json.loads(data)

            if data['type']:
                # led update
                for pin_color in data:
                    if type(data[pin_color]) == list:
                        for idx, pin in enumerate(data[pin_color]):

                            if type(pin) == bool:
                                led.status[pin_color][idx] = pin
                            else:
                                raise HTTPException(status_code=400, detail="request is invalid")
                        
            else: # add new ip address
                if data['ip'] not in ras.client_ip:
                    ras.client_ip[websocket] = data['ip']
                
                    # print(f"new add {ras.client_ip}")

            # led status broadcast
            for client in ras.client_ip:
                await client.send_text(json.dumps(led.status))
            
            # print(f"broadcast list {ras.client_ip}")

    except WebSocketDisconnect:
        del ras.client_ip[websocket]

# ras panel handshake
@ws_rounter.websocket("/ws/ras")
async def websocket_endpoint_ras(websocket: WebSocket):
    
    await websocket.accept()
    await websocket.send_text(json.dumps(ras.status))

    try:
        while True:
            # wait receive data
            data = await websocket.receive_text()
            data = json.loads(data)

            if data['type']:
                # name update
                if type(data['string']) == str: # check input
                    pattern = r'^[a-zA-Z0-9;:,.?!-_()*%#\s]{0,16}$'
                    if re.match(pattern, data['string']):
                        ras.status["string"] = data['string']
                
                else:
                    raise HTTPException(status_code=400, detail="request is invalid")
                # fan update
                if type(data['speed']) == str: # check input
                    if 0 <= int(data['speed']) and int(data['speed']) <= 100:
                        ras.status["speed"] = data['speed'] # save data
                else:
                    raise HTTPException(status_code=400, detail="request is invalid")
                
            else: # add new ip address
                # print(f"all ip {ras.client_ip}")
                if data['ip'] not in ras.client_ip:
                    ras.client_ip[websocket] = data['ip']
                    
                    # print(f"new add {ras.client_ip}")
                    # print(f"all ip {ras.client_ip}")

            # ras status broadcast
            for client in ras.client_ip:
                # print(f"보냄 {ras.status}")
                await client.send_text(json.dumps(ras.status))

            # print(f"broadcast list {ras.client_ip}")

    except WebSocketDisconnect:
        del ras.client_ip[websocket]
