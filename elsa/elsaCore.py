#
# Need Capstone and 
#

import os
from capstone import *
from elftools.elf.elffile import *

class Exe:
    def __init__(self):
        self.bincode = None
        self.map_adr = None

    def load_elf(self, fn):
        if not os.path.exists(fn):
            return False
        obj = ELFFile(open(fn, "rb"))
        print(vars(obj))
        # addresse de mappage finale
        for i in obj.iter_segments():
            print(vars(i))
        if self.bincode is not None:
            return True
        return False
