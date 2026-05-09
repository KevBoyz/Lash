import psutil as ps


def getListOfProcessSortedByMemory():
    listOfProcObjects = []
    for proc in ps.process_iter():
        try:
            pinfo = proc.as_dict(attrs=['pid', 'name', 'username'])
            pinfo['vms'] = proc.memory_info().vms / (1024 * 1024)
            listOfProcObjects.append(pinfo)
        except (ps.NoSuchProcess, ps.AccessDenied, ps.ZombieProcess):
            pass
    listOfProcObjects = sorted(listOfProcObjects, key=lambda procObj: procObj['vms'], reverse=True)
    return listOfProcObjects
