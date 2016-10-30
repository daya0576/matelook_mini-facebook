from datetime import datetime, timezone
import keys



time_eg = '2016-10-27T18:00:47+1100'


def time_date2txt(cur_time=None):
    if cur_time is None:
        cur_time = datetime.now(timezone.utc)

    cur_time_text = cur_time.strftime("%Y-%m-%dT%H:%M:%S%z")

    return cur_time_text


def time_txt2date(time_text):
    date_object = datetime.strptime(time_text, "%Y-%m-%dT%H:%M:%S%z")
    return date_object


def show_time(time):
    time_show = ''
    date_record = time_txt2date(time)
    date_now = datetime.now()

    sub_s = int(date_now.timestamp()-date_record.timestamp())

    if sub_s < 60:
        time_show = 'Just now'
    elif sub_s/60 < 60:
        time_show = '{} minutes'.format(sub_s//60)
    elif sub_s/60/60 < 24:
        hours = sub_s // 60 // 60
        time_show = '{} hrs'.format(hours) if hours != 1 else '{} hr'.format(hours)
    elif sub_s/60/60/24 >= 1:
        day = int(sub_s/60/60/24)
        if day == 1:
            time_show = 'yesterday'
        else:
            time_show = '{} days ago'.format(day)

    return time_show




TIME_ZONE = 'Australia/Sydney'


# print(time_date2txt(time_txt2date(time_eg)))
#
# print(show_time(time_eg))

print(time_date2txt())









