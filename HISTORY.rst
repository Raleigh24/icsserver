.. :changelog:

Release History
---------------

Current
+++++++

**Improvements**

- Use UDS socket rather than TCP to improve localization and security
- Moved resource exceptions to separate file

**Miscellaneous**

- Reworked project directory structure

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