# Task
Task is a single piece or module of execution which always has a name, or
target, in string format.


## Content
Task always has also content of what it actually does.
The actual work implementation of the task can be defined in a shell script, python 
code or with json configuration files.

## Inputs
Tasks may have either optional or mandatory inputs. 
Input consists of input name and value.

If the value of some input is not known when it is needed, tasks with same name as 
needed input are executed as needed. 

These tasks will then provide the correct values as inputs for the actual target task 
to be executed.

Task can have one special default input which' value can be provided without explicitly 
defining the input name by:
``` tg targetName=defaultInputValue```

For instance target `networkConnection` has only one input, which is also the default input, 
called `connection`. Since the only input is defined also as default input, instead of 

`tg connection=MyConnection networkConnection`,

 you can just write 
 
`tg networkConnection=MyConnection`. 
## Json configuration


## Functionality
The framework is divided in two separate but equally important parts. 

The scripts aka. tasks which describe *what* is to be done with the input values, 
and input values themselves which' control which scripts are to be executed in which order.

## Tasks
Tasks can be python functions or shell scripts for now.

You can write your own task or use the tasks coming with the framework.

Each task has set of zero or more inputs , mandatory or optional, 
a name and executable part (python function, command or shell script).

All tasks have a string name. Inputs are name value pairs, both are strings.


`task_func` creates task with executable content (the function contents),
target name (the function name) and inputs.

The inputs will be the function parameters the way they are.

```
from taskgraph.task import task_func

@taskfunc[network.json](taskgraph%2Fmodules%2Fjson%2Fnetwork.json)
def myfunction(myfirstparameter, mysecondparameter)
    print(myfirstparameter)
    print(mysecondparameter)

```

### Command line arguments
Command line arguments can be specified as groups containing zero or more inputs
or optional inputs by specifying them as list of strings in `command_line_arguments`

When running the task, of the elements of command line arguments list are included
if it doesn't contain neither kind of input, it contains mandatory input or it contains
optional input which is specified among the values.
```
{
    "target": "commit",
    "executable": "git",
    "commandLineArguments": ["commit --dry-run", "--file={commit_message_file}", "--message=\"{commit_message}\""],
    "optionalInputs" : ["commit_message_file", "commit_message"]
  },
```


### Runnable part of the task
The runnable part of the task is relayed in tuple as `Task` constructor second parameter.
The first 



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
