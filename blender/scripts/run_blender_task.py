import socket
import json
import sys

def run():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('127.0.0.1', 9876))
    
    code = """
import sys
p = r'c:\\Users\\User\\Documents\\4 - Website_ WebApp Project\\Chinese EV Configurator\\blender\\scripts'
if p not in sys.path:
    sys.path.insert(0, p)

for mod in list(sys.modules):
    if mod.startswith('seal_') or mod in ('build_seal', 'export_seal', 'cabin_parts', 'cabin_tools'):
        del sys.modules[mod]

import export_seal
res = export_seal.web(draco=True)
print('WEB EXPORT RESULT:', res)
"""
    req = json.dumps({"type": "execute_code", "params": {"code": code}})
    client.sendall((req + "\n").encode('utf-8'))
    
    data = b""
    while True:
        chunk = client.recv(4096)
        if not chunk:
            break
        data += chunk
        if b"\n" in chunk:
            break
            
    client.close()
    print("RESPONSE:", data.decode('utf-8', errors='ignore')[:1000])

if __name__ == '__main__':
    run()
