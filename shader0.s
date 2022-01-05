.section .text

shdr:
.int 0, 0
.int 0, 0
.int orb_shdr-shdr, 0
.int 0, 0
.int 0
.ascii "Shdr"
.int 0, 0
.int 0
.short (orb_shdr-shdr) - (entry-shdr) + 0x24
.short 0
.int 0
.int (entry-shdr) - 0x34
.int 0
.short 0
.short 0
.int 8, 0
.int 4
.int 2
.byte 2
.byte 0
.short 0
.int 0
.int 0
.int 0
.int 0xf
.int 0

.int 0

entry:
s_mov_b32 vcc_hi, lit(7)
s_buffer_load_dwordx4 s[0:3], s[0:3], 0x0
s_waitcnt lgkmcnt(0)
v_mov_b32 v1, s1
v_mov_b32 v0, s3
v_cvt_pkrtz_f16_f32 v1, s0, v1
v_cvt_pkrtz_f16_f32 v0, s2, v0
exp mrt0, v1, v1, v0, v0 done compr vm
s_endpgm

.align 16
.int 0, 0, 0
orb_shdr:
.int 0, 0
.ascii "OrbShdr"
.byte 7
.int 0
.byte 2, 1, 12, 5
.int 0, 0
.int 0
.int 1
.int 0
.int 1
.int 0
.byte 0
.byte 1
.byte 0
.byte 0
.int 0
.int strings_end-strings_start

.int 0
.int 16
.short 0x416
.short 0
.int 1
.int 0
rel1:
.int global_cb-rel1

.byte 3
.byte 1
.byte 0
.byte 0
.int 0
.int 16
.int 0
.int 0, 0
.int 0
rel2:
.int fillColor-rel2
rel3:
.int no_name-rel3

rel4:
.byte 3
.byte 0x38
.byte 0
.byte 0
.int 0
rel5:
.int main-rel5
rel6:
.int no_name-rel6

strings_start:
global_cb:
.asciz "__GLOBAL_CB__"
no_name:
.asciz "(no_name)"
fillColor:
.asciz "fillColor"
main:
.asciz "main"
.byte 0
strings_end:
