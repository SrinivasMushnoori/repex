import tarfile
import sys
def untar(Input_Files):
    tar = tarfile.open(Input_Files)
    tar.extractall()
    tar.close

untar(sys.argv[1])
