from functools import partial


class LineNumberProgram:

    def __init__(self, image) -> None:
        single_byte = partial(image.read, 1)
        while True:
            opcode = single_byte()
            if not opcode:
                break
            # print(ord(opcode), end=" ")
        print()
