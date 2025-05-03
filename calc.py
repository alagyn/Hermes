import sys

sys.path.append("build/tests/Debug")

import hermes

if __name__ == "__main__":
    parser = hermes.load_calc()

    stream = hermes.load_input_file("test.txt")
    print("Stream loaded")
    out = parser.parse(stream)

    exit()

    try:
        while True:
            x = input("> ")
            stream = hermes.load_input_bytes(x.encode())
            try:
                out = parser.parse(stream)
            except RuntimeError as err:
                print(err)
            print("output", out)

    except KeyboardInterrupt:
        pass
