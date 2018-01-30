#!/usr/bin/env python3

# Download the zipfile from Moodle and place it in its own directory.
# This script will extract it, delete it, and leave the results in the
# directory.

# Requirements:
# sudo -H pip3 install --upgrade pip
# sudo -H pip3 install pyunpack patool entrypoint2
# sudo apt install unzip unrar p7zip-full

import sys, os, shutil, re
from pyunpack import Archive

# Supported archive formats for extracting
archive_extensions = ('.zip', '.rar', '.7z')

# Verify the main archive exists and is a valid format,
# change to its directory if found.
if len(sys.argv) == 2:
    if not os.path.isfile(sys.argv[1]):
        raise ValueError('Archive file does not exist')
    labs_archive_path, labs_archive = os.path.split(sys.argv[1])
    if labs_archive.endswith(archive_extensions):
        if len(labs_archive_path) > 0:
            os.chdir(labs_archive_path)
    else:
        raise ValueError('Unsuported archive format')
else:
    raise ValueError('Usage: comparelabs.py archive.zip')

# Create a subdirectory to extract into, if it already exists remove it
lab_name = labs_archive.split('-')[2]
if os.path.isdir(lab_name):
    shutil.rmtree(lab_name)
os.mkdir(lab_name)

# Extract main archive and remove the archive file
Archive(labs_archive).extractall(lab_name)
#os.remove(LabsArchive)
os.chdir(lab_name)

# Parse every subdirectory (student)
for dir in os.listdir('.'):
    # Find student's name and rename directory if necessary
    # Example start name:
    #Emma Atkinson_7511054_assignsubmission_file_
    if '_' in dir:
        name = dir.split('_', 1)[0]
        os.rename(dir, name)
    else:
        name = dir

    # Unpack any zip/rar/etc files for the current student
    # TODO: Handle archives inside archives
    for dirpath, dirnames, filenames in os.walk(name):
        for file in filenames:
            if file.lower().endswith(archive_extensions):
                filepath = os.path.join(dirpath, file)
                Archive(filepath).extractall(name)
                os.remove(filepath)

    # Move any .vhd and .xdc files in subdirs to the student's directory
    # Delete the (now empty) subdirectories
    for f in os.listdir(name):
        path = os.path.join(name, f)
        if os.path.isdir(path):
            for dirpath, dirnames, filenames in os.walk(path, topdown=False):
                for file in filenames:
                    if file.lower().endswith(('.vhd', '.xdc')):
                        os.rename(os.path.join(dirpath, file), os.path.join(name, file))
                    else:
                        os.remove(os.path.join(dirpath, file))
                for d in dirnames:
                    os.rmdir(os.path.join(dirpath, d))
            os.rmdir(path)

# Create a list of students
names = os.listdir('.')
#for name in names:
#    print(name)

# Verify existence of testbenches and constraints files


#re.search('entity .* is.*\nend .*;', text, flags=re.IGNORECASE)


# Compare each student's files with each other's.

