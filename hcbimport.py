def all(name):
    file = open(name, "r")
    filelines = file.readlines()
    linklist = []
    proxylist = []
    proxyportlist = []
    sizelist = []
    for line in filelines:
        if line == '\n':
            break
        lineitems = line.rstrip().split(",")
        linklist.append(lineitems[0])
        proxyinfo = lineitems[1].split(":")
        proxylist.append(proxyinfo[0])
        proxyportlist.append(proxyinfo[1])
        sizelist.append(lineitems[2])

    return [linklist, proxylist, proxyportlist, sizelist]