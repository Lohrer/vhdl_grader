#!/usr/bin/env python3

# Download the zipfile from Moodle and place it in its own directory.
# This script will extract it, delete it, and leave the results in the
# directory.

# Requirements:
# sudo apt install unzip unrar p7zip-full python3-pip
# sudo -H pip3 install --upgrade pip
# sudo -H pip3 install pyunpack patool entrypoint2

import os
import argparse
from difflib import SequenceMatcher
import extractor

diff_cmd = 'diff --ignore-case --ignore-blank-lines --ignore-trailing-space' \
           '--ignore-space-change "%s/%s" "%s/%s"'


def main():
    parser = argparse.ArgumentParser(
        description='Check similarities between moodle submissions')
    parser.add_argument('zip_file', type=argparse.FileType(),
                        help='zip file downloaded from moodle with all'
                             'submissions')
    parser.add_argument('min_diff', type=float, default=0.95, nargs='?',
                        help='min similarity to flag')
    parser.add_argument('--show_diff', action='store_true', default=False,
                        help='show the difference between similar files')
    parser.add_argument('--verbose', '-v', action='store_true', default=False,
                        help='show debug info')
    parser.add_argument('--quick', '-q', action='store_true', default=False,
                        help='faster file comparison that returns an upper'
                             'bound')
    parser.add_argument('--realquick', '-qq', action='store_true',
                        default=False, help='even faster file comparison that'
                                            'returns an upper bound')
    args = parser.parse_args()

    # Extract main archive file into student subdirectories
    extractor.parse_moodle_submissions(args.zip_file.name)

    # Check for .xdc files and remove them
    names = os.listdir('.')  # Create a list of students
    for name in names:
        files = os.listdir(name)
        xdc_files = [xdc for xdc in files if xdc.lower().endswith('.xdc')]
        if len(xdc_files) > 1:
            print(name + ' has multiple XDC files.')
        elif not xdc_files:
            print(name + ' has no XDC file.')

    # Compare all students for similarity (VHDL and XDC files only)
    files = {}
    for i, name1 in enumerate(names):
        # Add the new student's VHDL files to the dictionary
        files[name1] = {f: extractor.read_code_file(os.path.join(name1, f))
                        for f in os.listdir(name1)
                        if f.lower().endswith(('.vhd', '.xdc'))}

        # Compare each student to every student before them
        # Since every preceding student's files have been read,
        # we don't need to read them again
        for j in range(i):
            name2 = names[j]
            if args.verbose:
                print('comparing ' + name1 + ' and ' + name2)

            # Calculate the average similarity over each of name1's files
            similarities = []
            for file1, file1_text in files[name1].items():
                # Find the file that most similarly matches file1
                max_similarity = 0.0
                most_similar_file = ''
                for file2, file2_text in files[name2].items():
                    sm = SequenceMatcher(None, file1_text, file2_text)
                    if args.realquick:
                        sim12 = sm.real_quick_ratio()
                    elif args.quick:
                        sim12 = sm.quick_ratio()
                    else:
                        sim12 = sm.ratio()
                    if sim12 > max_similarity:
                        max_similarity = sim12
                        most_similar_file = file2

                if args.verbose and max_similarity > args.min_diff:
                    print(file1 + ' is similar to ' + most_similar_file +
                          ' to degree ' + str(max_similarity))
                similarities.append((max_similarity, file1, most_similar_file))

            mean = sum(s[0] for s in similarities) / len(similarities)
            if mean > args.min_diff:
                print('Student ' + name1 + ' and ' + name2 +
                      ' are similar to degree ' + str(mean))
                similarities.sort(key=lambda sim: sim[0], reverse=True)
                for sim, f1, f2 in similarities:
                    if sim > args.min_diff:
                        print('(%f, %s, %s)' % (sim, f1, f2))
                        if args.show_diff:
                            cmd = diff_cmd % (name1, f1, name2, f2)
                            os.system(cmd)

    # TODO: Verify existence of testbenches


if __name__ == "__main__":
    main()
