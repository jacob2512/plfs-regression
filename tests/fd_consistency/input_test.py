#!/usr/bin/env python
#
# Submit the script just created.

import imp,os
(fp, path, desc) = imp.find_module('test_common', [os.getcwd()])
test_common = imp.load_module('test_common', fp, path, desc)
fp.close()

import expr_mgmt

# Script that we want experiment_managment to run.
script="reg_test.sh"

# Don't use mpirun; the field needs to be empty. Same with mpi_options.
mpirun=''

mpi_options = {}

mpi_program = ( test_common.curr_dir + "/" + str(script))

program_options = {}

def get_commands(expr_mgmt_options):
  global mpi_options, mpi_program, program_options 
  return expr_mgmt.get_commands( mpi_options=mpi_options, 
          mpi_program=mpi_program, program_options=program_options,
          mpirun=mpirun, expr_mgmt_options=expr_mgmt_options)
