import sys

n_sgpr = 8
n_vgpr = 4
m0_reg = 0
fragment = True
channel_mask = 15
uniform_ptr_reg = 0
sampler_ptr_reg = -1
size_of_uniform_space = 0
uniforms = []
samplers = []
inputs = []
outputs = []

strings = '__GLOBAL_CB__\0(no_name)\0'

with open(sys.argv[1]) as file:
    for line in file:
        line = line.split()
        if not line: continue
        if line[0] == 'vertex':
            assert len(line) == 1
            fragment = False
        elif line[0] == 'fragment':
            assert len(line) == 1
            fragment = True
        elif line[0] == 'gprs':
            assert len(line) == 3
            n_sgpr = int(line[1])
            assert n_sgpr in range(8, 105, 8)
            n_vgpr = int(line[2])
            assert n_vgpr in range(4, 257, 4)
        elif line[0] == 'm0':
            assert len(line) == 2
            m0_reg = int(line[1])
        elif line[0] == 'channel_mask':
            assert len(line) == 2
            channel_mask = int(line[1], 0)
        elif line[0] == 'uniform_reg':
            assert len(line) == 2
            uniform_ptr_reg = int(line[1])
            strings += line[1] + '\0'
        elif line[0] == 'sampler_reg':
            assert len(line) == 2
            sampler_ptr_reg = int(line[1])
        elif line[0] == 'uniform':
            assert len(line) in (5, 6)
            name = line[1]
            tp = int(line[2])
            offset = int(line[3])
            size = int(line[4])
            arraysz = int(line[5]) if len(line) > 5 else 1
            size_of_uniform_space = max(size_of_uniform_space, offset+size*arraysz)
            uniforms.append((tp, offset, size, arraysz, name))
            strings += name + '\0'
        elif line[0] == 'sampler':
            assert len(line) == 2
            strings += line[1] + '\0'
            strings += 'sampler2D[%d]\0' % len(samplers)
            samplers.append(line[1])
        elif line[0] == 'input':
            assert len(line) == 4
            name = line[1]
            tp = int(line[2])
            index = int(line[3])
            inputs.append((tp, index, name))
            strings += line[1] + '\0'
            strings += line[1].upper() + '\0'
        elif line[0] == 'output':
            assert len(line) == 4
            name = line[1]
            tp = int(line[2])
            index = int(line[3])
            outputs.append((tp, index, name))
            strings += line[1] + '\0'
            strings += line[1].upper() + '\0'

with open(sys.argv[2], 'rb') as file:
    gcn_bytecode = file.read()

if not fragment:
    channel_mask = 0x20400

if sampler_ptr_reg < 0:
    sampler_ptr_reg = 0 if fragment else 2

orb_shdr_offset = (0x73 + len(gcn_bytecode)) & -4

data = b''
data += bytes(16)
data += (orb_shdr_offset + 16).to_bytes(8, 'little')
data += bytes(12)
data += b'Shdr'
data += bytes(12)
data += (orb_shdr_offset - 0x3c).to_bytes(2, 'little')
data += bytes(1)
data += b'\x00' if fragment else b'\x03'
data += bytes(4)
data += b'\x3c\x00\x00\x00'
data += bytes(4)
data += ((n_sgpr // 8 - 1) * 64 + (n_vgpr // 4 - 1)).to_bytes(2, 'little')
data += bytes(2)
data += (m0_reg*2).to_bytes(8, 'little')
data += b'\x04\x00\x00\x00'
data += b'\x02\x00\x00\x00' if fragment else b'\x00\x00\x00\x00'
data += b'\x02'
data += bytes(3)
data += b'\x01\x00\x00\x00'
data += b'\x00\x00\x00\x00' if fragment else b'\x17\x00\x02\x00'
data += bytes(4)
data += channel_mask.to_bytes(4, 'little')
data += bytes(4)

data += gcn_bytecode
data += bytes(orb_shdr_offset - len(data))

strings_start = len(data) + 0x50 + 0x18 * len(samplers) + 0x18 + 0x24 * len(uniforms) + 0x10 * len(samplers) + 0x10 * (len(inputs) + len(outputs))

data += b'\x00\x00' if fragment else b'\x12\x00'
data += bytes(2)
data += b'\x17\x00' if not fragment else b'\x01\x00' if samplers else b'\x00\x00'
data += sampler_ptr_reg.to_bytes(2, 'little')
data += b'\x02\x00' #XXX
data += uniform_ptr_reg.to_bytes(2, 'little')
data += b'\x02\x00\x00\x00'
data += bytes(8)
data += b'OrbShdr\x00'
data += bytes(4)
data += b'\x03\x03' #XXX: what is this?
data += bytes(14)
data += (len(samplers) + 1).to_bytes(4, 'little')
data += b'\x00\x00\x00\x00'
data += len(uniforms).to_bytes(4, 'little')
data += len(samplers).to_bytes(4, 'little')
data += bytes((len(inputs),))
data += bytes((len(outputs),))
data += b'\x00'
data += bytes(5)
data += len(strings).to_bytes(4, 'little')

for idx, name in enumerate(samplers):
    data += idx.to_bytes(4, 'little')
    data += bytes(4)
    data += b'\x02'
    data += bytes(11)
    data += (strings_start + strings.find(name+'\0') - len(data)).to_bytes(4, 'little')

data += bytes(4)
data += size_of_uniform_space.to_bytes(4, 'little')
data += b'\x16'
data += bytes(3)
data += len(uniforms).to_bytes(4, 'little')
data += bytes(4)
data += (strings_start - len(data)).to_bytes(4, 'little')

for (tp, offset, size, arraysz, name) in uniforms:
    data += bytes((tp,))
    data += bytes((1,))
    data += bytes(2)
    data += offset.to_bytes(4, 'little')
    data += (size * arraysz).to_bytes(4, 'little')
    data += (arraysz if arraysz != 1 else 0).to_bytes(4, 'little')
    data += bytes(12)
    data += (strings_start + strings.find(name+'\0') - len(data)).to_bytes(4, 'little')
    data += (strings_start + 14 - len(data)).to_bytes(4, 'little')

for idx in range(len(samplers)):
    data += bytes(8)
    data += idx.to_bytes(4, 'little')
    data += (strings_start + strings.find('sampler2D[%d]\0'%idx) - len(data)).to_bytes(4, 'little')

for (tp, index, name) in inputs:
    data += bytes((tp,))
    data += bytes((0x28,))
    data += bytes(1)
    data += bytes((index,))
    data += bytes(4)
    data += (strings_start + strings.find(name+'\0') - len(data)).to_bytes(4, 'little')
    data += (strings_start + strings.find(name.upper()+'\0') - len(data)).to_bytes(4, 'little')

for (tp, index, name) in outputs:
    data += bytes((tp,))
    data += bytes((0x28,))
    data += bytes(1)
    data += bytes((index,))
    data += bytes(4)
    data += (strings_start + strings.find(name+'\0') - len(data)).to_bytes(4, 'little')
    data += (strings_start + strings.find(name.upper()+'\0') - len(data)).to_bytes(4, 'little')

assert len(data) == strings_start
data += strings.encode('ascii')

with open(sys.argv[3], 'wb') as file:
    file.write(data)
