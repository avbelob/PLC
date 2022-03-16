import math

commands = {"ADD": 0x01,
            "SUB": 0x02,
            "MOV": 0x04,
            "MOVVAL": 0x05,
            "PRINT": 0x06,
            "READ": 0x07,
            "PRINTSTR": 0x08,
            "JUMP": 0x09,
            "JUMPZ": 0x0A,
            "PUSH": 0x0B,
            "POP": 0x0C,
            "TOP": 0x0D,
            "FBEGIN": 0x0E,
            "FEND": 0x0F,
            "CALL": 0x10,
            "STOP": 0xFF
            }

inv_commands = {v: k for k, v in commands.items()}

reg_count = 10
base = 16
memory = 256


def num_to_hex(val):
    if val == 0:
        return ['00', '00', '00', '00']

    len = math.floor(math.log(val, base)) + 1
    hex_val = '0' * (8 - len) + str(hex(val))[2:]
    return [hex_val[i - 2:i] for i in range(2, 10, 2)]


def str_to_hex(str_val):
    hex_val = ''
    for c in str_val:
        len = math.floor(math.log(ord(c), base)) + 1
        cur_hex_val = '0' * (4 - len) + str(hex(ord(c)))[2:]
        hex_val += cur_hex_val[:2] + ' ' + cur_hex_val[2:] + ' '
    return hex_val


class VirtualMachine:
    def __init__(self, filename):
        self.program = []
        with open(filename) as f:
            for line in f.readlines():
                self.program.append(line.split())

        self.instruction_pointer = int(''.join(self.program[0]), base)
        self.stack_len = int(''.join(self.program[1]), 16)
        self.stack_pointer = base + 2

        self.commands_func = {0x01: self.add,
                              0x02: self.sub,
                              0x04: self.mov,
                              0x05: self.movval,
                              0x06: self.print,
                              0x07: self.read,
                              0x08: self.printstr,
                              0x09: self.jump,
                              0x0A: self.jumpz,
                              0x0B: self.push,
                              0x0C: self.pop,
                              0x0D: self.top,
                              0x0F: self.fend,
                              0x10: self.call,
                              0xFF: self.stop
                              }

    def run(self):
        while self.instruction_pointer:
            self.commands_func[int(self.program[self.instruction_pointer][0], base)]()

    def _get_regs(self, regs_count):
        regs = []
        for i in range(regs_count):
            regs.append(int(self.program[self.instruction_pointer][i + 1], base))

        if len(regs) == 1:
            return regs[0]

        return regs

    def _get_val(self, reg):
        return int(''.join(self.program[reg]), base)

    def add(self):
        r1, r2 = self._get_regs(regs_count=2)

        val1 = self._get_val(r1)
        val2 = self._get_val(r2)

        self.program[r1] = num_to_hex(val1 + val2)
        self.instruction_pointer += 1

    def sub(self):
        r1, r2 = self._get_regs(regs_count=2)

        val1 = self._get_val(r1)
        val2 = self._get_val(r2)

        self.program[r1] = num_to_hex(val1 - val2)
        self.instruction_pointer += 1

    def mov(self):
        r1, r2 = self._get_regs(regs_count=2)

        self.program[r1] = self.program[r2]
        self.instruction_pointer += 1

    def movval(self):
        r = self._get_regs(regs_count=1)
        self.program[r] = self.program[self.instruction_pointer][3:]
        self.instruction_pointer += 1

    def print(self):
        r = self._get_regs(regs_count=1)
        print(self._get_val(r))
        self.instruction_pointer += 1

    def read(self):
        r = self._get_regs(regs_count=1)
        self.program[r] = num_to_hex(int(input()))
        self.instruction_pointer += 1

    def printstr(self):
        r = int(''.join(self.program[self.instruction_pointer][3:]), 16)

        text = [chr(int(''.join(self.program[r][i:i + 2]), 16)) for i in
                range(0, len(self.program[r]), 2)]
        print(''.join(text))
        self.instruction_pointer += 1

    def jump(self):
        self.instruction_pointer = int(''.join(self.program[self.instruction_pointer][3:]), 16)

    def jumpz(self):
        r = self._get_regs(regs_count=1)
        val = self._get_val(r)
        if val == 0:
            self.instruction_pointer = int(''.join(self.program[self.instruction_pointer][3:]), 16)
        else:
            self.instruction_pointer += 1

    def push(self):
        r = self._get_regs(regs_count=1)
        self.program[self.stack_pointer] = self.program[r]
        self.stack_pointer += 1
        self.instruction_pointer += 1

    def pop(self):
        reg1 = self._get_regs(regs_count=1)
        self.stack_pointer -= 1
        self.program[reg1] = self.program[self.stack_pointer]
        self.instruction_pointer += 1

    def top(self):
        reg1 = self._get_regs(regs_count=1)
        self.program[reg1] = self.program[self.stack_pointer]
        self.instruction_pointer += 1

    def call(self):
        self.program[self.stack_pointer] = num_to_hex(self.instruction_pointer)
        self.stack_pointer += 1
        self.instruction_pointer = int(''.join(self.program[self.instruction_pointer][3:]), 16)

    def fend(self):
        self.stack_pointer -= 1
        self.instruction_pointer = int(''.join(self.program[self.stack_pointer]), 16) + 1

    def stop(self):
        self.instruction_pointer = None


