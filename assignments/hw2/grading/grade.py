#!/usr/bin/env python3

import os
import shutil
import subprocess
from pathlib import Path
import csv

class Submission:
    file_location = ""
    staging_root = None
    notes = None
    score = 0
    gradeable = False
    def __init__(self, sub_id, students):
        self.sub_id = sub_id
        self.students = students

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "Submission: {}. Students: {}. Gradeable: {}, Files: {} ,Score: {}, Notes: {}\n".format(self.sub_id, self.students, self.gradeable, self.file_location, self.score, self.notes)

submissions = {}

for entry in os.walk("../submissions", topdown=True):
    dir_name = entry[0]
    files = entry[2]

    dir_splits = dir_name.split("/")
    if len(dir_splits) < 3:
        continue;

    subs = dir_splits[2]
    subs_splits = subs.split("_")

    students = []
    sub_id = subs_splits[0]
    if subs_splits[1] == 'LATE':
        subs_splits.remove('LATE')
    if sub_id.startswith('homeworkgroup'):
        students = [subs_splits[-2].lower(), subs_splits[-1].lower()]
    else:
        if len(subs_splits) == 5:
            students = [subs_splits[-2].lower(), subs_splits[-1].lower()]
        else:
            students = [subs_splits[-1]]

    rem_suf = students[len(students) - 1].split('-')
    if len(rem_suf) > 0:
        students[-1] = rem_suf[0]

    submission = Submission(sub_id, students)
    gradeable = 'PriorityQueue.java' in files;

    if sub_id in submissions and submissions[sub_id].gradeable:
        continue

    if gradeable:
        submission.notes = ''
        submission.file_location = entry[0]
        submission.gradeable = True

    else:
        submission.notes = "Ungradeable: Missing file PriorityQueue.java"
        submission.gradeable = False

    submissions[sub_id] = submission

with open('grades.csv', 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=['eid', 'group', 'score', 'notes'])
    writer.writeheader()

    for s in submissions.values():
        print(s)
        if not s.gradeable:
            for stu in s.students:
                writer.writerow({'eid': stu, 'group': s.sub_id, 'score': s.score, 'notes': s.notes})
                csvfile.flush()
            continue
        # Create a subtree for each submission with a maven project we can run
        s.staging_root = './staging/{}'.format(s.sub_id)
        shutil.rmtree(s.staging_root)
        os.makedirs("{}/src/test/java".format(s.staging_root))

        shutil.copytree(s.file_location, "{}/src/main/java".format(s.staging_root))
        shutil.copy("./src/test/java/TestPriorityQueue.java", "{}/src/test/java/TestPriorityQueue.java".format(s.staging_root))
        shutil.copy("pom.xml", "{}/pom.xml".format(s.staging_root))

        print("Running tests in: {}".format(s.staging_root))
        p = subprocess.Popen(["mvn", "clean", "test"], cwd=s.staging_root)
        try:
            p.wait(timeout=20)

            result_path = "{}/target/surefire-reports/TestPriorityQueue.txt".format(s.staging_root)

            result_file = Path(result_path)
            if not result_file.exists():
                s.notes = "Submission didn't compile"
                for stu in s.students:
                    writer.writerow({'eid': stu, 'group': s.sub_id, 'score': s.score, 'notes': s.notes})
                csvfile.flush()
                continue;

            # Parse the test result file
            with open(result_path, mode='r') as result_file:
                all_results = result_file.readlines()
                results_summary = all_results[3].split(',')
                print(results_summary)
                tests_run = float(results_summary[0].replace("Tests run:", "").strip())
                tests_failed = float(results_summary[1].replace("Failures:", "").strip()) + float(results_summary[2].replace("Errors:", "").strip())
                pass_ratio = (tests_run - tests_failed) / tests_run
                s.score = max(5, int(35 * pass_ratio))
                s.gradeable = True
                if tests_failed > 0.0:
                    s.notes = "Tests failed: "
                    for line in all_results:
                        if line.startswith('test'):
                            test_name = line.split(' ')[0]
                            s.notes += test_name + "; "

                for stu in s.students:
                    writer.writerow({'eid': stu, 'group': s.sub_id, 'score': s.score, 'notes': s.notes})
                csvfile.flush()
                continue

        except subprocess.TimeoutExpired:
            s.notes = "Tests timed out."
            s.score = 3
            s.gradeable = True
            for stu in s.students:
                writer.writerow({'eid': stu, 'group': s.sub_id, 'score': s.score, 'notes': s.notes})
                csvfile.flush()
            continue
