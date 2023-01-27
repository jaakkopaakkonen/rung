# taskgraph
taskgraph (graph of tasks by their interrelated dependencies) is 
a modular framework for testing and everyday operations based on 
simple small and independent scripts on command line level, 
and their inter dependencies.

## Functionality
The framework is divided in two separate but equally important parts. 

The scripts aka. tasks which describe *what* is to be done with the input values, 
and input values themselves which' control which scripts are to be executed in which order.

### Tasks
Tasks can be python functions or shell scripts for now.

You can write your own task or use the tasks coming with the framework.

Each task has set of zero or more inputs , mandatory or optional, 
a name and executable part (python function, command or shell script).

All tasks have a string name. Inputs are name value pairs, both are strings.

### Result store
You can use results of earlier executed tasks as input by using task name
(and possible keys and indexes if result is dictionary or list) as input value.




# Development

## TODO
| id  | Importance      | Component        | Task                                                                                                                                                                                                                                                   | Size     | Difficulty     | Current Status
|-----|-----------------|------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------|----------------|---
| 2   | Quite important | `dag`            | Optional inputs are not traversed from the values.<br/>If you have task with optional input which can be built from the inputs provided but the original optional input in itself is not provided,<br/>framework does not construct the optional input | Huge     | Very difficult | Status unknown.<br/>Create unittest.
| 3   | Important       | values           | Output all values related to task execution to enable result comparison/verification                                                                                                                                                                   | Smallish | Easy           | Under the hood functions exist and information available.<br/>Design elegant usage 
| 4   | Medium          | `send_smtp_mail` | Fill result from execution of the task.                                                                                                                                                                                                                | Small    | Easy           
| 5   | Medium          | dag + values     | Figure out how artefacts are removed (eg. mails in imap mailbox) on framework level.                                                                                                                                                                   | Big      | Hard
| 6   | Medium          | modules          | Create task to remove mails from imap inbox                                                                                                                                                                                                            |          |                | Depends on #5
| 7   | Very important  | results          | Compare result values to predefined set of what they should be.                                                                                                                                                                                        | Medium   | Medium
| 9   |                 |                  | Check results incrementally while running to enable long/infinite sessions                                                                                                                                                                             
| 10  | Low             | main             | Option for showing only possible tasks with current set inputs                                                                                                                                                                                       
| 11  | Very important  | dag tasks        | Name spaces based on modules for inputs. Eg. `jenkins.username`                                                                                                                                                                                        | Big      | Hard
| 12  | Quite Important | task             | Enable default input to make `tg task_name=value`
