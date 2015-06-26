__author__ = 'shirin'


def byte_to_hex(byte_str):
    return ''.join(["%02x" % ord(i) for i in byte_str]).strip()


def hex_to_byte(hex_str):
    res = []
    hex_str = ''.join(hex_str.split(' '))
    for i in range(0, len(hex_str), 2):
        res.append(chr(int(hex_str[i:i+2], 16)))
    return ''.join(res)


def zero_encode(inputbuf):
    res = ""
    zero = False
    zero_count = 0
    for c in inputbuf:
        if c is not '\0':
            if zero_count is not 0:
                res += chr(zero_count)
                zero_count = 0
                zero = False
            res += c
        else:
            if zero is False:
                res += c
                zero = True
            zero_count += 1

    if zero_count is not 0:
        res += chr(zero_count)
    return res


def zero_decode(inputbuf):
    res = ""
    in_zero = False
    for c in inputbuf:
        if c is not '\0':
            if in_zero is True:
                zero_count = ord(c)
                zero_count -= 1
                while zero_count > 0:
                    res += '\0'
                    zero_count -= 1
                in_zero = False
            else:
                res += c
        else:
            res += c
            in_zero = True
    return res


def zero_decode_id(inputbuf):
    res = ""
    in_zero = False
    for c in inputbuf:
        if c is not '\0':
            if in_zero is True:
                zero_count = ord(c)
                zero_count -= 1
                while zero_count > 0:
                    res += '\0'
                    zero_count -= 1
                in_zero = False
            else:
                res += c
        else:
            res += c
            in_zero = True
    return res[:4]


if __name__ == "__main__":
    print zero_encode(byte_to_hex(hex_to_byte(zero_decode("fa74a"))))
    # print zero_decode(zero_encode("sal\0am\0"))
    # print zero_encode("sal\0am")
