import sys

sys.path.append("build/tests/Debug")

import hermes_calc as hermes

if __name__ == "__main__":
    parser = hermes.load_calc()

    with open("test.txt", mode='rb') as f:

        out = parser.parse(f)
        print(out)

    # stream = hermes.load_input_file("test.txt")
    # print("Stream loaded")
    # out = parser.parse(stream)
    # exit()

    try:
        while True:
            x = input("> ")
            # stream = hermes.load_input_bytes(x.encode())
            try:
                out = parser.parse(x.encode())
            except RuntimeError as err:
                print(err)
            print("output", out)

    except KeyboardInterrupt:
        pass
