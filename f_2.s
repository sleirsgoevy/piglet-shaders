.section .text

shdr:
.int 0, 0
.int 0, 0
.int orb_shdr-shdr, 0 #footer_offset
.int 0, 0
.int 0
.ascii "Shdr"
.int 0, 0
.int 0
.short (orb_shdr-shdr) - (entry-shdr) + 0x24 #size
.short 0
.int 0
.int (entry-shdr) - 0x34
.int 0
.short 0x80 #nreg (24 scalar, 4 vector)
.short 0
.int 32, 0 #unk48
.int 4 #always4
.int 2 #shader_type_54
.byte 2 #unk58
.byte 0
.short 0
.byte 1, 0, 0, 0#.int 0
.int 0 #shader_type_60
.int 0
.int 0xf #channel_mask
.int 0

entry:
s_mov_b32 vcc_hi, lit(15)
s_mov_b32 m0, s16
s_buffer_load_dword s12, s[12:15], 0x0
s_mov_b64 vcc, exec
s_wqm_b64 exec, exec
v_interp_p1_f32 v2, v0, attr0.x
v_interp_p1_f32 v3, v0, attr0.y
v_interp_p2_f32 v2, v1, attr0.x
v_interp_p2_f32 v3, v1, attr0.y
image_sample v[0:3], v[2:5], s[0:7], s[8:11] dmask:15
s_waitcnt vmcnt(0) & lgkmcnt(0)
v_mul_f32 v0, s12, v0
v_mul_f32 v1, s12, v1
v_mul_f32 v3, s12, v3
v_mul_f32 v2, s12, v2
v_cvt_pkrtz_f16_f32 v0, v0, v1
v_cvt_pkrtz_f16_f32 v1, v2, v3
s_mov_b64 exec, vcc
exp mrt0, v0, v0, v1, v1 done compr vm
s_endpgm

.int 0 #cbz_f0
.short 1 #unk_f4
.short 8 #unk_f6
.short 2 #unk_f8
.short 12 #unk_fa
.int 0 #buffer_source
orb_shdr:
.int 0, 0
.asciz "OrbShdr"
.int 0
.short 0x0303 #unk14
.short 0
.int 0, 0
.int 0
.int 2 #number_of_sampler_uniforms
.int 0 #cnt28
.int 1 #number_of_uniforms_2c
.int 1 #number_of_samplers
.byte 1 #number_of_inputs
.byte 1 #number_of_outputs
.byte 0 #cnt36
.byte 0
.int 0 #cnt38
.int strings_end-strings_start #strings_size

## sampler uniforms
.int 0 #index
.int 0
.byte 2 #unk08
.byte 0
.byte 0
.byte 0
.int 0
.int 0
rel1:
.int s_sampler-rel1

.int 0
.int 4 #size_of_uniform_space
.byte 0x16 #unk48
.byte 0
.short 0
.int 1 #number_of_uniforms_4c
.int 0
rel2:
.int global_cb_s-rel2

## uniforms
.byte 0 #type
.byte 1 #is_enabled
.byte 0
.byte 0
.int 0 #offset04
.int 4 #size08
.int 0
.int 0, 0
.int 0
rel3:
.int u_opacity-rel3 #name
rel4:
.int no_name_s-rel4

## samplers
.int 0, 0
.int 0 #index
rel5:
.int samplers2D_0-rel5 #name

## inputs
.byte 1 #type
.byte 0x24 #marker
.byte 0
.byte 0 #index
.int 0
rel6:
.int v_transformedTexCoord-rel6 #name
rel7:
.int V_TRANSFORMEDTEXCOORD-rel7 #name_caps

## outputs
.byte 3 #type
.byte 0x38 #marker
.byte 0
.byte 0 #index
.int 0
rel8:
.int main_s-rel8 #name
rel9:
.int no_name_s-rel9 #name_caps

strings_start:
s_sampler:
.asciz "s_sampler"
global_cb_s:
.asciz "__GLOBAL_CB__"
u_opacity:
.asciz "u_opacity"
no_name_s:
.asciz "(no_name)"
samplers2D_0:
.asciz "samplers2D[0]"
v_transformedTexCoord:
.asciz "v_transformedTexCoord"
V_TRANSFORMEDTEXCOORD:
.asciz "V_TRANSFORMEDTEXCOORD"
main_s:
.asciz "main"
.byte 0
strings_end:
