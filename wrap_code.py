#!/usr/bin/env python3.3

ASM_code = b"""
.file "test.c"
.text
.globl  _start
.type   _start, @function
_start:
    pushl $12
    pushl $555
    movl (%esp), %eax
    addl -4(%esp), %eax
    pushl %eax
    movl $0x8045600, %eax
    call *%eax
    hlt

.size   _start, .-_start
.ident  "GCC: (Ubuntu/Linaro 4.6.3-1ubuntu5) 4.6.3"
.section    .note.GNU-stack,"",@progbits
"""

import tempfile

f = tempfile.NamedTemporaryFile(suffix=".s", delete=False)
f.write(ASM_code)
f.close()

import subprocess
exefile = tempfile.NamedTemporaryFile(delete=False)
exefile.close()

subprocess.check_call(["gcc", "-nostartfiles", "-m32", "-o", exefile.name, f.name])

import orgasm
bincode = orgasm.LoadElf32Text(exefile.name)

reorg = orgasm.Reorganize(bincode)
reorg.doDispatch()
reorg.doOrganize()
print(reorg.getFinalAsm())
