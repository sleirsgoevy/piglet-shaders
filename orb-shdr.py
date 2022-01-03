import sys

data = open(sys.argv[1], 'rb').read()

def peek(off, sz):
    return int.from_bytes(data[off:off+sz], 'little')

print('# shdr:')
footer_offset = peek(0x10, 8)
print('footer_offset =', hex(footer_offset))
print('magic =', data[0x24:0x28])
print('size =', hex(peek(0x34, 2)))
print('entry =', hex(peek(0x3c, 4)))
unk44 = peek(0x44, 2)
print('unk44 =', hex(unk44)+(' (vertex)' if unk44 == 0x144 else ' (fragment)' if unk44 == 0 else ' (unknown)'))
print('unk48 (8) =', hex(peek(0x48, 8)))
print('unk50 (4) =', hex(peek(0x50, 4)))
print('unk54 (2) =', hex(peek(0x54, 4)))
unk58 = peek(0x58, 1)
print('unk58 =', hex(unk58)+(' (vertex)' if unk58 == 1 else ' (fragment)' if unk58 in (0, 2) else ' (unknown)'))
unk60 = peek(0x60, 2)
print('unk60 =', hex(unk60)+(' (vertex)' if unk60 == 0x17 else ' (fragment)' if unk60 == 0 else ' (unknown)'))
unk62 = peek(0x62, 2)
print('unk62 =', hex(unk62)+(' (vertex)' if unk62 == 2 else ' (fragment)' if unk62 == 0 else 0))
channel_mask = peek(0x68, 4)
print('channel_mask =', hex(channel_mask)+(' (vertex)' if channel_mask == 0x20400 else ' (fragment)' if channel_mask < 16 else ' (unknown)'))

orb_shdr_offset = footer_offset

def opeek(off, sz):
    return peek(orb_shdr_offset + off, sz)

def read_rel_s(off):
    return data[orb_shdr_offset + off + opeek(off, 4):].split(b'\0', 1)[0]

print()
print('# orb_shdr:')
print('magic =', data[orb_shdr_offset+0x8:orb_shdr_offset+0x10])
print('unk14 =', data[orb_shdr_offset+0x14:orb_shdr_offset+0x18].hex())
cnt24 = opeek(0x24, 4)
print('cnt24 =', hex(cnt24))
print('cnt28 (x32) =', hex(opeek(0x28, 4)))
number_of_uniforms_2c = opeek(0x2c, 4)
print('number_of_uniforms_2c =', number_of_uniforms_2c)
number_of_samplers = opeek(0x30, 4)
print('number_of_samplers =', hex(number_of_samplers))
number_of_inputs = opeek(0x34, 1)
print('number_of_inputs =', hex(number_of_inputs))
number_of_outputs = opeek(0x35, 1)
print('number_of_outputs =', hex(number_of_outputs))
print('cnt36 (x16) =', hex(opeek(0x36, 1)))
print('cnt38 (x1) =', hex(opeek(0x38, 4)))
strings_size = opeek(0x3c, 4)
print('strings_size =', hex(strings_size))

idx = 0x40
print()
print('## sampler uniforms:')
for i in range(cnt24-1):
    print('----')
    print('index =', hex(opeek(idx, 4)))
    print('unk08 =', hex(opeek(idx+8, 4))) # all but the lowest 2 is cbz
    print('name =', read_rel_s(idx+0x14))
    idx += 0x18

print()
print('size_of_uniform_space =', hex(opeek(idx+4, 4)))
print('unk48 =', hex(opeek(idx+8, 2)))
print('number_of_uniforms_4c =', hex(opeek(idx+0xc, 4)))
print('global_cb_s =', read_rel_s(idx+0x14))
idx += 0x18

print()
print('## uniforms')
for i in range(number_of_uniforms_2c):
    print('----')
    print('type =', hex(opeek(idx+0, 1)))
    print('is_enabled =', hex(opeek(idx+1, 1)))
    print('offset08 =', hex(opeek(idx+4, 4)))
    print('size0c =', hex(opeek(idx+0x8, 4)))
    print('name =', read_rel_s(idx+0x1c))
    print('no_name_s =', read_rel_s(idx+0x20))
    idx += 0x24

print()
print('## samplers')
for i in range(number_of_samplers):
    print('----')
    print('index =', hex(opeek(idx+8, 4)))
    print('name =', read_rel_s(idx+0xc))
    idx += 0x10

print()
print('## inputs')
for i in range(number_of_inputs+number_of_outputs):
    if i == number_of_outputs:
        print()
        print('## outputs')
    print('----')
    print('type =', hex(opeek(idx, 1)))
    print('marker =', hex(opeek(idx+1, 1)))
    print('index =', hex(opeek(idx+3, 1)))
    print('name =', read_rel_s(idx+0x8))
    print('name_caps =', read_rel_s(idx+0xc))
    idx += 0x10

if not number_of_outputs:
    print()
    print('## outputs')

if orb_shdr_offset + idx + strings_size != len(data):
    print()
    print('incomplete parser, more data follows')