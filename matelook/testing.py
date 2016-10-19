# -*- coding: utf-8 -*-

import re

def add_zid_link(text):
    print(text)
    zids = re.findall(r'z[0-9]{7}', text)
    print(zids)


if __name__ == "__main__":
    text = "z5101274 z5115045 z5083924"
    add_zid_link(text)