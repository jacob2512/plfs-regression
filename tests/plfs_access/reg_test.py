#!/usr/bin/env python
#
# Test plfs_access in a FUSE PLFS mount point.

import os,sys,getpass,re,datetime,subprocess
from time import localtime, strftime
#
# Get the username of the user running this test.
#
#user = getpass.getuser()
#
# Figure out the base directory of the regression suite
#
curr_dir = os.getcwd()
#
# This method of the "Regular Expression" (re) class returns
# the part of "curr_dir" up to the character just before
# "regression/".
#
basedir = re.sub('tests/plfs_access.*', '', curr_dir)

#
# Add the directory that contains the helper scripts. We'll need
# experiment_management
utils_dir = basedir + "tests/utils"
if utils_dir not in sys.path:
    sys.path += [ utils_dir ]

# Import the module for dealing with experiment_management paths
import rs_exprmgmt_paths_add as emp
# Add the experiment_management location to sys.path
emp.add_exprmgmt_paths(basedir)
import expr_mgmt

class AccessError(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return str(self.msg)

def main(argv=None):
    """Main method for running this test.

    Return values:
     0: Test ran
    -1: Problem with mounting plfs
    """
    #
    # Where the output of the test will be placed.
    #
    out_dir = (str(expr_mgmt.config_option_value("outdir")) + "/"
        + str(datetime.date.today()))
    #
    # Create the directory if needed
    #
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    out_file = (str(out_dir) + "/" + str(strftime("%H-%M-%S", localtime())) + ".log")
    try:
        of = open(out_file, 'w')
    except OSError, detail:
        print ("Error: unable to create log file " + str(out_file) + ": " + str(detail))
        return [ -1 ]
    #
    # Temporarily redirect standard output and standard error to a log
    # file for this test. We'll use check_results.py to look at that
    # file and determine if the test passed or failed.
    #
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = of
    sys.stderr = of
    #
    # Test status
    #
    test_stat = "FAILED"

    try:
        problem = False # Problems with changing ownership of a file?
        #
        # Call the access.bash /bin/bash script to do the plfs_access test. It will echo
        # its output to stderr and stdout, so point that to the file we have opened.
        #
        p = subprocess.Popen(['./access.bash'], stdout=of, stderr=of, shell=True)
        p.communicate()
        if p.returncode != 0:
            raise AccessError("Problem using plfs_access on plfs mount.\nExiting.\n")

        test_stat = "PASSED"
        
    except AccessError, detail:
        print("Problem dealing with plfs_access: " + str(detail))
#
# If we ever go back to the old terminating check, uncomment the line:
#         problem = True
#
    else:
        print("The test " + str(test_stat))
    finally:
        #
        # Close up shop, and revert stdout and stderr to their normal places.
        #
        of.close()
        sys.stdout = old_stdout
        sys.stderr = old_stderr
#
# If we get to this place, we'll return 0 so that check_results.py will
# process the output file and determine success or failure from the output
# file.
#
        return [ 0 ]
#
# This was the old terminating check.
#
#        if problem == True:
#
# David Shrader says to return 0 no matter what so that check_results.py can
# run and detect the error.
#
#            return [ 0 ]
#            return [ -1 ]
#        else:
#            return [ 0 ]

if __name__ == "__main__":
    ret = main()
    # ret is a list, so don't return it to the shell. For now, just return a 0.
    sys.exit(0)
