const net = require('net');

const client = new net.Socket();
let code = `
import sys, os, time
p = r'c:\\Users\\User\\Documents\\4 - Website_ WebApp Project\\Chinese EV Configurator\\blender\\scripts'
if p not in sys.path:
    sys.path.insert(0, p)

for mod in list(sys.modules):
    if mod.startswith('seal_') or mod in ('build_seal', 'export_seal', 'cabin_parts', 'cabin_tools'):
        del sys.modules[mod]

import export_seal
res = export_seal.web(draco=True)
print("WEB_RESULT_SUCCESS:", res)
`;

const payload = JSON.stringify({
  type: 'execute_code',
  params: { code: code }
}) + '\n';

client.connect(9876, '127.0.0.1', () => {
  console.log('Connected to Blender socket. Sending task...');
  client.write(payload);
});

let responseData = '';
client.on('data', (data) => {
  responseData += data.toString('utf8');
  if (responseData.includes('\n')) {
    console.log('Received response from Blender:');
    console.log(responseData.slice(0, 2000));
    client.destroy();
  }
});

client.on('close', () => {
  console.log('Connection closed');
});

client.on('error', (err) => {
  console.error('Socket error:', err);
});
