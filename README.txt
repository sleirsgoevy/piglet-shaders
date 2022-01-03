Layout: first header (Shdr), then GPU code from entry3c+0x34 to footer_offset_10-0x10, then footer (OrbShdr) at footer_offset_10. Possibly there is another small header between footer_offset_10-0x10 and OrbShdr.

orb-shdr.txt: description of the format in pseudo-c-structure form. cbz* -- unknown, zeroing changes nothing. unk* -- unknown, significant. known fields have meaningful names. Assume packed structs.

orb-shdr.py: parser of the format in Python. Parses and pretty-prints all known elements of the file, except actual gpu bytecode.