class Assembler:
    def __init__(self, filename, bin_file):
        self.program_text = []
        with open(filename, encoding="utf-8") as f:
            for line in f.readlines():
                self.program_text.append(line.strip())

        self.key_words = ["VARS", "START", "FUNC"]
        self.parse_functions = {"ADD": self._parse_two_regs,
                                "SUB": self._parse_two_regs,
                                "MOV": self._parse_two_regs,
                                "MOVVAL": self._parse_reg_and_val,
                                "PRINT": self._parse_one_reg,
                                "READ": self._parse_one_reg,
                                "PRINTSTR": self._parse_str_val,
                                "JUMP": self._parse_jump,
                                "JUMPZ": self._parse_jumpz,
                                "PUSH": self._parse_one_reg,
                                "POP": self._parse_one_reg,
                                "TOP": self._parse_one_reg,
                                "CALL": self._parse_func_code,
                                "STOP": self._parse_stop
                                }

        self.regs = {'r' + str(i): i for i in range(memory)}
        self.program = [' '.join(num_to_hex(0))] * memory
        self.vars = self.get_string_vars()
        self.functions = {}
        self.jump_positions = {}
        self.jumps = {}
        self.get_functions()

        ip = len(self.program) + 1
        self.program = [' '.join(num_to_hex(ip))] + self.program

        self.run()

        with open(bin_file, 'w', encoding="utf-8") as f:
            f.write('\n'.join(self.program))

    def get_string_vars(self):
        vars = {}
        vars_count = 0
        if self.key_words[0] in self.program_text:
            line = self.program_text.index(self.key_words[0]) + 1
            while line != len(self.program_text) and self.program_text[line] not in self.key_words:
                var = self.program_text[line].split("\"")
                self.program.append(str_to_hex(var[1]))
                vars[var[0][:-1]] = vars_count + 1
                vars_count += 1
                line += 1

        return vars

    def get_functions(self):
        if self.key_words[2] in self.program_text:
            line = self.program_text.index(self.key_words[2]) + 1

            while line < len(self.program_text) and self.program_text[line] not in self.key_words:
                command = self.program_text[line].split()
                if command[0] == "FBEGIN":
                    self.functions[command[1]] = len(self.program) + 1
                    self.jumps = {}
                    line += 1
                    while self.program_text[line] != "FEND":
                        command = self.program_text[line].split()
                        if command[0] in self.parse_functions:
                            self.parse_functions[command[0]](command)
                        else:
                            self.jump_positions[command[0]] = len(self.program) + 1
                        line += 1
                    self.program.append('0f 00 00 00')
                    for line, label in self.jumps.items():
                        self.program[line - 1] += ' '.join(num_to_hex(self.jump_positions[label]))
                else:
                    line += 1

    def run(self):
        line = self.program_text.index(self.key_words[1]) + 1
        self.jumps = {}
        while line != len(self.program_text) and self.program_text[line] not in self.key_words:
            command = self.program_text[line].split()
            if command[0] in self.parse_functions:
                self.parse_functions[command[0]](command)
            else:
                self.jump_positions[command[0]] = len(self.program)
            line += 1
        for line, label in self.jumps.items():
            self.program[line - 1] += ' '.join(num_to_hex(self.jump_positions[label]))

    def _get_regs_code(self, command, regs_count):
        return ' '.join([num_to_hex(self.regs[command[i]])[3] for i in range(1, regs_count + 1)])

    def _parse_one_reg(self, command):
        command_code = num_to_hex(commands[command[0]])[3]
        reg_code = self._get_regs_code(command, regs_count=1)
        self.program.append(command_code + " " + reg_code + ' 00 00')

    def _parse_two_regs(self, command):
        command_code = num_to_hex(commands[command[0]])[3]
        regs_code = self._get_regs_code(command, regs_count=2)
        self.program.append(command_code + " " + regs_code + ' 00')

    def _parse_reg_and_val(self, command):
        command_code = num_to_hex(commands[command[0]])[3]
        reg_code = self._get_regs_code(command, regs_count=1)
        val_code = ' '.join(num_to_hex(int(command[2])))
        self.program.append(command_code + " " + reg_code + " 00 " + val_code)

    def _parse_str_val(self, command):
        command_code = num_to_hex(commands[command[0]])[3]
        str_val = ' '.join(num_to_hex(self.vars[command[1]] + memory))
        self.program.append(command_code + " 00 00 " + str_val)

    def _parse_func_code(self, command):
        command_code = num_to_hex(commands[command[0]])[3]
        func_code = ' '.join(num_to_hex(self.functions[command[1]]))
        self.program.append(command_code + " 00 00 " + func_code)

    def _parse_jump(self, command):
        command_code = num_to_hex(commands[command[0]])[3]
        self.program.append(command_code + " 00 00 ")
        self.jumps[len(self.program)] = command[1]

    def _parse_jumpz(self, command):
        command_code = num_to_hex(commands[command[0]])[3]
        reg_code = self._get_regs_code(command, regs_count=1)
        self.program.append(command_code + " " + reg_code + " 00 ")
        self.jumps[len(self.program)] = command[2]

    def _parse_stop(self, command):
        self.program.append('ff 00 00 00')
