# rung
rung is a modular framework for testing and everyday operations based on simple small and independent scripts on command line level.

## Functionality
The framework is divided in two separate but equally important parts. 

The scripts aka. steps which describe *what* is to be done with the input values, and input values themselves which' control which scripts are to be executed in which order.

### Steps
Steps are defined for now only in python code.

You can write your own or use the steps coming with the framework.

Each step has set of inputs, mandatory or optional, and a target. 

All these parameters have a string identifier or name describing the property.

# Development

## TODO
| id | Importance      | Component        | Task                                                                                                                                                                                                                                                   | Size     | Difficulty     | Current Status
|----|-----------------|------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------|----------------|---
| 1  | Very important  | All              | Change name                                                                                                                                                                                                                                            | Tiny     | Very easy      
| 2  | Quite important | `dag`            | Optional inputs are not traversed from the values.<br/>If you have step with optional input which can be built from the inputs provided but the original optional input in itself is not provided,<br/>framework does not construct the optional input | Huge     | Very difficult | Status unknown.<br/>Create unittest.
| 3  | Important       | values           | Output all values related to target execution to enable result comparison/verification                                                                                                                                                                 | Smallish | Easy           | Under the hood functions exist and information available.<br/>Design elegant usage 
| 4  | Medium          | `send_smtp_mail` | Fill result from execution of the step.                                                                                                                                                                                                                | Small    | Easy           
| 7  | Low             | modules          | Create step to fetch inbox of imap box                                                                                                                                                                                                                 | Medium   | Medium         
| 5  | Medium          | dag + values     | Figure out how artefacts are removed (eg. mails in imap mailbox) on framework level.                                                                                                                                                                   | Big      | Hard
| 6  | Medium          | modules          | Create step to remove mails from imap inbox                                                                                                                                                                                                            |          |                | Depends on #5
| 7  | Very important  | results          | Compare result values to predefined set of what they should be.                                                                                                                                                                                        | Medium   | Medium
| 9  |                 |                  | Check results incrementally while running to enable long/infinite sessions                                                                                                                                                                             
|10  | Low             | main             | Option for showing only possible targets with current set inputs

