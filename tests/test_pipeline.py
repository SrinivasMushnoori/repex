from radical.entk import Pipeline, Stage, Task
from radical.entk import states
from radical.entk.exceptions import *
import pytest, threading

def test_pipeline_initialization():

    """
    ***Purpose***: Test if pipeline attributes are correctly initialized upon creation
    """

    p = Pipeline()

    assert type(p._uid) == str
