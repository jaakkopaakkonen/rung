# Nurmi
Nurmi is a modular framework for testing and everyday operations based on simple small and independent steps on command line level.

## Ancient History
The greatest pride of Swedish naval warfare was a huge warship ship called Vasa, which sank in the Stockolm harbour after seiling only roughly 1300 meters in 1628.

In 1961 when Swedish marine archealogists decided to salvage the wreck of the ship, a group of finnish technology unversity students dived on the ship the night before and placed there a small statue of finnish runner Paavo Nurmi engraved with text in latin "Paavo Nurmi, the Great Finnish Runner".

Apparently the statue is still in the inventory of Vasa museum in Stockholm.

## Functionality
The framework is divided in two separate but equally important parts. 

The steps which describe *what* is to be done with the input values, and input values themselves which' control which steps are to be executed in which order.

### Steps
Steps are defined for now only in python code.

You can write your own or use the steps coming with the framework.

Each step has set of inputs, mandatory or optional, and a target. 

All these parameters have a string identifier or name describing the property.

# Development

## TODO
| Importance        | Component        | Task                                                                                   | Size   | Difficulty     | 
|-------------------|------------------|----------------------------------------------------------------------------------------|--------|----------------|
| Very important    | All              | Change name                                                                            | Tiny   | Very easy      |
| Quite important   | Main/ info graph | Dependencies and targets other way around                                                                                                                                                                                               | Tiny   | Very easy      |
| Quite important   | dag              | Optional inputs are not traversed from the values. If you have step with optional input which can be built from the inputs provided but the original optional input in itself is not provided, framework does not construct the optional input | Huge   | Very difficult |
| Important         | values           | Output all values related to target execution to enable result comparison/verification | Huge   | Difficult      |
| Not important yet | values           | Start and end timestamps of each target to results                                     | Medium | Medium         |
