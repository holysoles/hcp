

def all(name, linklist, proxylist, sizelist):
    file = open(name, "w")
    for i in range(len(linklist)):
        file.write("%s,%s,%s\r\n" % (linklist[i], proxylist[i], sizelist[i]))
    file.close()
