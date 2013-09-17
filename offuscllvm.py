#!/usr/bin/env python3.3

from llvm.core import *
from llvm.ee import *
from llvm.passes import *

# PRINT AVAILABLE PASS
#for k, v in llvm.passes._dump_all_passes():
#    print("pass : %s , desc: %s" % (k, v))
for k in dir(llvm.passes):
    if "PASS_" in k:
        print(k)


# need a module
module = Module.new("offsc")

# Some type
ty_int = Type.int(32)
ty_pint = Type.pointer(ty_int)
ty_ppint = Type.pointer(ty_pint)

func_type = Type.function(Type.int(), [Type.int()])
funcadr_type = Type.pointer(Type.function(Type.void(), (), var_arg=True))

# Create a main function

main = Function.new(module, func_type, "main")

entry = main.append_basic_block("entry")
# need a builder
builder = Builder.new(entry)

funcadr_type = Type.pointer(Type.function(Type.void(), (), var_arg=True))
funcadr = builder.alloca(ty_int, "funcadr")
builder.store(Constant.int(ty_int, 1234), funcadr)
vfuncadr = builder.load(funcadr, "vfuncadr")
ptrfunc = builder.inttoptr(vfuncadr, funcadr_type, "ptrfunc")
builder.call(ptrfunc, [])

#builder.call(Constant.int(Type.int(), 56789), [])

eax = builder.alloca(Type.int(), "eax")
_eax = builder.load(eax, "_eax")
builder.store(Constant.int(ty_int, 4), eax)

p1 = builder.alloca(ty_int, "p1")
p2 = builder.alloca(ty_int, "p2")
p3 = builder.alloca(ty_int, "p3")
p4 = builder.alloca(ty_int, "p4")
p5 = builder.alloca(ty_int, "p5")

total = builder.alloca(ty_int, "total")
builder.store(Constant.int(ty_int, 0), total)
vtotal = builder.load(total, "vtotal")

intp1 = builder.ptrtoint(p1, ty_int, "intp1")
# 0
p1int = builder.inttoptr(intp1, ty_pint, "p1int")
builder.store(Constant.int(ty_int, 1), p1int)
vp1int = builder.load(p1int, "vp1int")
vtotal = builder.add(vtotal, vp1int, "vtotal")
builder.store(vtotal, p1int)

intp1 = builder.sub(intp1, Constant.int(ty_int, 8), "intp1")
# 1
p1int = builder.inttoptr(intp1, ty_pint, "p1int")
builder.store(Constant.int(ty_int, 2), p1int)
vp1int = builder.load(p1int, "vp1int")
vtotal = builder.add(vtotal, vp1int, "vtotal")
builder.store(vtotal, p1int)

intp1 = builder.sub(intp1, Constant.int(ty_int, 8), "intp1")
# 2
p1int = builder.inttoptr(intp1, ty_pint, "p1int")
builder.store(Constant.int(ty_int, 3), p1int)
vp1int = builder.load(p1int, "vp1int")
vtotal = builder.add(vtotal, vp1int, "vtotal")
builder.store(vtotal, p1int)

builder.store(vtotal, total)

builder.ret(vtotal)

# is the function correct
main.verify()

print("STUPID LLVM CODE")
print(module)

# pass manager
pass_man = FunctionPassManager.new(module)
#pass_man.add(PASS_MEM2REG)
# Reassociate expressions.
#pass_man.add(PASS_REASSOCIATE)
# Eliminate Common SubExpressions.
#pass_man.add(PASS_GVN)
# Simplify the control flow graph (deleting unreachable blocks, etc).
#pass_man.add(PASS_DCE)
#pass_man.add(PASS_DA)
#pass_man.add(PASS_MEMDEP)
#pass_man.add(PASS_CONSTPROP)
pass_man.add(PASS_INSTCOMBINE)

# finish init pass_man
pass_man.initialize()


# optimize block
pass_man.run(main)

print("OPTIMIZED CODE")
print(module)

# For intel syntax
import sys, os
os.environ['LLVMPY_OPTIONS'] = "-x86-asm-syntax=intel"
parse_environment_options(sys.argv[0], "LLVMPY_OPTIONS")

### change Target
# For 32 bit
tm = TargetMachine.lookup(arch="x86", cpu="i386")

# For 64 bit
#tm = TargetMachine.lookup(arch="x86-64", cpu="x86-64")


txtasm = tm.emit_assembly(module)
print("OUTPUT ASM INTEL:")
print(txtasm)

