.. :changelog:

Release History
---------------

2.1.2 (2021-07-07)
++++++++++++++++++

**Improvements**

- Added improved exception handling to prevent threads from stopping

**Bugfixes**

- Fixed issue where ICS server unable to startup when a resource is disabled.
- Fixed issue when starting a group with resources with no dependencies showed the group state as UNKNOWN instead of PARTIAL

2.1.1 (2021-05-20)
++++++++++++++++++

**Bugfixes**

- Fixed issue where service group is able to come online when Parallel attribute is false

**Miscellaneous**

- Changed IgnoreDisabled default value to true

2.1.0 (2021-03-25)
++++++++++++++++++

**New Features**

- Added ability to allow the system to decide which node to start a service group based on a user defined system load
- Added Load attribute to resources to allow the user to specify the amount of load a resource will put on a system
- Added SystemList attribute to service groups to specify which nodes a service group can become online
- Added icsdump command line tool to dump system data for external use
- Added user executed commands to logs
- Added ability to show all nodes status in the cluster with icssys -state

**Improvements**

- Added better support for modifying list attributes
- Updated -wait arguments for icsgrp and icsres to support clustering conditions

**Bugfixes**

- Fixed issue with using and saving alert recipients
- Fixed issue with catching exceptions when unable to connect to server with command line tools
- Fixed issue where icsgrp -state <group> and icsres -state <res> output a dictionary instead of a table

**Miscellaneous**

- Removed NodeName attribute as a user editable attribute
- All nodes in cluster are now it NodeList attribute

2.0.0 (2021-03-10)
++++++++++++++++++

**New Features**

- Added node clustering using Pyro
- Added daemon process to control start/stop of icsserver
- Separated out alerts management to separate process

**Improvements**

- Added ability to be packaged and installed using pip
- Added -version option to icssys
- Added -list option to icssys
- Improved logging control
- Resource logs are rotated

**Miscellaneous**

- Added GNU General Public License v3.0 licence
- Added unit testing
- Added test alerts


1.3.0 (2019-02-20)
++++++++++++++++++

**New Features**

- Added system level attribute control
- Added icssys command for system level control
- Added ClusterName system attribute
- Added NodeName system attribute
- Added GroupLimit system attribute
- Added BackupInterval system attribute
- Added AlertRecipients system attribute
- Added AlertLevel system attribute
- Added AutoStart group attribute
- Added IgnoreDisabled group attribute
- Added config backup feature
- Added ability to change log level during runtime
- Added attribute list method to attribute class
- Added attribute option to icsgrp command
- Added attribute value option to icsgrp command
- Added attribute modify option to icsgrp command
- Added attribute option to icsres command
- Added attribute option to icssys command
- Added enabledresources to icsgrp command
- Added disableresources to icsgrp command

**Bugfixes**

- Fixed issue where listing resources would hang in a system with a large number of resources


**Miscellaneous**

- Major code refactor of central system to better manage system level functions and centralize system data
- Refactored rpc interface functions
- Refactored environment variable configuration
- Refactored config file functions
- Added exception logging to rpc handler


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