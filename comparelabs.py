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
from difflib import SequenceMatcher

def get_file_text(filename):
    try:
        f = open(filename)
    except OSError as err:
        return ''
    else:
        try:
            return f.read()
        except:
            return ''
        finally:
            f.close()

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
                        os.rename(os.path.join(dirpath, file),
                            os.path.join(name, file))
                    else:
                        os.remove(os.path.join(dirpath, file))
                for d in dirnames:
                    os.rmdir(os.path.join(dirpath, d))
            os.rmdir(path) # TODO: Remove any leftover non-.vhd/.xdc files

# Check for .xdc files and remove them
names = os.listdir('.') # Create a list of students
for name in names:
    files = os.listdir(name)
    xdc_files = [xdc for xdc in files if xdc.endswith('.xdc')]
    if len(xdc_files) > 1:
        print(name + ' has multiple XDC files.')
    elif not xdc_files:
        print(name + ' has no XDC file.')
    for file in xdc_files:
        os.remove(os.path.join(name, file))

# Compare all students for similarity
# TODO: cut time in half by only comparing each pair once
for name1 in names:
    # Get all of name1's files
    files1 = os.listdir(name1)
    for name2 in names:
        if name2 == name1:
            continue

        # Get all of name2's files
        files2 = os.listdir(name2)

        # Calculate the average similarity over each of name1's files
        similarities = []
        for file1 in files1:
            file1_text = get_file_text(os.path.join(name1, file1))
            # Find the file that most similary matches file1
            max_similarity = 0.0;
            most_similar_file = ''
            for file2 in files2:
                file2_text = get_file_text(os.path.join(name2, file2))
                sim12 = SequenceMatcher(None, file1_text, file2_text).ratio()
                if sim12 > max_similarity:
                    max_similarity = sim12
                    most_similar_file = file2
            #if max_similarity > 0.95:
            #    print(file1 + ' is similar to ' + most_similar_file +
            #        ' to degree ' + str(max_similarity))
            similarities.append(max_similarity)
        mean = sum(similarities) / float(len(similarities))
        if mean > 0.9:
            print('Student ' + name1 + ' and ' + name2 +
                ' are similar to degree ' + str(mean))

# TODO: Verify existence of testbenches
