# Lash,  the py-package ![](Images/desktop.png)![](Images/lash_gif.gif)

This package provides a set of desktop tools that simplify and automate repetitive  
processes. Lash also has utility functions that cover some needs of desktop users.

Thinking about being simple and effective, Lash was developed with a command   
line interface, having syntax similar to cli's linux, with options args and help sections.

![image][]

Access [KevBoyz-Docs/lash](https://kevboyz.github.io/KevBoyz-Docs/sub-pages/documentations/lash/index.html) for the full documentation. 

## Lash overview

*Installing:* `pip install lash`  
*Executing*: `python -m lash`

## Compress file in zip archive

    $ py -m lash zip compress C:\Users\User\Documents
    Compacting archives, please wait...

    - - Process list - -
    Compacting: .gitattributes
    Compacting: .gitignore
    Compacting: setup.cfg
    Compacting: setup.py
    [...]
    process completed, 206 files compacted


# Scheduling commands execution

    $ py -m lash sched run --help
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
package, which can be edited manually in */lash/Exportables/config.py*  
You can get the config.py path with `lash getconfig` command

**Thanks for ReadMe**


# Release notes

## v1.2.0 - General Upgrade

* 

## v1.1.3.1 - Readme from Pypi page

* Rst text added to Pipy page

## v1.1.3 - Bug fix

* Auto-help text sections updated
* web new command now create the template files using the code declared as string at config.py
* New command: getconfig See the config file path
* beep.waw and web_pkg.zip removed from package
* Error .zip.zip fixed in zip extract command
* Licence classifier added to setup.py
* Brave.exe removed from config file
* -o Option added to autoclick, do a only single

## v1.1.2 - Bug fix

* Function autoclick fixed

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



