#!/usr/bin/env python
#
# Run a plfs regression test.

import sys,imp,os,re,subprocess
sys.path += ['./']

# Load the common.py module to get common variables.
(fp, path, desc) = imp.find_module('common', [os.getcwd()])
common = imp.load_module('common', fp, path, desc)
fp.close()

# After loading common.py, can load run_expr
import run_expr

def main(argv=None):
    """The main routine for submitting and running a test.

    Returns a list of job ids submitted for this test.
    """
    if argv == None:
        argv = sys.argv

    # Generated script
    script = "reg_test.sh"
    # Script that can be passed to experiment_management to run the
    # generated script
    input_script = "input_script.py"
    # Walltime for the job(s)
    walltime = "10:00"

    # Figure out the target that this test will be using.
    scratch_target=common.get_panfs_target()
    if scratch_target == None: 
       print ("Error getting a scratch target.")
       return [-1]

    # Figure out the mounts for this test
    mounts = common.get_mountpoints()
    if mounts == None:
        print ("Error getting mounts")
        return [-1]
    # Get the target filename
    filename = common.get_filename()
    # Define utils directory
    utils_dir = (common.basedir + "/tests/utils/")

# Prescript and postscript 
    prescript = (common.basedir + "/tests/utils/rs_plfs_fuse_mount.sh ")
    postscript = (common.basedir + "/tests/utils/rs_plfs_fuse_umount.sh ")
    
    # Create the script
    try:
        f = open(script, 'w')
        # Write the header including statements to get the correct environment
        f.write('#!/bin/bash\n')
        f.write('source ' + str(common.basedir) + '/tests/utils/rs_env_init.sh\n')

        # Create a for loop to iterate throuh all mountpoints/paths
        mounts=' '.join(mounts)
        f.write('for mnt in ' + str(mounts) + '\n')
        f.write('do\n')
        f.write("    echo \"Running " + str(prescript) + "$mnt" + "\"\n")
        f.write("    need_to_umount=\"True\"\n")
        # The next section of code is to determine if the script needs to
        # run the unmount command. If rs_plfs_fuse_mount.sh returns with a 1,
        # this test is not going to issue the unmount command.
        f.write("    " + str(prescript) + "$mnt" + "\n")
        f.write("    ret=$?\n")
        f.write("    if [ \"$ret\" == 0 ]; then\n")
        f.write("        echo \"Mounting successful\"\n")
        f.write("        need_to_umount=\"True\"\n")
        f.write("    elif [ \"$ret\" == 1 ]; then\n")
        f.write("        echo \"Mount points already mounted.\"\n")
        f.write("        need_to_umount=\"False\"\n")
        f.write("    else\n")
        f.write("        echo \"Something wrong with mounting.\"\n")
        f.write("        exit 1\n")
        f.write("    fi\n")
        # Generate target for use by fs_test
        f.write('    top=`' + str(utils_dir) + 'rs_exprmgmtrc_target_path_append.py $mnt`\n')
        f.write('    path=$top/' + str(filename) + '\n')
        f.write('    echo Using $path as target\n')

        f.write("    echo \"Attempting to write to non-plfs space\"\n")
        f.close()

        # Generate the write command
        os.system(str(common.em_p.get_expr_mgmt_dir(common.basedir))
            + "/run_expr.py --dispatch=list ./input_write.py >> " + str(script))
        # Put in a check of the previous command
        f = open(script, 'a')
        f.write("    ret=$?\n")
        f.write("    if [ \"$ret\" == 0 ]; then\n")
        f.write("        echo \"Write successful\"\n")
        f.write("    else\n")
        f.write("        echo \"Something wrong with writing.\"\n")
        f.write("        if [ \"$need_to_umount\" == \"True\" ]; then\n")
        f.write("            echo \"Running " + str(postscript) + "\"\n")
        f.write("            " + str(postscript) + "\n")
        f.write("        fi\n")
        f.write("        exit 1\n")
        f.write("    fi\n")

        # Generate plfs target path from mountpoint
        f.write('    top=`' + str(utils_dir) + 'rs_exprmgmtrc_target_path_append.py $mnt`\n')
        f.write('    plfs_target=$top/' + str(filename) + '\n')
        f.write("    echo \"Using " +  str(scratch_target) + " as copy source\"\n")
        f.write('    echo \"Using $plfs_target as copy target\"\n')

        # Copy scratch file to plfs space 
        f.write("    echo \"Copying file from non-plfs to plfs space\"\n")
        f.write("    cp " + scratch_target + " " + "$plfs_target" + "\n")
        f.write("    echo \"Attempting to read from plfs space\"\n")
        f.close()

        # Generate the read command
        os.system(str(common.em_p.get_expr_mgmt_dir(common.basedir))
            + "/run_expr.py --dispatch=list ./input_read.py >> " + str(script))
        # Remove the targets if it is still there
        os.system("echo \"if [ -e " + str(scratch_target) + " ]; then rm " 
          + str(scratch_target) + "; fi\" >> " + str(script))
#        os.system("echo \"if [ -e " + str(plfs_target) + " ]; then rm " 
#          + str(plfs_target) + "; fi\" >> " + str(script))
        # Write into the script the script that will unmount plfs
        f = open(script, 'a')
        f.write("    if [ \"$need_to_umount\" == \"True\" ]; then\n")
        f.write("        echo \"Running " + str(postscript) + "$mnt" + "\"\n")
        f.write("        " + str(postscript) + "$mnt" + "\n")
        f.write("    fi\n")
        f.write('done\n')
        f.close()
        # Make the script executable.
        os.chmod(script, 0764)
    except (IOError, OSError), detail:
        print ("Problem with creating script " + str(script) 
            + ": " + str(detail))
        return [-1]


    # Run the script through experiment_management
    last_id = run_expr.main(['run_expr', str(common.curr_dir) + "/" + str(input_script),
        '--nprocs=' + str(common.nprocs), '--walltime=' + str(walltime), 
        '--dispatch=msub'])
    return [last_id]
    return [0]

if __name__ == "__main__":
    result = main()
    if result[-1] > 0:
        sys.exit(0)
    else:
        sys.exit(1)
