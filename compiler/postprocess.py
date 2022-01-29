import sys

data = sys.stdin.buffer.read().decode('ascii', 'replace')

if '\n*** COMPILATION ERROR ***\n' in data:
    comperr = data.split('\n*** COMPILATION ERROR ***\n', 1)[1].split('\n*************************\n', 1)[0]
    print(comperr, file=sys.stderr)
    exit(1)

shader = ''.join(i for i in data.rsplit('\nPixel Shader:\n', 1)[1].split('\n*** SHADER CONFIG ***\n', 1)[0] if ord(i) in range(32, 127) or i == '\n')
sh1, sh2 = shader.split('Shader epilog disassembly:\n', 1)
sh1 = sh1.rsplit('\n', 1)[0]
sh2 = '\n'.join(i for i in sh2.split('\n') if not i.endswith(':'))
shader = [i.split(';', 1)[0].strip() for i in (sh1+'\n'+sh2).split('\n') if ' ' not in i or not i.endswith(':')]

shader_stats = {i: j for i, j in (i.split(': ', 1) for i in data.rsplit('\n*** SHADER STATS ***\n', 1)[1].split('\n********************\n', 1)[0].split('\n'))}

assert shader_stats['Spilled SGPRs'] == '0'
assert shader_stats['Spilled VGPRs'] == '0'
assert shader_stats['Private memory VGPRs'] == '0'
assert shader_stats['LDS'] == '0 blocks'
assert shader_stats['Scratch'] == '0 bytes per wave'

uniforms = []
samplers = []
offset = 0

for i in data.split('\n'):
    if i.startswith('uniform '):
        i = i.split()
        name = i[1]
        tp = int(i[3], 16)
        size = int(i[5])
        if tp == 0x8b5e: # GL_SAMPLER_2D
            samplers.append(name)
            continue
        elif tp in (
            0x1404, # GL_INT
            0x1405, # GL_UNSIGNED_INT
            0x1406, # GL_FLOAT
        ):
            size *= 4
        elif tp in range(0x8b50, 0x8b53): # GL_FLOAT_VEC?
            size *= 4 * (tp - 0x8b4e)
        elif tp in range(0x8b53, 0x8b56): # GL_INT_VEC?
            size *= 4 * (tp - 0x8b51)
        elif tp in range(0x8b5a, 0x8b5d): # GL_FLOAT_MAT?
            size *= 4 * (tp - 0x8b58) * (tp - 0x8b58)
        else:
            raise NotImplementedError(hex(tp))
        uniforms.append((tp, offset, size, name))
        offset += size

sgprs = int(shader_stats['SGPRS'])
vgprs = int(shader_stats['VGPRS'])
if samplers:
    samplers_base1 = sgprs
    sgprs += 8
    samplers_base2 = sgprs
    sgprs += 4
    uniform_base = sgprs
    sgprs += 12
else:
    uniform_base = sgprs
    sgprs += 8

idx = 0
while idx < len(shader):
    if not shader[idx].endswith(':'):
        if shader[idx].startswith('s_buffer_load_'):
            q = shader[idx].split(', ')
            q[1] = 's[%d:%d]'%(uniform_base, uniform_base+3)
            shader[idx] = ', '.join(q)
        elif shader[idx].startswith('buffer_load_'):
            q = shader[idx].split(', ')
            q[2] = 's[%d:%d]'%(uniform_base, uniform_base+3)
            shader[idx] = ', '.join(q)
        elif samplers and shader[idx].startswith('s_load_dwordx8 ') and shader[idx].endswith(', 0x100'):
            q = int(shader[idx].split('[', 1)[1].split(':', 1)[0])
            shader[idx:idx+1] = (
                's_mov_b64 s[%d:%d], s[%d:%d]'%(q+i, q+i+1, samplers_base1+i, samplers_base1+i+1)
                for i in range(0, 8, 2)
            )
        elif samplers and shader[idx].startswith('s_load_dwordx4 ') and shader[idx].endswith(', 0x10c'):
            q = int(shader[idx].split('[', 1)[1].split(':', 1)[0])
            shader[idx:idx+1] = (
                's_mov_b64 s[%d:%d], s[%d:%d]'%(q+i, q+i+1, samplers_base2+i, samplers_base2+i+1)
                for i in (0, 2)
            )
    idx += 1

shader = '\n'.join(shader)

m0 = uniform_base + 4

orbis_types = {
    0x1406: 0,
    0x8b50: 1,
    0x8b51: 2,
    0x8b52: 3,
    0x1404: 8,
    0x8b53: 9,
    0x8b54: 10,
    0x8b55: 11,
    0x1405: 12,
    0x8dc6: 13,
    0x8dc7: 14,
    0x8dc8: 15,
    0x8b5a: 25,
    0x8b65: 26,
    0x8b66: 27,
    0x8b67: 29,
    0x8b5b: 30,
    0x8b68: 31,
    0x8b69: 33,
    0x8b6a: 34,
    0x8b5c: 35,
}

with open(sys.argv[2], 'w') as file:
    print('gprs', sgprs, vgprs, file=file)
    if m0 >= 32:
        print('m0', 16, file=file)
        print('uniform_reg', 12, file=file)
        if samplers:
            print('sampler_reg', 8, file=file)
    else:
        print('m0', m0, file=file) # seems that for some reason m0 value must be upper than uniform buffer
        print('uniform_reg', uniform_base, file=file)
        if samplers:
            print('sampler_reg', samplers_base2, file=file)
    for (tp, offset, sz, name) in uniforms:
        print('uniform', name, orbis_types[tp], offset, sz, file=file)
    for name in samplers:
        print('sampler', name, file=file)
    print('output', 'main', 3, 0, file=file)

with open(sys.argv[1], 'w') as file:
    shader = '\n'.join(i.replace('exp mrt0 ', 'exp mrt0, ') for i in shader.split('\n'))
    if m0 >= 32:
        print('s_mov_b32 s5, s16', file=file)
        for i in range(0, 4, 2):
            print('s_mov_b64 s[%d:%d], s[%d:%d]'%(uniform_base+i, uniform_base+i+1, 12+i, 13+i), file=file)
            print('s_mov_b64 s[%d:%d], s[%d:%d]'%(samplers_base2+i, samplers_base2+i+1, 8+i, 9+i), file=file)
    elif m0 != 5:
        print('s_mov_b32 s5, s%d'%m0, file=file)
    print('v_mov_b32 v2, v0', file=file)
    print('v_mov_b32 v3, v1', file=file)
    if samplers:
        for i in range(0, 8, 2):
            print('s_mov_b64 s[%d:%d], s[%d:%d]'%(samplers_base1+i, samplers_base1+i+1, i, i+1), file=file)
    file.write(shader)
