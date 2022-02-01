import sys

fragment = True

if '-v' in sys.argv:
    del sys.argv[sys.argv.index('-v')]
    fragment = False

if '-f' in sys.argv:
    del sys.argv[sys.argv.index('-f')]
    fragment = True

data = sys.stdin.buffer.read().decode('ascii', 'replace')

if '\n*** COMPILATION ERROR ***\n' in data:
    comperr = data.split('\n*** COMPILATION ERROR ***\n', 1)[1].split('\n*************************\n', 1)[0]
    print(comperr, file=sys.stderr)
    exit(1)

shader = ''.join(i for i in data.rsplit('\nPixel Shader:\n' if fragment else '\nVertex Shader as VS:\n', 1)[1].split('\n*** SHADER CONFIG ***\n', 1)[0].split('\n*** SHADER STATS ***\n', 1)[0] if ord(i) in range(32, 127) or i == '\n')
sh1, sh2 = shader.split('Shader epilog disassembly:\n' if fragment else 'Shader main disassembly:\n', 1)
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
attributes = []
offset = 0

for i in data.split('\n'):
    if i.startswith('uniform '):
        i = i.split()
        name = i[1]
        tp = int(i[3], 16)
        size = int(i[5])
        if tp == 0x8b5e: # GL_SAMPLER_2D
            assert size == 1
            if fragment:
                samplers.append(name)
            continue
        elif tp in (
            0x1404, # GL_INT
            0x1405, # GL_UNSIGNED_INT
            0x1406, # GL_FLOAT
        ):
            item_size = 4
        elif tp in range(0x8b50, 0x8b53): # GL_FLOAT_VEC?
            item_size = 4 * (tp - 0x8b4e)
        elif tp in range(0x8b53, 0x8b56): # GL_INT_VEC?
            item_size = 4 * (tp - 0x8b51)
        elif tp in range(0x8b5a, 0x8b5d): # GL_FLOAT_MAT?
            item_size = 4 * (tp - 0x8b58) * (tp - 0x8b58)
        else:
            raise NotImplementedError(hex(tp))
        uniforms.append((tp, offset, size, item_size, name))
        offset += size * item_size
    elif i.startswith('attribute ') and not fragment:
        i = i.split()
        name = i[1]
        tp = int(i[3], 16)
        size = int(i[5])
        assert size == 1
        if tp not in (
            0x1404, 0x1405, 0x1406,
            0x8b50, 0x8b51, 0x8b52,
            0x8b53, 0x8b54, 0x8b55
        ):
            raise NotImplementedError(hex(tp))
        attributes.append((name, tp))

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
if attributes:
    attr_base = vgprs
    vgprs += 4 * (len(attributes) + 1)
else:
    attr_base = 256

# here try to parse the assembly to adapt to sony's abi
# probably incomplete
idx = 0

s_regs = {'s2': 'uniform_base', 's3': 'sampler_base', 's8': 'attr_base', 's12': 'attr_0', 's13': 'attr_0', 's14': 'attr_0', 's15': 'attr_0'}
for i in map('s%d'.__mod__, range(sgprs)):
    if i not in s_regs:
        s_regs[i] = 'unknown'

