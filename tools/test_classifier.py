from barkoder_reader import collect_barcodes
from classifier import classify_barcodes

raw_barcodes = collect_barcodes()
classified = classify_barcodes(raw_barcodes)

print("RAW BARCODES:")
print(raw_barcodes)

print("\nCLASSIFIED:")
for k, v in classified.items():
    print(k, ":", v)