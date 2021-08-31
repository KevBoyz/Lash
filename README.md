# About Lash

This package provides a set of desktop tools that simplify and  
automate repetitive processes. Lash also has utility functions  
that cover some needs of desktop users.

Thought to be simple and effective, Lash was developed with a  
command line interface that has self-help and semantic commands.

![image][]

## Lash overview

*Installing:* `pip install lash`  
*Executing*: `python -m lash`  
**Getting help**: `python -m lash --help`

*Please ignore all -m in **Usage line**.  

## Usage examples — $ py -m lash zip compress –help Usage: -m zip


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

------------------------------------------------------------------------

    $py -m lash sched run --help
    Usage: -m sched run [OPTIONS] command <hours> <minutes> <seconds>

    Run commands repetitively at a given interval starting from
    current moment.

    $ py -m lash sched run "py -m lash random" 0 0 2
    78311
    13918
    64280
    [...]

    Aborted!

### Lash Configurations

From version 1.1.0, **configurations** were implemented in the
package,  
which can be edited manually in */lash/Exportables/config.py*

**Thanks for ReadMe**


# Release notes

## v1.1.1 - Just a new function

* New feature: Encrypt/Decrypt files with `spy crypt` command.
* Licence error fix.

## v1.1.0 - Bug fix and upgrades

* Bug fix and upgrades in `zip compress/extract` command.
* Bug fix and upgrades in `calc prob` command
* Bug fix and upgrades in `organize` command.
* Bug fixed in `web new` command, generate default new web project.
* Implementing `configs`, additional configurations to package.
* Implementing `task-killer` command, kill chain of tasks to optimization.
* Change licence to **GNU-GPLv3**
* *Log* command renamed to `spy`
* New features for sched command:
* Support for *multi-time* options in `run` command
* * Sub-command: `exec` -> Execute a task from determined moment of day
* * Sub-command: `wait` -> Wait x time, run a task once and exit


  [image]: Images/lash_print.png