while idx < len(shader):
    if not shader[idx].endswith(':'):
        ss = shader[idx].split(' ')
        if ss[0].endswith('_e32'):
            ss[0] = ss[0][:-4]
        shader[idx] = ' '.join(ss)
        if shader[idx].startswith('s_mov_b32 '):
            q = shader[idx].split(' ', 1)[1].split(', ')
            if q[1] in s_regs:
                s_regs[q[0]] = s_regs[q[1]]
            else:
                try: int(q[1], 0)
                except ValueError:
                    s_regs[q[0]] = 'unknown'
                else:
                    s_regs[q[0]] = 'constant'
        elif shader[idx].startswith('s_mov_b64 '):
            q = shader[idx].split(' ', 1)[1].split(', ')
            dst_reg = int(q[0].split('[', 1)[1].split(':', 1)[0])
            if q[1] == 'exec':
                s_regs['s%d'%dst_reg] = s_regs['s%d'%(dst_reg+1)] = 'exec'
            else:
                assert q[1].startswith('s[')
                src_reg = int(q[1].split('[', 1)[1].split(':', 1)[0])
                try: s_regs['s%d'%dst_reg] = s_regs['s%d'%src_reg]
                except KeyError: s_regs['s%d'%dst_reg] = 'unknown'
                try: s_regs['s%d'%(dst_reg+1)] = s_regs['s%d'%(src_reg+1)]
                except KeyError: s_regs['s%d'%(dst_reg+1)] = 'unknown'
        elif shader[idx].startswith('s_movk_i32 '):
            s_regs[shader[idx].split(' ', 1)[1].split(', ')[0]] = 'constant'
        elif shader[idx].startswith('s_buffer_load_'):
            q = shader[idx].split(', ')
            old_reg = int(q[1].split('[', 1)[1].split(':', 1)[0])
            if s_regs['s%d'%old_reg] == 'uniform_base' and s_regs['s%d'%(old_reg+1)] == s_regs['s%d'%(old_reg+2)] == s_regs['s%d'%(old_reg+3)] == 'constant':
                q[1] = 's[%d:%d]'%(uniform_base, uniform_base+3)
            else:
                print('warning: unrecognized s_buffer_load_*')
            shader[idx] = ', '.join(q)
        elif shader[idx].startswith('buffer_load_'):
            q = shader[idx].split(', ')
            old_reg = int(q[2].split('[', 1)[1].split(':', 1)[0])
            if s_regs['s%d'%old_reg] == 'uniform_base' and s_regs['s%d'%(old_reg+1)] == s_regs['s%d'%(old_reg+2)] == s_regs['s%d'%(old_reg+3)] == 'constant':
                q[2] = 's[%d:%d]'%(uniform_base, uniform_base+3)
                shader[idx] = ', '.join(q)
            elif s_regs['s%d'%old_reg] == s_regs['s%d'%(old_reg+1)] == s_regs['s%d'%(old_reg+2)] == s_regs['s%d'%(old_reg+3)] and s_regs['s%d'%old_reg].startswith('attr_'):
                q[0] = q[0].split(' ', 1)[1]
                if '[' in q[0]:
                    first, last = map(int, q[0].split('[', 1)[1].split(']', 1)[0].split(':'))
                else:
                    first = last = int(q[0][1:])
                base = attr_base + 4 * int(s_regs['s%d'%old_reg][5:])
                shader[idx:idx+1] = ('v_mov_b32 v%d, v%d'%(i, i+base-first) for i in range(first, last+1))
            else:
                print('warning: unrecognized buffer_load_*')
        elif shader[idx].startswith('s_load_dwordx8 '):
            q = int(shader[idx].split('[', 1)[1].split(':', 1)[0])
            old_reg = int(shader[idx].split('[', 2)[2].split(':', 1)[0])
            if samplers and s_regs['s%d'%old_reg] == 'sampler_base' and s_regs['s%d'%(old_reg+1)] == 'constant' and shader[idx].endswith(', 0x100'):
                shader[idx:idx+1] = (
                    's_mov_b64 s[%d:%d], s[%d:%d]'%(q+i, q+i+1, samplers_base1+i, samplers_base1+i+1)
                    for i in range(0, 8, 2)
                )
                idx += 3
            else:
                print('warning: unrecognized s_load_dwordx8')
        elif shader[idx].startswith('s_load_dwordx4 '):
            q = int(shader[idx].split('[', 1)[1].split(':', 1)[0])
            old_reg = int(shader[idx].split('[', 2)[2].split(':', 1)[0])
            if samplers and s_regs['s%d'%old_reg] == 'sampler_base' and s_regs['s%d'%(old_reg+1)] == 'constant' and shader[idx].endswith(', 0x10c'):
                shader[idx:idx+1] = (
                    's_mov_b64 s[%d:%d], s[%d:%d]'%(q+i, q+i+1, samplers_base2+i, samplers_base2+i+1)
                    for i in (0, 2)
                )
                idx += 1
            elif s_regs['s%d'%old_reg] == 'attr_base' and s_regs['s%d'%(old_reg+1)] == 'constant':
                index = int(shader[idx].split(', ')[-1], 0)
                assert index % 4 == 0
                for i in range(q, q+4):
                    s_regs['s%d'%i] = 'attr_%d'%(index // 4 + 1)
                shader[idx:idx+1] = ()
                continue
            else:
                print('warning: unrecognized s_load_dwordx4')
    idx += 1

shader = '\n'.join(shader)

if fragment:
    m0 = uniform_base + 4
else:
    m0 = 8

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
    if not fragment:
        print('vertex', file=file)
    print('gprs', sgprs, vgprs, file=file)
    if m0 >= 32:
        print('m0', 16, file=file)
        print('uniform_reg', 12, file=file)
        if samplers:
            print('sampler_reg', 8, file=file)
    elif not fragment and uniform_base > 4:
        print('m0', m0, file=file) # see below
        print('uniform_reg', 4, file=file)
    else:
        print('m0', m0, file=file) # seems that for some reason m0 value must be upper than uniform buffer
        print('uniform_reg', uniform_base, file=file)
        if samplers:
            print('sampler_reg', samplers_base2, file=file)
    for (tp, offset, sz, itemsz, name) in uniforms:
        print('uniform', name.split('[', 1)[0], orbis_types[tp], offset, itemsz, sz, file=file)
    for name in samplers:
        print('sampler', name, file=file)
    if fragment:
        print('output', 'main', 3, 0, file=file)
    elif attributes:
        for idx, (name, tp) in enumerate(attributes):
            print('input', name, orbis_types[tp], idx, file=file)

with open(sys.argv[1], 'w') as file:
    shader = '\n'.join('exp '+i[4:].replace(' ', ', ', 1) if i.startswith('exp ') else i for i in shader.split('\n'))
    if not fragment:
        # abi call
        print('s_swappc_b64 s[0:1], s[0:1]', file=file)
    if m0 >= 32:
        print('s_mov_b32 s5, s16', file=file)
        for i in range(0, 4, 2):
            print('s_mov_b64 s[%d:%d], s[%d:%d]'%(uniform_base+i, uniform_base+i+1, 12+i, 13+i), file=file)
            print('s_mov_b64 s[%d:%d], s[%d:%d]'%(samplers_base2+i, samplers_base2+i+1, 8+i, 9+i), file=file)
    elif not fragment and uniform_base > 4:
        for i in range(0, 4, 2):
            print('s_mov_b64 s[%d:%d], s[%d:%d]'%(uniform_base+i, uniform_base+i+1, 4+i, 5+i), file=file)
    elif m0 != 5:
        print('s_mov_b32 s5, s%d'%m0, file=file)
    if attributes:
        for i in range(len(attributes) * 4):
            print('v_mov_b32 v%d, v%d'%(attr_base+i, 4+i), file=file)
    print('v_mov_b32 v2, v0', file=file)
    print('v_mov_b32 v3, v1', file=file)
    if samplers:
        for i in range(0, 8, 2):
            print('s_mov_b64 s[%d:%d], s[%d:%d]'%(samplers_base1+i, samplers_base1+i+1, i, i+1), file=file)
    file.write(shader)
