#!/usr/bin/env python
#
# A simple read and write using adio

import os,imp
(fp, path, desc) = imp.find_module('test_common', [os.getcwd()])
test_common = imp.load_module('test_common', fp, path, desc)
fp.close()
import fs_test


mpi_options = {
    "n"     : [ test_common.nprocs ]
}

mpi_program = ( str(test_common.basedir) + "inst/test_fs/fs_test."            
            + os.getenv("MY_MPI_HOST") + ".x" )

program_options = {
  "size"       : [ 1048760 ],
  "deletefile" : [ '' ],
  "shift"      : [ '' ],
  "nodb"       : [ ''],
  "type"     : [ 2 ],
  "nobj"     : [ 4 ],
  "strided"  : [ 0 ],
  "target"   : [ "plfs:$path" ],
  "touch"       : [ '3' ],
  "check"       : [ '3' ]
}

# fs_test doesn't need program_arguments

def get_commands(expr_mgmt_options):
  global mpi_options, mpi_program, program_options 
  return fs_test.get_commands( mpi_options=mpi_options, 
          mpi_program=mpi_program, program_options=program_options,
          n1_strided=False, n1_segmented=True, nn=False,
          expr_mgmt_options=expr_mgmt_options )
