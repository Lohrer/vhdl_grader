#!/usr/bin/env python3

# Download the zipfile from Moodle and place it in its own directory.
# This script will extract it, delete it, and leave the results in the
# directory.

# Requirements:
# sudo -H pip3 install --upgrade pip
# sudo -H pip3 install pyunpack patool entrypoint2
# sudo apt install unzip unrar p7zip-full

import sys, os, shutil, re
import itertools
import argparse
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

parser = argparse.ArgumentParser(description='Check similarities between moodle submissions')
parser.add_argument('zip_file', type=argparse.FileType(), help='zip file downloaded from moodle with all submissions')
parser.add_argument('min_diff', type=float, default=0.95, nargs='?', help='min similarity to flag')
parser.add_argument('--show_diff', action='store_true', default=False, help='show the difference between similar files')
parser.add_argument('--verbose', '-v', action='store_true', default=False, help='show debug info')
args = parser.parse_args()

# Supported archive formats for extracting
archive_extensions = ('.zip', '.rar', '.7z')

# Verify the main archive exists and is a valid format,
# change to its directory if found.
labs_archive_path, labs_archive = os.path.split(args.zip_file.name)
if labs_archive.endswith(archive_extensions):
    if len(labs_archive_path) > 0:
        os.chdir(labs_archive_path)
    else:
        raise ValueError('Unsuported archive format')

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
for pair in itertools.combinations(names, 2):
    name1, name2 = pair
    if args.verbose: print('comparing ' + name1 + ' and ' + name2)

    # Get all of the files
    files1 = os.listdir(name1)
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

        if args.verbose and max_similarity > 0.95:
            print(file1 + ' is similar to ' + most_similar_file +
                  ' to degree ' + str(max_similarity))
        similarities.append((max_similarity, file1, most_similar_file))
    simsum = 0
    for sim, f1, f2 in similarities:
        simsum += sim
    mean = simsum / float(len(similarities))
    if mean > args.min_diff:
        print('Student ' + name1 + ' and ' + name2 + ' are similar to degree ' + str(mean))
        similarities.sort(key=lambda sim: sim[0], reverse=True)
        for sim, f1, f2 in similarities:
            if sim < 0.95: break;
            print('(%f, %s, %s)' % (sim, f1, f2))
            if args.show_diff:
                cmd='diff --ignore-case --ignore-blank-lines --ignore-trailing-space --ignore-space-change "%s/%s" "%s/%s"' % (name1, f1, name2, f2)
                os.system(cmd)

# TODO: Verify existence of testbenches
