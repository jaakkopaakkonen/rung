# Task
Task is a single piece or module of execution which always has a name in string 
format and content of what it actually does.

The content, the actual work implementation of the task can be defined in a shell script, python 
code or with json configuration files.

Json configuration files for task definitions end up calling executable binaries in the system with different argument values.
Python task definitions usually do not call external executables but stay in the python domain.

You can write your own task or use the tasks coming with the framework.

## Inputs
Tasks may have 0 or more mandatory or optional inputs. 
Input consists of input name and value.

If the value of some input is not known when it is needed, tasks with same name as 
needed input are executed as needed. 

These tasks will then provide the correct values as inputs for the actual task 
to be executed.

Task can have one special default input which' value can be provided without explicitly 
defining the input name by:
``` tg taskName=defaultInputValue```

For instance task by the name of `networkConnection` has only one input, which is also the default input, 
called `connection`. Since the only input is defined also as default input, instead of 

`tg connection=MyConnection networkConnection`,

 you can just write 
 
`tg networkConnection=MyConnection`. 


## Defining tasks json modules
Modules are defined as json dictionary which can optionally be stored in a list, 
defined inside a json file.

### Executable
Json based tasks execute command line executables, so the executable name is the
only mandatory field in addition to the task name.

Example:
```
{
    "name": "hostname",
    "executable": "hostname"
}
```

Before any execution or even parsing the tasks from json and python files,
framework examines all the executable binaries available in `PATH` variable 
and ignores all tasks which have defined executable which is not in the `PATH`
and cannot be therefore successfully executed.

### Inputs
Inputs and optional inputs are defined in list with respective names: `inputs`, `optionalInputs`.

If you want to enable the default input execution by only task name from the
command line, the default input must be defined in both `inputs` and 
string value `defaultInput`.

Example:
```
[
  {
    "name": "wifi",
    "executable": "nmcli",
    "commandLineArguments": "radio wifi {state}",
    "inputs": ["state"],
    "defaultInput": "state"
  }
]
```
With above definition wifi can be turned on just by:
```
tg wifi=on
```
instead of 
```
tg state=on wifi
```

### Dependencies between inputs
If task defines inputs, there may be situations where you may want to define 
execution order within the inputs, or dependencies between then.

```
[
  {
    ...
    "inputDependencides": {
      "input1": "secondlevelinput1",
      "input2": "secondlevelinput2",
      "input3": "input1"
    }
  }
]
```

### Setting hard coded inputs for dependency tasks
There is a defined task called `sendDbusMessage` which pretty much describes 
what it does

It has three inputs: `type`, `destination` and `contents`.

On linux system running gnome related window manager, locking the screen can 
be done with a dbus call with following values: 
```
type=method_call
destination=org.gnome.ScreenSaver
contents=/org/gnome/ScreenSaver org.gnome.ScreenSaver.Lock
```

There is a mechanism to define task and in the task definition declare hard coded
inputs for dependency tasks.
This is done with a map object called `values`.

For `lockScreen` the full definition in json would be following:
```
  {
    "name": "lockScreen",
    "inputs": ["sendDbusMessage"],
    "values": {
      "type":  "method_call",
      "destination": "org.gnome.ScreenSaver",
      "contents": "/org/gnome/ScreenSaver org.gnome.ScreenSaver.Lock"
    }
  },
```

### Setting inputs completed from values for dependency tasks
TODO. BUILD_ID etc

## Python functions

`task_func` creates task with executable content (the function contents),
task name (the function name) and inputs.

The inputs will be the function parameters the way they are.

```
from taskgraph.task import task_func

@taskfunc
def myfunction(myfirstparameter, mysecondparameter)
    print(myfirstparameter)
    print(mysecondparameter)

```

## Command line arguments
Command line arguments can be specified as groups containing zero or more inputs
or optional inputs by specifying them as list of strings in `command_line_arguments`

When running the task, of the elements of command line arguments list are included
if it doesn't contain neither kind of input, it contains mandatory input or it contains
optional input which is specified among the values.
```
{
    "name": "commit",
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

## Philosophy
When looking at how things work, you might get the feeling "that could be done with a lot less keypresses", and you would be right.

The main big idea around the framework is to make things very explicit and specific and reduce the possiblity
of misunderstandings, and NOT to try to extrapolate and compute things from smaller stack of information.



## TODO
| id  | Importance      | Component        | Task                                                                                                                                                                                                                                                   | Size     | Difficulty     | Current Status
|-----|-----------------|------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------|----------------|---
| 3   | Important       | values           | Output all values related to task execution to enable result comparison/verification                                                                                                                                                                   | Smallish | Easy           | Under the hood functions exist and information available.<br/>Design elegant usage 
| 4   | Medium          | `send_smtp_mail` | Fill result from execution of the task.                                                                                                                                                                                                                | Small    | Easy           
| 5   | Medium          | dag + values     | Figure out how artefacts are removed (eg. mails in imap mailbox) on framework level.                                                                                                                                                                   | Big      | Hard
| 6   | Medium          | modules          | Create task to remove mails from imap inbox                                                                                                                                                                                                            |          |                | Depends on #5
| 7   | Very important  | results          | Compare result values to predefined set of what they should be.                                                                                                                                                                                        | Medium   | Medium
| 9   |                 |                  | Check results incrementally while running to enable long/infinite sessions                                                                                                                                                                             
| 10  | Low             | main             | Option for showing only possible tasks with current set inputs                                                                                                                                                                                       
| 11  | Very important  | dag tasks        | Name spaces based on modules for inputs. Eg. `jenkins.username`                                                                                                                                                                                        | Big      | Hard
| 12  | Quite Important | task             | Enable default input to make `tg task_name=value`
