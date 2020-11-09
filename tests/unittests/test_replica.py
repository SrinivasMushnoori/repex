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
        import pprint
        pwd = os.path.dirname(os.path.abspath(__file__))
        wl = ru.read_json(pwd + '/test_case/workflow_gromacs.json')

        workload =  ru.Config(cfg=wl)
        
        test_rep = Replica(workload=workload)
        
        test_rep.add_md_stage(sid='test_sid')
        
        self.assertEqual(len(test_rep.stages),
                         len(workload['md']['description'])) 
        task0 = list(test_rep.stages[0].tasks)[0]
        self.assertEqual(task0.name, 'test.0000.0000.md')
        self.assertEqual(task0.sandbox, 'test.0000.md')
        link_inputs = ['pilot:///inputs//mdin.mdp.test > resource:///test_sid/pilot.0000/test.0000.md/mdin.mdp', 
                       'pilot:///inputs//sys.top > resource:///test_sid/pilot.0000/test.0000.md/sys.top',
                       'pilot:///inputs//sys.itp > resource:///test_sid/pilot.0000/test.0000.md/sys.itp', 
                       'pilot:///inputs//inp.ener > resource:///test_sid/pilot.0000/test.0000.md/inp.ener', 
                       'pilot:///inputs//martini_v2.2.itp > resource:///test_sid/pilot.0000/test.0000.md/martini_v2.2.itp', 
                       'pilot:///inputs//inpcrd.gro.test > resource:///test_sid/pilot.0000/test.0000.md/inpcrd.gro']
        self.assertEqual(task0.link_input_data, link_inputs)
        self.assertEqual(task0.arguments, ['grompp', '-f', 'mdin.mdp', '-c', 'inpcrd.gro', '-o', 'sys.tpr', '-p', 'sys.top'])
        self.assertEqual(task0.cpu_reqs, {'process_type': 'MPI', 'processes': 1, 'thread_type': None, 'threads_per_process': 1})
        self.assertEqual(task0.executable, 'gmx_mpi')
        self.assertEqual(task0.pre_exec, ['module purge', 'module load intel/19.3', 'module load gromacs/2018_cpu'])

        task1 = list(test_rep.stages[1].tasks)[0]
        self.assertEqual(task1.name, 'test.0000.0001.md')
        self.assertEqual(task1.sandbox, 'test.0000.md')
        link_inputs = []
        self.assertEqual(task1.link_input_data, link_inputs)
        self.assertEqual(task1.arguments, ["mdrun", "-s", "sys.tpr", "-deffnm", "sys", "-c", "outcrd.gro", "-e", "sys.edr"])
        self.assertEqual(task1.cpu_reqs, {'process_type': 'MPI', 'processes': 4, 'thread_type': None, 'threads_per_process': 1})
        self.assertEqual(task1.executable, 'gmx_mpi')
        self.assertEqual(task1.pre_exec, ['module purge', 'module load intel/19.3', 'module load gromacs/2018_cpu'])

        task2 = list(test_rep.stages[2].tasks)[0]
        self.assertEqual(task2.name, 'test.0000.0002.md')
        self.assertEqual(task2.sandbox, 'test.0000.md')
        link_inputs = []
        self.assertEqual(task2.link_input_data, link_inputs)
        download_output_data = ['resource:///test_sid/pilot.0000/test.0000.md/outcrd.gro > client:///outputs//outcrd.gro.test.0000']
        self.assertEqual(task2.download_output_data, download_output_data)
        self.assertEqual(task2.arguments, [ "energy", "-f", "sys.edr", "-b", 0.25, "<", "inp.ener", ">", "mdinfo"])
        self.assertEqual(task2.cpu_reqs, {'process_type': 'MPI', 'processes': 1, 'thread_type': None, 'threads_per_process': 1})
        self.assertEqual(task2.executable, 'gmx_mpi')
        self.assertEqual(task2.pre_exec, ['module purge', 'module load intel/19.3', 'module load gromacs/2018_cpu'])

        # Inserting second MD cycle
        test_rep.add_md_stage(sid='test_sid', exchanged_from='ex_0')
        
        task0 = list(test_rep.stages[3].tasks)[0]
        self.assertEqual(task0.name, 'test.0001.0000.md')
        self.assertEqual(task0.sandbox, 'test.0001.md')
        pprint.pprint(task0.link_input_data)
        link_inputs = ['pilot:///inputs//mdin.mdp.test > resource:///test_sid/pilot.0000/test.0001.md/mdin.mdp', 
                       'pilot:///inputs//sys.top > resource:///test_sid/pilot.0000/test.0001.md/sys.top',
                       'pilot:///inputs//sys.itp > resource:///test_sid/pilot.0000/test.0001.md/sys.itp', 
                       'pilot:///inputs//inp.ener > resource:///test_sid/pilot.0000/test.0001.md/inp.ener', 
                       'pilot:///inputs//martini_v2.2.itp > resource:///test_sid/pilot.0000/test.0001.md/martini_v2.2.itp', 
                       'resource:///test_sid/pilot.0000/ex_0/outcrd.gro.test > resource:///test_sid/pilot.0000/test.0001.md/inpcrd.gro']
        self.assertEqual(task0.link_input_data, link_inputs)
        self.assertEqual(task0.arguments, ['grompp', '-f', 'mdin.mdp', '-c', 'inpcrd.gro', '-o', 'sys.tpr', '-p', 'sys.top'])
        self.assertEqual(task0.cpu_reqs, {'process_type': 'MPI', 'processes': 1, 'thread_type': None, 'threads_per_process': 1})
        self.assertEqual(task0.executable, 'gmx_mpi')
        self.assertEqual(task0.pre_exec, ['module purge', 'module load intel/19.3', 'module load gromacs/2018_cpu'])

        task1 = list(test_rep.stages[4].tasks)[0]
        self.assertEqual(task1.name, 'test.0001.0001.md')
        self.assertEqual(task1.sandbox, 'test.0001.md')
        link_inputs = []
        self.assertEqual(task1.link_input_data, link_inputs)
        self.assertEqual(task1.arguments, ["mdrun", "-s", "sys.tpr", "-deffnm", "sys", "-c", "outcrd.gro", "-e", "sys.edr"])
        self.assertEqual(task1.cpu_reqs, {'process_type': 'MPI', 'processes': 4, 'thread_type': None, 'threads_per_process': 1})
        self.assertEqual(task1.executable, 'gmx_mpi')
        self.assertEqual(task1.pre_exec, ['module purge', 'module load intel/19.3', 'module load gromacs/2018_cpu'])

        task2 = list(test_rep.stages[5].tasks)[0]
        self.assertEqual(task2.name, 'test.0001.0002.md')
        self.assertEqual(task2.sandbox, 'test.0001.md')
        link_inputs = []
        self.assertEqual(task2.link_input_data, link_inputs)
        download_output_data = ['resource:///test_sid/pilot.0000/test.0001.md/outcrd.gro > client:///outputs//outcrd.gro.test.0001']
        self.assertEqual(task2.download_output_data, download_output_data)
        self.assertEqual(task2.arguments, [ "energy", "-f", "sys.edr", "-b", 0.25, "<", "inp.ener", ">", "mdinfo"])
        self.assertEqual(task2.cpu_reqs, {'process_type': 'MPI', 'processes': 1, 'thread_type': None, 'threads_per_process': 1})
        self.assertEqual(task2.executable, 'gmx_mpi')
        self.assertEqual(task2.pre_exec, ['module purge', 'module load intel/19.3', 'module load gromacs/2018_cpu'])