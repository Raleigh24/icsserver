.. :changelog:

Release History
---------------


Current
++++++++++++++++++

**Miscellaneous**

- Refactored rpc interface functions


1.2.2 (2018-06-28)
++++++++++++++++++

**Improvements**

- Server will create UDS socket directory if does not exist
- Improved error handling when creating UDS socket
- Correct permissions applied to UDS socket

**Bugfixes**

- Fixed incorrect exception handling for network issues at startup


1.2.1 (2018-04-10)
++++++++++++++++++

**Improvements**

- Only enabled resources are considered when calculating group states
- Resource propagation can continue though disabled resources

**Miscellaneous**

- Removed default names from config file


1.2.0 (2018-03-04)
++++++++++++++++++

**Improvements**

- Use UDS socket rather than TCP to improve localization and security
- Moved resource exceptions to separate file
- Made python bin location more dynamic to support different environments
- Changed print statements to be compatible with python3 (python3 not yet supported)
- Added module compatibility for python3 (python3 not yet supported)
- Added command to icsserver to change working directory of server to prevent issues if working directory is removed


**Miscellaneous**

- Reworked project directory structure
- Refactored testing tools


1.1.1 (2018-03-14)
++++++++++++++++++

**New Features**

- Added automatic creation of config directory

**Improvements**

- Added exception handling for creating log file
- Added exception handling for creating pid file
- Added more robust signal handling for CLI commands
- Changed polling info in log from info to debug level
- Formatted CLI error messages to be consistent
- Improved general logging
- Added signal command to icsstop to shutdown server without using -force option

**Bugfixes**

- Fixed bug where exception is raised when getting state of group that has
    no resources. Group state will now return unknown.
- Fixed bug where resources would be disassociated from a group when creating a group that
    already exists


1.1.0 (2018-02-15)
++++++++++++++++++

**New Features**

- Changed method of starting and stopping server by adding icsstart
    and icsstop and removed icsserver command

**Improvements**

- Changed bash scripts in bin to set correct ICS_HOME


1.0.0 (2018-02-13)
++++++++++++++++++
- Initial version