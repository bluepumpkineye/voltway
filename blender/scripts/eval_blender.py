import socket
import json
import sys

def eval_code(code_str, timeout=300):
    s = socket.socket()
    s.settimeout(timeout)
    s.connect(('127.0.0.1', 9876))
    payload = json.dumps({'type': 'execute_code', 'params': {'code': code_str}})
    s.sendall(payload.encode('utf-8'))
    chunks = []
    while True:
        try:
            chunk = s.recv(65536)
            if not chunk:
                break
            chunks.append(chunk)
            data = b''.join(chunks)
            try:
                obj = json.loads(data.decode('utf-8'))
                return obj
            except Exception:
                continue
        except Exception as e:
            print("Socket error:", e)
            break
    s.close()
    return None

if __name__ == '__main__':
    code = sys.argv[1] if len(sys.argv) > 1 else 'import bpy; print("Objects:", len(bpy.data.objects))'
    res = eval_code(code)
    print("Result:", res)
