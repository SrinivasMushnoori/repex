import tarfile
import sys
import os
import glob


def untar(input_files):
    tar = tarfile.open(input_files)
    tar.extractall()
    tar.close
    os.rename(glob.glob('*.mdin')[0], 'mdin')
    os.rename(glob.glob('*.prmtop')[0], 'prmtop')
    os.rename(glob.glob('*.inpcrd')[0], 'inpcrd')


untar(sys.argv[1])
