# Configure file, edit only the values of keys.
# Read the docstring


def config():
    """
    Configuration guide; Description of keys.

    * beep: *Beep* When finish a task
    * black_list: List of processes to be killed by _taskkiller_,
    insert the process name + extension in srt type, like: 'process.exe' or if you are in Linux: 'process'
    Be careful what you add to this list, you may receive permission errors when terminating certain processes.
    """
    return \
        {
            'beep': True,
            'black_list': ['brave.exe']
        }
