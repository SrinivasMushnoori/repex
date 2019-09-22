
<img src="https://travis-ci.org/radical-cybertools/radical.repex.svg?branch=master" alt="Travis CI"/>

# ReplicaExchange

Replica-Exchange (RE) is a family of simulation techniques used to enhance
sampling and more thoroughly explore phase space of simulations. RE simulations
involve the concurrent execution of independent simulations which interact and
exchange information. Replica Exchange (RE), a method devised as early as 1986
by Swendsen et. al., is a popular technique to enhance sampling in molecular
simulations. Replica Exchange Molecular Dynamics (REMD) was first formulated in
1999 by Sugita and Okamoto. Initially REMD was used to perform exchanges of
temperatures, but was later extended to perform other exchange types. Over the
years, REMD has been adopted by many scientific disciplines including chemistry,
physics, biology and materials science.

Most RE implementations however are confined within their parent molecular
dynamics (MD) packages. This is limiting because it becomes difficult to
implement new RE methods, or apply exchange methods across MD packages.

RepEx is designed to be scalable, flexible, and above all, extensible. New
developments in replica exchange (RE) should not only be limited to specific MD
packages in which they were developed. RepEx aims to decouple the development of
new advanced sampling algorithms from specific MD engines, and allows users to
easily implement their cumstom RE algorithms and plug them into RepEx. RepEx
also supports multiple MD engines including AMBER and GROMACS.

RepEx is available under the MIT License.


# Documentation

RepEx replica exchange package implemented via the Ensemble Toolkit 0.7 API.
Documentation can be found at: https://repex-30.readthedocs.io/en/latest/



