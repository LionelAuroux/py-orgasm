#!/usr/bin/env python3.3

#
#  SAMPLE OF DISTORM3 & CONSTRUCT
#

import sys
import orgasm

if len(sys.argv) != 2:
    print("Usage: %s exec_file" % sys.argv[0])
    exit(42)

print("READ %s" % sys.argv[1])
bincode = orgasm.LoadElf32Text(sys.argv[1])


# decode inst flow
map_adr = 0
idx = 0
while True:
    one_inst = orgasm.DecodeOne(map_adr, bincode, orgasm.Decode32Bits, idx)
    print("%05X : % 16s\t\t%s" % (one_inst[0], one_inst[3], one_inst[2]))
    size_inst = one_inst[1]
    map_adr += size_inst
    idx += size_inst
    #if one_inst[2] == "HLT":
    if idx >= len(bincode):
        print("FIN")
        break
