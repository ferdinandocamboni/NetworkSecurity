from scapy.all import rdpcap, Dot11CCMP

pkts = rdpcap("capture-6.pcap")

# Estrae il campo Data cifrato escludendo gli ultimi 8 byte del CCMP MIC
c1 = bytes(pkts[289][Dot11CCMP].data)[:-8]  # 1423 byte (pacchetto 290)
c2 = bytes(pkts[478][Dot11CCMP].data)[:-8]  # 237 byte  (pacchetto 479)

# Calcola C1 XOR C2 (= P1 XOR P2) sui primi 237 byte
xor_p1_p2 = bytes(a ^ b for a, b in zip(c1, c2))
with open("expense-formq.txt", "rb") as f:
    form_bytes = f.read()

# Cerca l'offset in cui P1 (expense-form_2.txt) rivela testo ASCII leggibile in P2
for offset in range(40, 200):
    p2_segment = bytes(
        xor_p1_p2[offset + i] ^ form_bytes[i]
        for i in range(min(len(xor_p1_p2) - offset, len(form_bytes)))
    )
    if b"POST" in p2_segment or b"HTTP" in p2_segment or b"netsec{" in p2_segment:
        print(f"Offset {offset}: {p2_segment}")