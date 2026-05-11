
def get_last(path):
    if path.rfind('\\') != -1:
        last = path[1 + path.rfind('\\'):]
    else:
        last = path[1 + path.rfind('/'):]
    if '"' in last:
        last = last.replace('"', '')
    return last


def tuple_to_seconds(times):
    seconds = 0
    seconds += times[0] * 3600
    seconds += times[1] * 60
    seconds += times[2]
    return seconds
