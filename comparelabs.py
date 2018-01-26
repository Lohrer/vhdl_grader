#!/usr/bin/env python3

# sudo -H pip3 install --upgrade pip
# sudo pip3 install pyunpack patool entrypoint2
# sudo apt install unzip unrar p7zip-full

import os
import re
from pyunpack import Archive

# TODO: Find path of lab, or pass in as arg
labdir = 'Lab1W18'

# Parse every subdirectory
for dir in os.listdir(labdir):
    # Find student's name and rename directory if necessary
    # Example start name:
    #Emma Atkinson_7511054_assignsubmission_file_
    if '_' in dir:
        name, data = dir.split('_', 1)
        os.rename(os.path.join(labdir, dir), os.path.join(labdir, name))
    else:
        name = dir

    # Unpack any zip/rar/etc files for the current student
    namepath = os.path.join(labdir, name)
    for dirpath, dirnames, filenames in os.walk(namepath):
        for f in filenames:
            if f.lower().endswith(('.zip', '.rar', '.7z')):
                zipfile = os.path.join(dirpath, f)
                Archive(zipfile).extractall(namepath)
                os.remove(zipfile)

    # Move any .vhd and .xdc files in subdirs to the student's directory
    # Delete the (now empty) subdirectories
    for f in os.listdir(namepath):
        path = os.path.join(namepath, f)
        if os.path.isdir(path):
            for dirpath, dirnames, filenames in os.walk(path, topdown=False):
                for file in filenames:
                    if file.lower().endswith(('.vhd', '.xdc')):
                        os.rename(os.path.join(dirpath, file), os.path.join(namepath, file))
                    else:
                        os.remove(os.path.join(dirpath, file))
                for d in dirnames:
                    os.rmdir(os.path.join(dirpath, d))
            os.rmdir(path)

# Create a list of students
names = os.listdir(labdir)
#for name in names:
#    print(name)

# Verify existence of testbenches and constraints files


#re.search('entity .* is.*\nend .*;', text, flags=re.IGNORECASE)


# Compare each student's files with each other's.

