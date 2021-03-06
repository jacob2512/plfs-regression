#!/usr/bin/env python
#
# Input file for experiment_management

import imp,os
(fp, path, desc) = imp.find_module('common', [os.getcwd()])
common = imp.load_module('common', fp, path, desc)
fp.close()

import fs_test

# For tests of type 2 and 3, use the mount point located in .plfsrc

mpi_options = {
    "n"     : [ common.nprocs ]
}

mpi_program = ( str(common.basedir) + "inst/test_fs/fs_test."            
            + os.getenv("MY_MPI_HOST") + ".x" )

program_options = {
  "size"       : [ 1048760 ],
  "shift"      : [ '' ],
  "nodb"       : [ '' ],
  "type"       : [ 2 ],
  "nobj"       : [ 1 ],
  "strided"    : [ 0 ],
  "op"         : [ 'read' ],
  "touch"      : [ '3' ],
  "check"      : [ '3' ],
  "deletefile" : [ '' ],
  "target"     : [ '$path' ]
}

# fs_test doesn't need program_arguments

def get_commands(expr_mgmt_options):
  global mpi_options, mpi_program, program_options 
  return fs_test.get_commands( mpi_options=mpi_options, 
          mpi_program=mpi_program, program_options=program_options,
          n1_strided=False, n1_segmented=True, nn=False,
          expr_mgmt_options=expr_mgmt_options )
