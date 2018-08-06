import datetime


def log(message):
    global logfile
    text = '{0} {1}'.format(now(),message)
    print(text)
    with open('data/debug.log', 'a') as f:
        f.write(text + '\n')



def now():
    return '{0:%Y/%m/%d %H:%M:%S}'.format(datetime.datetime.now())