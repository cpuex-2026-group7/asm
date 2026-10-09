import sys
import re

# ======== ISA ========
isa = [
    # ALU / NONE
    {"opcode": "0000000", "expr": "halt"},
    {"opcode": "0001100", "expr": "beq rs1, rs2, imm"},
    {"opcode": "0001101", "expr": "bne rs1, rs2, imm"},
    {"opcode": "0001110", "expr": "blt rs1, rs2, imm"},
    {"opcode": "0001111", "expr": "bge rs1, rs2, imm"},
    # ALU / WI
    {"opcode": "0010100", "expr": "jal rd, imm"},
    {"opcode": "0011000", "expr": "jalr rd, rs1, imm"},
    {"opcode": "0011001", "expr": "addi rd, rs1, imm"},
    {"opcode": "0011010", "expr": "lw rd, imm(rs1)"},
    {"opcode": "0011100", "expr": "add rd, rs1, rs2"},
    {"opcode": "0011101", "expr": "sub rd, rs1, rs2"},
    # ALU / WF
    {"opcode": "0101000", "expr": "flw rdf, imm(rs1)"},
    # ALU / MEM
    {"opcode": "0111100", "expr": "sw rs2, imm(rs1)"},
    {"opcode": "0111101", "expr": "fsw rs2f, imm(rs1)"},
    # FPU / WI
    {"opcode": "1011000", "expr": "fcvt.w.s rd, rs1f"},
    {"opcode": "1011100", "expr": "feq.s rd, rs1f, rs2f"},
    {"opcode": "1011101", "expr": "flt.s rd, rs1f, rs2f"},
    # FPU / WF
    {"opcode": "1100000", "expr": "fli.s rdf, imm"},
    {"opcode": "1100100", "expr": "flim.s rdf, imm"},
    {"opcode": "1101000", "expr": "fcvt.s.w rdf, rs1"},
    {"opcode": "1101001", "expr": "fsqrt.s rdf, rs1f"},
    {"opcode": "1101010", "expr": "fneg.s rdf, rs1f"},
    {"opcode": "1101011", "expr": "fabs.s rdf, rs1f"},
    {"opcode": "1101100", "expr": "fadd.s rdf, rs1f, rs2f"},
    {"opcode": "1101101", "expr": "fsub.s rdf, rs1f, rs2f"},
    {"opcode": "1101110", "expr": "fmul.s rdf, rs1f, rs2f"},
    {"opcode": "1101111", "expr": "fdiv.s rdf, rs1f, rs2f"},
]
imm_pc_relative = ["beq", "bne", "blt", "bge", "jal"]

