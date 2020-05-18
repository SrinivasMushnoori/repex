.. _installation:

************
Installation
************

First, create a Python 3.6+ virtualenv, then install RepEx by running the following commands::
  
    pip install radical.utils
    pip install radical.pilot
    pip install radical.entk
    pip install radical.analytics
    pip install gitpython
    pip install git+https://github.com/radical-cybertools/radical.analytics.git@feature/entk-integration
    git clone https://github.com/SrinivasMushnoori/repex.git
    cd repex
    python setup.py install

Please note that you will require `RabbitMQ <https://www.rabbitmq.com/>`_ to successfully run RepEx. This is because Ensemble Toolkit uses RMQ, please follow directions `here <https://radicalentk.readthedocs.io/en/latest/install.html#installing-rabbitmq>`_.


Secondly, please ensure that you have a working installation of your preferred MD engine (AMBER and GROMACS have been tested so far) as well as a version of python 3.6+ with numpy  on the target resource.

Once installation is complete, run the following command to ensure that RepEx was correctly installed::

    repex-version

This should display the repex version you have installed.
