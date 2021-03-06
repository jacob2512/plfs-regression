#! /bin/tcsh -f
#
# This script will test various mkdir operations. There are three tests: new
# file in a new directory, remove a directory when it is non-empty, and that
# when a directory is created on a PLFS frontend, the corresponding directories
# are create on all of the PLFS backends connected to that frontend.

# Make sure the script that parses out the PLFS mount points is there and that
# it is executable.
if ( -x ../utils/rs_plfs_config_query.py ) then
  set mount_points = `../utils/rs_plfs_config_query.py -m`

  # If the script fails, note that and return a non-zero value.
  if ( $? != 0 ) then
    echo "Failure: Error finding the PLFS mount points with rs_plfs_config_query.py"
    exit 1
  endif

  # Got the mount points parsed from the plfsrc file.
  echo "PLFS mount point(s) is/are: $mount_points"

# The script was not found or is not executable.
else
  echo "Failure: The script, ../utils/rs_plfs_config_query.py, is not executable and must be"
  exit 1
endif

# Check to make sure the script that will append experiment_managment's
# rs_mnt_append_path is available.
if ( ! -x ../utils/rs_exprmgmtrc_target_path_append.py ) then
  echo "Failure: ../utils/rs_exprmgmtrc_target_path_append.py is not executable and must be"
  exit 1
endif

# Check to make sure the script that mounts plfs mount points is available
if ( ! -x ../utils/rs_plfs_fuse_mount.sh ) then
  echo "Failure: The script, ../utils/rs_plfs_fuse_mount.sh, is not executable and must be"
  exit 1
endif

# Check to make sure the script that un-mounts plfs mount points is available
if ( ! -x ../utils/rs_plfs_fuse_umount.sh ) then
  echo "Failure: The script, ../utils/rs_plfs_fuse_umount.sh, is not executable and must be"
  exit 1
endif

# Loop over each of the PLFS mount points defined in the plfsrc file.
foreach mnt ( $mount_points )
#
# Check to see if $mnt is already mounted. If it is not, and it can't be mounted
# successfully, print an error and return a non-zero value to note the error.
#
#  set the_mp = `df | grep ${mnt} | awk '{print $6}'`
#  if ( $the_mp != $mnt ) then
#
  ../utils/rs_plfs_fuse_mount.sh $mnt serial
  set ret_val = $status
#  echo "ret_val is $ret_val"

  if ( $ret_val == 0 ) then
    set need_to_unmount = 1
  else if ( $ret_val == 1 ) then
    set need_to_unmount = 0
  else
    echo "Failure: Mount point $mnt is not mounted and could not be mounted by $USER"
    continue
  endif
#
# Set the place where we will create directories to do the directory operations.
# This includes the using the optional rs_mnt_append_path parameter
#
  set top  = `../utils/rs_exprmgmtrc_target_path_append.py $mnt`
  echo "Using $top for directory operations"
