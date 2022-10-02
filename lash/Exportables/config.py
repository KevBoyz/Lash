def config():
    """
    Configuration guide; Description of keys.

    * black_list: List of processes to be killed by _taskkiller_,
     - insert the process name + extension in srt type, like: 'process.exe' or if you are in Linux: 'process'
     - Be careful what you add to this list, you may receive permission errors when terminating certain processes.
    * html, css and js code: The default code that the files of _web new_ command will have.
    """
    return \
        {
            'black_list': []
        }
