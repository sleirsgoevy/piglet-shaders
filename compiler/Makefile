all: libpreload.so victim

libpreload.so: preload.c
	gcc preload.c -O0 -shared -ldl -fPIE -fPIC -o libpreload.so -g

victim: victim.c
	gcc victim.c -o victim -lX11 -lEGL -lGLESv2

clean:
	rm -f libpreload.so victim