#
# Make the directory where we will do this test.
#
  echo "Making directory $top with mkdir -p..."
  mkdir -p $top
  if ( $? != 0 ) then
    echo "Failure: Error making directory $top with mkdir -p"
    set big_problem = "True"
  else
    echo "Success"
    set big_problem = "False"
  endif

  if ( big_problem != "True" ) then
    #############################################################
    # First test: new file in new directory
    # make sure a new file is indeed present
    #
    echo "Test 1: new file in a new directory"

    set ts   = `date +%s`
    set dir_a = $top/a-$ts
    set ts   = `date +%s`
    set file_a = $dir_a/a.$ts
    #
    # Make the directory where we will create a file and make sure we can
    # see it.
    #
    echo "Making directory $dir_a with mkdir -p..."
    mkdir -p $dir_a
    if ( $? != 0 ) then
      echo "Failure: Error making directory $dir_a with mkdir -p"
    else
      #
      # Create the file that we will verify exists.
      #
      echo "Successfully created $dir_a"
      echo "Creating file $file_a with touch..."
      touch $file_a
      if ( $? != 0 ) then
        echo "Failure: Error creating file $file_a with touch"
      else
        echo "Success"
        set file_name = `ls $file_a`

        if ( $file_name != $file_a ) then
          echo "Failure: The file $file_a was not found."
        else
          echo "Success: $file_a was found."
        endif
      endif
      #
      # Get rid of the directory and file we created.
      #
      echo "Removing the directory $dir_a and the file $file_a..."
      rm -rf $dir_a
    endif

    #############################################################
    # Test 2: remove non-empty directory
    #
    # Now create a directory, copy in /etc/passwd, try to remove the directory without "-rf",
    # which should fail. Make sure our copy is the same as the original /etc/passwd. If
    # all that succeeds, rm -rf the whole directory because it worked as expected.
    #
    echo "Test 2: remove non-empty directory"

    set ts   = `date +%s`
    set dir_p = $top/passwd-$ts
    
    # Make the directory where we will copy the /etc/passwd file.
    echo "Making directory $dir_p with mkdir -p..."
    mkdir -p $dir_p
    if ( $? != 0 ) then
      echo "Failure: Error making directory $dir_p with mkdir -p"
    else
      echo "Success"
      # Copy in /etc/passwd and make sure that succeeds.
      echo "Copying /etc/passwd to $dir_p..."
      cp /etc/passwd $dir_p
      if ( $? != 0 ) then
        echo "Failure: Error copying /etc/passwd to $dir_p."
      else
        echo "Success"
        # Make sure /etc/passwd is in the dir_p.
        set file_name = `ls $dir_p/passwd`

        if ( $file_name != "$dir_p/passwd" ) then
          echo "Failure: The file passwd was not found in $dir_p."
        else
          # check that the files are the same
          set diff_passwd = `diff /etc/passwd $dir_p/passwd`
          if ( $diff_passwd != "" ) then
            echo "Failure: The file passwd was not copied in correctly because it is different than /etc/passwd."
            echo `diff /etc/passwd $dir_p/passwd`
          else
            echo "/etc/passwd and $dir_p/passwd are identical"
            # Try to remove the directory without "-rf" and while a file is in it. We should
            # get an error.
            echo "Attempting to remove $dir_p with rmdir... it should fail because the directory is not empty."
            rmdir $dir_p
            if ( $? == 0 ) then
              echo "Failure: Removed the directory $dir_p when it had a file in it."
            else
              echo "successfully failed to remove directory"
              # Now make sure the copy of /etc/passwd still matches /etc/passwd.
              echo "Checking that $dir_p/passwd is still identical to /etc/passwd"
              set diff_passwd = `diff /etc/passwd $dir_p/passwd`

              if ( $diff_passwd != "" ) then
                echo "Failure: The copied passwd file is no longer identical to /etc/passwd."
                echo `diff /etc/passwd $dir_p/passwd`
              else
                echo "$dir_p/passwd is still identical to /etc/passwd"
              endif
            endif # check on removing plfs directory when non-empty
          endif # check to make sure copied passwd file is the same as the original
        endif # checking that passwd is in the plfs directory
      endif # copying /etc/passwd

      echo "Removing $dir_p with rm -rf..."
      rm -rf $dir_p
    endif #creating dir_p

    #############################################################
    # Test 3: directories on PLFS backend creation
    #
    # Test mkdir: Use a PLFS mount with multiple backends. Create a
    # directory. Use ls on the actual file system (not the PLFS mount point)
    # to verify that it exists on all the backends, not just one.
    #
    echo "Test 3: verify directory creation is reflected on PLFS backends"

    set ts   = `date +%s`
    set dir_e = existence-$ts
    echo "Making directory $top/$dir_e with mkdir -p..."
    mkdir -p $top/$dir_e
    if ( $? != 0 ) then
      echo "Failure: Error making directory $top/$dir_e with mkdir -p"
    else
      echo "Success"
      # Get a list of backends for this mount point.
      set mount_point_backends = `../utils/rs_plfs_config_query.py -b $mnt`
      # If the script fails, note that and return a non-zero value.
      if (( $? != 0 ) || ( mount_point_backends == "" )) then
        echo "Failure: Error finding the PLFS mount point backends with rs_plfs_config_query.py"
      else
        # Got the mount points parsed from the plfsrc file.
        echo "PLFS mount point $mnt backend(s) is/are: $mount_point_backends"
        # Loop over each of the mount point backends defined in the plfsrc file.
        foreach backend ( $mount_point_backends )
          # Need to get the optional append path
          set backend_top_dir = `../utils/rs_exprmgmtrc_target_path_append.py $backend`
          echo "Checking to make sure that $dir_e exists in $backend_top_dir..."
          if ( ! -e $backend_top_dir/$dir_e ) then
            echo "Failure"
          else
            echo "Success"
          endif
        end # loop over plfs backends
      endif # getting mount points

      echo "Removing $top/$dir_e..."
      rm -rf $top/$dir_e
    endif # error creating dir_e
  endif #problem making top-level directory
#
# Now unmount the mount point if it was mounted by us.
#
  if ( $need_to_unmount == "1" ) then
    echo "Calling rs_plfs_fuse_umount.sh to unmount $mnt..."
    ../utils/rs_plfs_fuse_umount.sh $mnt serial
    set ret_val = $status

    if ( $ret_val != 0 ) then
      echo "Failure: Mount point $mnt could not be unmounted by $USER"
    endif
  endif # check on if we need to unmount
end # loop over mount points
