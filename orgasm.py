
import distorm3

from distorm3 import Decode16Bits, Decode32Bits, Decode64Bits
from ctypes import *
from construct.formats.executable.elf32 import *

def DecodeOne(codeOffset, code, dt, instidx=0):
    """
    inspired from DecodeGenerator but decode only one instruction for made easier the
    recursive descent BasicBlock identification
    """
    # basic control
    if not code:
        return
    if not codeOffset:
        codeOffset = 0
    if dt not in (distorm3.Decode16Bits, distorm3.Decode32Bits, distorm3.Decode64Bits):
        raise ValueError("Invalid decode type value: %r" % (dt,))
    # not usable
    codeLen = len(code)
    # 
    code_buf = create_string_buffer(code)
    # ptet ajout idx
    p_code = byref(code_buf, instidx)
    result = (distorm3._DecodedInst * distorm3.MAX_INSTRUCTIONS)()
    #print("RESULT %s" % result)
    p_result = byref(result)
    instruction_off = 0
    #
    while codeLen > 0:
        usedInstructionsCount = c_uint(0)
        status = distorm3.internal_decode(distorm3._OffsetType(codeOffset), p_code, codeLen, dt, p_result, distorm3.MAX_INSTRUCTIONS, byref(usedInstructionsCount))
        if status == distorm3.DECRES_INPUTERR:
            raise ValueError("Invalid arguments passed to distorm_decode()")
        used = usedInstructionsCount.value
        #print("USED: %s" % used)
        if not used:
            break
        #for index in xrange(used):
        for index in range(used):
            di = result[index]
            print("DI : %r" % di)
            asm = di.mnemonic.p.decode("ascii")
            if len(di.operands.p):
                asm += " " + di.operands.p.decode("ascii")
            pydi = (di.offset, di.size, asm, di.instructionHex.p.decode("ascii"))
            instruction_off += di.size
            return pydi

def LoadElf32Text(fn):
    obj = elf32_file.parse_stream(open(fn, "rb"))
    # addresse de mappage finale
    map_adr = 0
    bincode = None
    for section in obj.sections:
        if section.name == b'.text':
            map_adr = section.addr
            bincode = section.data.read()
    return bincode

from llvm.core import *
from llvm.ee import *
from llvm.passes import *
import re

class   Reorganize:

    def __init__(self, bincode):
        self.bincode = bincode
        # need a module
        self.module = Module.new("reorg")
        func_type = Type.function(Type.void(), [])
        self.main = Function.new(self.module, func_type, "main")
        self.entry = self.main.append_basic_block("entry")
        # need a builder
        self.builder = Builder.new(self.entry)
        self.instlist = [
            re.compile("PUSH (?P<type>DWORD)? 0x[a-fA-F0-9]+"),
        ]

    def doDispatch(self):
        """
    pushl $12
    pushl $555
    movl 8(%esp), %eax
    addl 4(%esp), %eax
    add 8, %esp
    pushl %eax
    movl $0x8045600, %eax
    call *%eax
        """
        # decode inst flow
        map_adr = 0
        idx = 0
        while True:
            one_inst = DecodeOne(map_adr, self.bincode, Decode32Bits, idx)
            print("%05X : % 16s\t\t%s" % (one_inst[0], one_inst[3], one_inst[2]))
            size_inst = one_inst[1]
            map_adr += size_inst
            idx += size_inst

            if one_inst[2] == "HLT":
                break

        ti = Type.int()
        pti = Type.pointer(Type.int())

        # build sp
        sp = self.builder.alloca(ti, "sp")
        sp2 = self.builder.alloca(ti, "sp2")
        sp3 = self.builder.alloca(ti, "sp3")

# PUSH
        # DEC SP
        isp = self.builder.ptrtoint(sp, ti, "isp")
        isp = self.builder.sub(isp, Constant.int(ti, 4), "isp")
        sp = self.builder.inttoptr(isp, pti, "sp")
        # STORE
        self.builder.store(Constant.int(ti, 12), sp)

# PUSH
        # DEC SP
        isp = self.builder.ptrtoint(sp, ti, "isp")
        isp = self.builder.sub(isp, Constant.int(ti, 4), "isp")
        sp = self.builder.inttoptr(isp, pti, "sp")
        # STORE
        self.builder.store(Constant.int(ti, 555), sp)

# MOV
        # EAX
        eax = self.builder.alloca(ti, "eax")
        # 8(%esp) -> EAX
        isp = self.builder.ptrtoint(sp, ti, "isp")
        isp = self.builder.add(isp, Constant.int(ti, 8), "isp")
        tmp = self.builder.inttoptr(isp, pti, "tmp")
        tmp = self.builder.load(sp, "tmp")
        self.builder.store(tmp, eax)

# ADD
        # 4(%esp)
        isp = self.builder.ptrtoint(sp, ti, "isp")
        isp = self.builder.add(isp, Constant.int(ti, 4), "isp")
        tmp = self.builder.inttoptr(isp, pti, "tmp")
        # + EAX
        vtmp = self.builder.load(tmp)
        _eax = self.builder.load(eax)
        _eax = self.builder.add(vtmp, _eax, "eax")

# ADD SP
        isp = self.builder.ptrtoint(sp, ti, "isp")
        isp = self.builder.add(isp, Constant.int(ti, 4), "isp")
        sp = self.builder.inttoptr(isp, pti, "sp")

# PUSH
        # DEC SP
        isp = self.builder.ptrtoint(sp, ti, "isp")
        isp = self.builder.sub(isp, Constant.int(ti, 4), "isp")
        sp = self.builder.inttoptr(isp, pti, "sp")
        # STORE
        self.builder.store(_eax, sp)

# MOV
        self.builder.store(Constant.int(ti, 0x8045600), eax)

# CALL
        funcadr_type = Type.pointer(Type.function(Type.void(), (), var_arg=True))
        _eax = self.builder.load(eax, "_eax")
        ptrfunc = self.builder.inttoptr(_eax, funcadr_type, "ptrfunc")
        self.builder.call(ptrfunc, [])


        self.builder.ret_void()
        print(self.module)

    def doOrganize(self):
        pass_man = FunctionPassManager.new(self.module)
        pass_man.add(PASS_MEM2REG)
        pass_man.add(PASS_REG2MEM)
        # Reassociate expressions.
        pass_man.add(PASS_REASSOCIATE)
        # Eliminate Common SubExpressions.
        pass_man.add(PASS_GVN)
        # Simplify the control flow graph (deleting unreachable blocks, etc).
        pass_man.add(PASS_DCE)
        pass_man.add(PASS_DA)
        pass_man.add(PASS_MEMDEP)
        pass_man.add(PASS_CONSTPROP)
        pass_man.add(PASS_INSTCOMBINE)
        # finish init pass_man
        pass_man.initialize()
        # optimize block
        pass_man.run(self.main)

    def getFinalAsm(self):
        # For intel syntax
        import sys, os
        os.environ['LLVMPY_OPTIONS'] = "-x86-asm-syntax=intel"
        parse_environment_options(sys.argv[0], "LLVMPY_OPTIONS")
        # For 32 bit
        tm = TargetMachine.lookup(arch="x86", cpu="i386")
        return tm.emit_assembly(self.module)
