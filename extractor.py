#!/usr/bin/env python3

import os
import re
import shutil
from pyunpack import Archive

# Supported archive formats for extracting
archive_extensions = ('.zip', '.rar', '.7z')

# Comment characters for filetypes
comment_chars = {'.vhd': '--', '.xdc': '#'}


# Read file and strip comments and blank lines
def read_code_file(filepath):
    try:
        f = open(filepath)
    except OSError:
        print('Error opening file ' + filepath)
        return ''
    else:
        try:
            # Read text while filtering out comments
            filename, extension = os.path.splitext(filepath)
            comment_char = comment_chars[extension]
            text = ''
            for line in f:
                line = line.partition(comment_char)[0]
                line = line.strip()
                if len(line) > 0:
                    text += line + '\n'
            return text
        except:
            print('Error reading file ' + filepath)
            return ''
        finally:
            f.close()


def parse_moodle_submissions(zip_file):
    # Verify the main archive exists and is a valid format,
    # change to its directory if found.
    labs_archive_path, labs_archive = os.path.split(zip_file)
    if labs_archive.endswith(archive_extensions):
        if len(labs_archive_path) > 0:
            os.chdir(labs_archive_path)
    else:
        raise ValueError('Unsuported archive format')

    # Create a subdirectory to extract into, if it already exists remove it
    matches = re.search('lab ?[0-9]+', labs_archive, re.I)
    if matches:
        lab_name = matches.group(0)
    else:
        lab_name = 'lab'
        print('Warning: Archive name does not include "lab #", using name "lab"')
    if os.path.isdir(lab_name):
        shutil.rmtree(lab_name)
    os.mkdir(lab_name)

    # Extract main archive file
    Archive(labs_archive).extractall(lab_name)
    os.chdir(lab_name)

    # Parse every subdirectory (student)
    for student_dir in os.listdir('.'):
        # Find student's name and rename directory if necessary
        # Example start name:
        # Firstname Lastname_7511054_assignsubmission_file_
        if '_' in student_dir:
            name = student_dir.split('_', 1)[0]
            os.rename(student_dir, name)
        else:
            name = student_dir

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
                os.rmdir(path)  # TODO: Remove any leftover non-.vhd/.xdc files
