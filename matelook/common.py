# -*- coding: utf-8 -*-

import re
from datetime import datetime


def time_date2txt(cur_time=datetime.utcnow()):
    return cur_time.strftime("%Y-%m-%dT%H:%M:%S+0000")


if __name__ == "__main__":
    print(time_date2txt())

