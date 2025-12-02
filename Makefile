all: tracker peer

tracker: tracker.c
	gcc tracker.c -o tracker -pthread

peer: peer.c
	gcc peer.c -o peer -pthread

clean:
	rm tracker peer
