# About Lash
This package provides a set of desktop tools that simplify and  
automate repetitive processes. Lash also has utility functions  
that cover some needs of desktop users. 

Thought to be simple and effective, Lash was developed with a   
command line interface that has self-help and semantic commands.

## Lash overview 
_Installing:_ `pip install lash`  
_Executing_: `python -m lash`

**Getting help**: `python -m lash --help`
    
    Usage: -m [OPTIONS] COMMAND [ARGS]...

    - Lash 1.0.0 by KevBoyz ~ https://github.com/KevBoyz/Lash

    Options:
    --help  Show this message and exit.

    Commands:
    autoclick  Auto clicker
    calc       Math utilities
    keyhold    hold a keyboard key
    log        Simple loggers to rec events
    organize   Organize your files
    random     Randomize numbers
    sched      Schedule tasks at the command line level
    web        Generic Web-Tools
    zip        Zip tools

_Please ignore all `-m` in __Usage__ line_.   
## Usage examples
---
    $ py -m lash zip compress --help
    Usage: -m zip compress [OPTIONS] <path>

    Compress files in zip archive
    Options:
    -fn TEXT  Output file name
    -v        Verbose mode   [default: True]

    $ py -m lash zip compress -fn "Zip" C:\Users\Kevin\Documents
    Compacting archives, please wait...

    - - Process list - -
    Compacting: .gitattributes
    Compacting: .gitignore
    Compacting: setup.cfg
    Compacting: setup.py
    [...]
    process completed, 206 files compacted

---
    $ python -m lash sched run --help
    Usage: sched run [OPTIONS] command

    Run commands repetitively at a given interval starting from current moment.

    Options:
    -s INTEGER  Set delay seconds
    -m INTEGER  Set delay minutes
    -h INTEGER  Set delay hours

    $ python -m lash sched run -s 5 "py -m lash random"
    31139
    15368
    60600
    [...]
    Aborted!
## Final declarations
The tool is under development and will have weekly updates with corrections
and news, this project is still small and unknown by your target audience,
if you liked the work, please share it with your contacts.  

**Thanks for ReadMe**
