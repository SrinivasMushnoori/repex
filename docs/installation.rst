.. _installation:

************
Installation
************

Install RepEx by running the following commands::
  

    pip install radical.pilot
    pip install radical.entk
    git clone https://github.com/SrinivasMushnoori/repex.git
    cd repex
    python setup.py install

Please note that you will require `RabbitMQ <https://www.rabbitmq.com/>`_ to successfully run RepEx. This is because Ensemble Toolkit uses RMQ, please follow directions `here <https://radicalentk.readthedocs.io/en/latest/install.html#installing-rabbitmq>`_.


Secondly, please ensure that you have a working installation of your preferred MD engine on the target resource (AMBER/GROMACS currently supported)

Once installation is complete, run the following command to ensure that RepEx was correctly installed::

    repex-version

This should display the repex version you have installed (Current release is 3.0.1)