# ======= MAIN ========
def main():
    # parse arg
    if (len(sys.argv) < 2):
        print(f"usage: {sys.argv[0]} asm.py <src> [dst]")
        sys.exit(1)
    src = sys.argv[1]
    dst = "" if len(sys.argv) < 3 else sys.argv[2]
    if dst == "":
        sp = src.rsplit("/", 1)
        name = sp[-1].rsplit(".", 1)[0]
        dst = f"{sp[0]}/{name}.bin" if len(sp) > 1 else f"{name}.bin"
    # build isa meta
    print("analzing isa...")
    isa_meta = {}
    for op in isa:
        # analyze expr
        opcode = op["opcode"]
        expr = op["expr"]
        expr = re.sub(r"imm\(([a-zA-Z0-9]+)\)", r"imm, \1", expr) # imm(x) -> imm, x
        sp = expr.split(" ", 1)
        opname = sp[0]
        args = [] if len(sp) == 1 else sp[1].split(",")
        arg_types = [("imm" if arg.strip() == "imm" else ("regf" if arg.strip().endswith("f") else "regx")) for arg in args] # regx, regf, imm
        args = [arg.strip().rstrip("f") for arg in args] # rd, rs1, rs2, imm
        isa_meta[opname] = {"opcode": opcode, "args": args, "arg_types": arg_types, "imm": opcode[3:5]} # e.g. args = ["rd", "rs1", "rs2", "imm"], arg_types = ["regx", "regx", "regx", "imm"], imm = "01"
    
    # read asm
    labels = {}
    instructions = [] # index is addr
    print("reading asm...")
    with open(src, "r") as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            line = line.split("#", 1)[0].split("//", 1)[0].split(";", 1)[0].strip()
            if line == "": # empty line
                continue
            if ":" in line: # label
                label, a = line.split(":", 1)
                if a.strip() != "":
                    print(f"error: line ({i+1}): invalid text after label: {line.strip()}")
                    sys.exit(1)
                elif label.strip() in labels:
                    print(f"error: line ({i+1}): duplicated label ({label.strip()})")
                    sys.exit(1)
                labels[label.strip()] = len(instructions)
            else: # inst
                inst = re.sub(r"([^\s,]+)\s*\(([a-zA-Z0-9]+)\)", r"\1, \2", line) # imm(x) -> imm, x
                sp = inst.split(" ", 1)
                opname = sp[0]
                args = [] if len(sp) == 1 else sp[1].split(",")
                if opname not in isa_meta:
                    print(f"error: line ({i+1}): invalid opname: {opname}")
                    sys.exit(1)
                if len(args) != len(isa_meta[opname]["arg_types"]): # check arg num
                    print(f"error: line ({i+1}): invalid number of args for {opname}: {'' if len(sp) < 2 else sp[1]} (should be {len(isa_meta[opname]['args'])})")
                    sys.exit(1)
                parsed_args = {}
                for j, arg in enumerate(args): # check arg type
                    arg = arg.strip()
                    if re.match(r"x[0-9]+", arg): # regx
                        if isa_meta[opname]["arg_types"][j] != "regx":
                            print(f"error: line ({i+1}): invalid arg type for {opname}: {arg} (should be {isa_meta[opname]['arg_types'][j]})")
                            sys.exit(1)
                        parsed_args[isa_meta[opname]["args"][j]] = int(arg.replace("x", ""))
                    elif re.match(r"f[0-9]+", arg): # regf
                        if isa_meta[opname]["arg_types"][j] != "regf":
                            print(f"error: line ({i+1}): invalid arg type for {opname}: {arg} (should be {isa_meta[opname]['arg_types'][j]})")
                            sys.exit(1)
                        parsed_args[isa_meta[opname]["args"][j]] = int(arg.replace("f", ""))
                    elif re.match(r"\-?0x[0-9a-fA-F]+", arg): # imm (base16)
                        if isa_meta[opname]["arg_types"][j] != "imm":
                            print(f"error: line ({i+1}): invalid arg type for {opname}: {arg} (should be {isa_meta[opname]['arg_types'][j]})")
                            sys.exit(1)
                        parsed_args[isa_meta[opname]["args"][j]] = int(arg, 16)
                    elif re.match(r"\-?[0-9]+", arg): # imm (base10)
                        if isa_meta[opname]["arg_types"][j] != "imm":
                            print(f"error: line ({i+1}): invalid arg type for {opname}: {arg} (should be {isa_meta[opname]['arg_types'][j]})")
                            sys.exit(1)
                        parsed_args[isa_meta[opname]["args"][j]] = int(arg)
                    else: # label
                        if isa_meta[opname]["arg_types"][j] != "imm":
                            print(f"error: line ({i+1}): invalid arg type for {opname}: {arg} (should be {isa_meta[opname]['arg_types'][j]})")
                            sys.exit(1)
                        parsed_args[isa_meta[opname]["args"][j]] = arg
                instructions.append({"opname": opname, "args": parsed_args}) # e.g. args = {rd: 12, rs1: 2, rs2: 2 , imm: 550}
    
    # output
    with open(dst, "wb") as f:
        for i, inst in enumerate(instructions):
            opname = inst["opname"]
            args = inst["args"]
            opcode = isa_meta[opname]["opcode"]
            imm_type = isa_meta[opname]["imm"]
            
            rd = format(args["rd"], "05b") if "rd" in args else "00000"
            rs1 = format(args["rs1"], "05b") if "rs1" in args else "00000"
            rs2 = format(args["rs2"], "05b") if "rs2" in args else "00000"
            raw = f"{opcode}{rd}{rs1}{rs2}{'0' * 10}"
            
            if "imm" in args and isinstance(args["imm"], str): # resolve label
                if args["imm"] not in labels:
                    print(f"error: undefined label: {args['imm']}")
                    sys.exit(1)
                args["imm"] = labels[args["imm"]] - i if opname in imm_pc_relative else labels[args["imm"]]
            
            if "imm" in args:
                if imm_type == "00" or imm_type == "01": # [19:0]
                    raw = raw[:12] + format(args["imm"] & 0xFFFFF, "020b")
                elif imm_type == "10": # [14:0]
                    raw = raw[:17] + format(args["imm"] & 0x7FFF, "015b")
                elif imm_type == "11": # [24:20] [9:0]
                    r = format(args["imm"] & 0x7FFF, "015b")
                    raw = raw[:7] + r[0:5] + raw[12:22] + r[5:15]
                
            f.write(int(raw, 2).to_bytes(4, byteorder="big"))
    print(f"successfully assembled {src} to {dst}")
    

if "__main__" == __name__:
    main()