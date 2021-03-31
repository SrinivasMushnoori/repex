# pylint: disable=protected-access, unused-argument
# pylint: disable=no-value-for-parameter

__copyright__ = "Copyright 2020, http://radical.rutgers.edu"
__license__   = "MIT"

from unittest import TestCase

import os
import radical.utils as ru

from radical.repex.replica import Replica
from radical.entk import Pipeline, Stage, Task

try:
    import mock
except ImportError:
    from unittest import mock


# ------------------------------------------------------------------------------
#
class TestTask(TestCase):

    # --------------------------------------------------------------------------
    #
    @mock.patch('radical.utils.generate_id', return_value='test')
    @mock.patch('radical.utils.Logger')
    def test_add_md_stage(self, mocked_generate_id, mocked_Logger):

        pwd = os.path.dirname(os.path.abspath(__file__))
        wl_cfg = ru.read_json(pwd + '/test_case/workflow_gromacs.json')
        workload = ru.Config(cfg=wl_cfg)

        test_rep = Replica(workload=workload)

        test_rep.add_md_stage(sid='test_sid')

        self.assertEqual(len(test_rep.stages),
                         len(workload['md']['description']))
        task0 = list(test_rep.stages[0].tasks)[0]
        self.assertEqual(task0.name, 'test.0000.0000.md')
        self.assertEqual(task0.sandbox, 'test.0000.md')

        link_inputs = ['pilot:///inputs//mdin.mdp.test > unit:////mdin.mdp',
                       'pilot:///inputs//sys.top > unit:////sys.top',
                       'pilot:///inputs//sys.itp > unit:////sys.itp',
                       'pilot:///inputs//inp.ener > unit:////inp.ener',
                       'pilot:///inputs//martini_v2.2.itp > unit:////martini_v2.2.itp',
                       'pilot:///inputs//inpcrd.gro.test > unit:////inpcrd.gro']
        self.assertEqual(task0.link_input_data, link_inputs)
        self.assertEqual(task0.arguments, ['grompp', '-f', 'mdin.mdp', '-c',
                                           'inpcrd.gro', '-o', 'sys.tpr', '-p',
                                           'sys.top'])
        self.assertEqual(task0.cpu_reqs, {'cpu_process_type': 'MPI',
                                          'cpu_processes': 1,
                                          'cpu_thread_type': None,
                                          'cpu_threads': 1})
        self.assertEqual(task0.executable, 'gmx_mpi')
        self.assertEqual(task0.pre_exec, ["module load gromacs/2020.2-cpu",
                                          "export GMX_MAXBACKUP=-1"])

        task1 = list(test_rep.stages[1].tasks)[0]
        self.assertEqual(task1.name, 'test.0000.0001.md')
        self.assertEqual(task1.sandbox, 'test.0000.md')

        link_inputs = []
        self.assertEqual(task1.link_input_data, link_inputs)
        self.assertEqual(task1.arguments, ["mdrun", "-s", "sys.tpr", "-deffnm",
                                           "sys", "-c", "outcrd.gro", "-e",
                                           "sys.edr"])
        self.assertEqual(task1.cpu_reqs, {'cpu_process_type': 'MPI',
                                          'cpu_processes': 4,
                                          'cpu_thread_type': None,
                                          'cpu_threads': 1})
        self.assertEqual(task1.executable, 'gmx_mpi')
        self.assertEqual(task1.pre_exec, ["module load gromacs/2020.2-cpu",
                                          "export GMX_MAXBACKUP=-1"])

        task2 = list(test_rep.stages[2].tasks)[0]
        self.assertEqual(task2.name, 'test.0000.0002.md')
        self.assertEqual(task2.sandbox, 'test.0000.md')

        link_inputs = []
        self.assertEqual(task2.link_input_data, link_inputs)
        download_output_data = ['unit:////outcrd.gro > \
                                 client:///outputs//outcrd.gro.test.0000']
        self.assertEqual(task2.download_output_data, download_output_data)
        self.assertEqual(task2.arguments, [ "energy", "-f", "sys.edr", "-b",
                                            0.25, "<", "inp.ener", ">",
                                            "mdinfo"])
        self.assertEqual(task2.cpu_reqs, {'cpu_process_type': 'MPI',
                                          'cpu_processes': 1,
                                          'cpu_thread_type': None,
                                          'cpu_threads': 1})
        self.assertEqual(task2.executable, 'gmx_mpi')
        self.assertEqual(task2.pre_exec, ["module load gromacs/2020.2-cpu",
                                          "export GMX_MAXBACKUP=-1"])

        # Inserting second MD cycle
        ex_0 = Task()
        ex_0.name = 'test.ex'
        ex_0.sandbox = 'ex.0'
        test_rep.add_md_stage(sid='test.sid', exchanged_from=ex_0)
        task0 = list(test_rep.stages[3].tasks)[0]

        self.assertEqual(task0.name, 'test.0001.0000.md')
        self.assertEqual(task0.sandbox, 'test.0001.md')

        link_inputs = ['pilot:///inputs//mdin.mdp.test > unit:////mdin.mdp',
                       'pilot:///inputs//sys.top > unit:////sys.top',
                       'pilot:///inputs//sys.itp > unit:////sys.itp',
                       'pilot:///inputs//inp.ener > unit:////inp.ener',
                       'pilot:///inputs//martini_v2.2.itp > \
                        unit:////martini_v2.2.itp',
                       'pilot:///ex_0/outcrd.gro.test > unit:////inpcrd.gro']
        self.assertEqual(task0.link_input_data, link_inputs)
        self.assertEqual(task0.arguments, ['grompp', '-f', 'mdin.mdp', '-c',
                                           'inpcrd.gro', '-o', 'sys.tpr', '-p',
                                           'sys.top'])
        self.assertEqual(task0.cpu_reqs, {'cpu_process_type': 'MPI',
                                          'cpu_processes': 1,
                                          'cpu_thread_type': None,
                                          'cpu_threads': 1})
        self.assertEqual(task0.executable, 'gmx_mpi')
        self.assertEqual(task0.pre_exec, ["module load gromacs/2020.2-cpu",
                                          "export GMX_MAXBACKUP=-1"])

        task1 = list(test_rep.stages[4].tasks)[0]
        self.assertEqual(task1.name, 'test.0001.0001.md')
        self.assertEqual(task1.sandbox, 'test.0001.md')

        link_inputs = []
        self.assertEqual(task1.link_input_data, link_inputs)
        self.assertEqual(task1.arguments, ["mdrun", "-s", "sys.tpr", "-deffnm", 
                                           "sys", "-c", "outcrd.gro", "-e",
                                           "sys.edr"])
        self.assertEqual(task1.cpu_reqs, {'cpu_process_type': 'MPI',
                                          'cpu_processes': 4,
                                          'cpu_thread_type': None,
                                          'cpu_threads': 1})
        self.assertEqual(task1.executable, 'gmx_mpi')
        self.assertEqual(task1.pre_exec, ["module load gromacs/2020.2-cpu",
                                          "export GMX_MAXBACKUP=-1"])

        task2 = list(test_rep.stages[5].tasks)[0]
        self.assertEqual(task2.name, 'test.0001.0002.md')
        self.assertEqual(task2.sandbox, 'test.0001.md')

        link_inputs = []
        self.assertEqual(task2.link_input_data, link_inputs)
        download_output_data = ['unit:////outcrd.gro > \
                                 client:///outputs//outcrd.gro.test.0001']
        self.assertEqual(task2.download_output_data, download_output_data)
        self.assertEqual(task2.arguments, [ "energy", "-f", "sys.edr", "-b", 
                                            0.25, "<", "inp.ener", ">",
                                            "mdinfo"])
        self.assertEqual(task2.cpu_reqs, {'cpu_process_type': 'MPI',
                                          'cpu_processes': 1,
                                          'cpu_thread_type': None,
                                          'cpu_threads': 1})
        self.assertEqual(task2.executable, 'gmx_mpi')
        self.assertEqual(task2.pre_exec, ["module load gromacs/2020.2-cpu",
                                          "export GMX_MAXBACKUP=-1"])
