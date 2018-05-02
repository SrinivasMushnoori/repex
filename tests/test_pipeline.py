from radical.entk import Pipeline, Stage, Task
import pytest

def test_pipeline_initialization():

    """
    ***Purpose***: Test if pipeline is correctly initialized upon creation
    """

    p = Pipeline()

    assert type(p._name) == str

    
    #Further tests need to be written when Exchange_methods base class is implemented along with its inherited classes.  
    
