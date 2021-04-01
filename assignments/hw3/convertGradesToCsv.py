'''
By: Siddhartha Shetkar
Usage:
Before using this, it should be used in conjunction with a shell script. For an exmaple look at gradePSort.sh
arg1 - relative or absolute path to file containing all the grades
       Ex. "scores.txt"
       Note: your text file should be something like this format based on how Canvas autodownloads submissions
       [name]_[number]_[number]_[eid1]_[eid2]-[submission number]
       Ex. sidshetkar_234523_12345_ss3453_ry2342 or sidshetkar_234523_12345_ss3453_ry2342-2 
arg2 - relative or absolute path to csv file that gives eid to name mapping
       Ex. "name_to_eid.csv"
       Note: needs format with one column titled "Names" and one column titled "Grades"
'''
import os
import sys
import re
import collections
import pandas as pd

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Please provide path to file with all grades in it.")
        sys.exit()
    elif len(sys.argv) < 3:
        print("Please provide csv file path with the name to eid mapping")
        sys.exit()
    grades_txt_name = sys.argv[1]
    name_to_eid_map_file_name = sys.argv[2]

    # make eid to name map
    name_to_eid_df = pd.read_csv(name_to_eid_map_file_name)
    name_to_eid_map = {}
    for col_name, row in name_to_eid_df.iterrows():
        name_to_eid_map[row['EIDs']] = row['Names']

    grades_df = pd.DataFrame()
    grades = {}

    # store grades in dictionary
    with open(grades_txt_name) as f:
        lines = f.readlines()
        for line in lines:
            line = line.split()
            name = line[0]
            grade = line[1]
            # format name
            if name[-2] == '-':
                # remove dash
                name = name[:-2]
            eids = name.split('_')
            # index eids backwards because all eids are at the end
            first_eid = eids[-1].lower()
            first_name = name_to_eid_map[first_eid]
            grades[first_name] = grade
            # incase student is alone
            second_eid = '' if eids[-2].isnumeric() else eids[-2].lower()
            if second_eid != '':
                second_name = name_to_eid_map[second_eid]
                grades[second_name] = grade
    grades = collections.OrderedDict(
        sorted(grades.items()))
    sorted_names = []
    sorted_grades = []
    for name, grade in grades.items():
        print('{}: {}'.format(name, grade))
        sorted_names.append(name)
        sorted_grades.append(grade)

    grades_df['Names'] = sorted_names
    grades_df['Grades'] = sorted_grades
    grades_df.to_csv('grades.csv')
