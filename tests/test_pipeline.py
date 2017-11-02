from radical.entk import Pipeline, Stage, Task
import pytest

def test_pipeline_initialization():

    """
    ***Purpose***: Test if pipeline attributes are correctly initialized upon creation
    """

    p = Pipeline()

    assert type(p._uid) == str

    
