import logging
log = logging.getLogger("glu")
log.setLevel(1)

import glu.framework
import glu.valuestack
import glu.util
import pprint


class step:
    """ Class to wrap executable parts and their arguments to
        more controlled entities to enable testing
    """

    def __init__(
        self,
        target=None,
        signature=(),
        inputs=[],
        optional_inputs=[],
    ):
        """Add and register new step to be used as input for other steps
        :param Name to be used for executing the step specifically via run_target
        :param signature: The actual executable call (function or lambda)
            and it's argument names as list or tuple of strings, or as
            dictionary of strings,
            when the input name either as target of earlier step or name
            in values is different from the argument actual argument name.
            If dictionary format is used, the argument actual argument name
            for the executable is key and input as value.
        :param inputs: Additional inputs as list, tuple or separate parameters,
            which are neccessary for this step but are not relayed to the
            signature executable call.
        """
        # The name of this step to bue used by run_target
        self.target = None
        # The actual callable implementation extracted
        # from the first parameter in signature
        self.callable_implementation = None
        # The names of arguments for the callable implementation
        self.callable_arguments = None
        # Other mandatory inputs or prerequisites for this step
        self.inputs = None
        # Optional inputs or prerequisites for this step
        self.optional_inputs = frozenset(optional_inputs)

        if type(target) != str:
            # Assume target is function
            # Dig out the functiona name and parameter names
            inputs = glu.util.get_function_name_params(target)
            new_target = inputs.pop(0)
            signature = tuple([target] + inputs)
            target = new_target
        log.warning("Registering step "+str(target))
        if inputs:
            if isinstance(inputs, tuple):
                inputs = list(inputs)
            elif not isinstance(inputs, list):
                inputs = [inputs]
        if not isinstance(signature, (list, tuple)):
            self.callable_implementation = signature
        else:
            if not signature:
                self.inputs = frozenset(inputs)
            else:
                self.callable_implementation = signature[0]
                if len(signature) == 2:
                    if isinstance(signature[1], (list, tuple)):
                        arguments = signature[1]
                        self.inputs = frozenset(inputs + arguments)
                    elif isinstance(signature[1], dict):
                        arguments = signature[1]
                        inputvalues = []
                        for inputvalue in arguments.values():
                            if inputvalue:
                                inputvalues.append(inputvalue)
                        self.inputs = frozenset(
                            inputs + inputvalues
                        ) - self.optional_inputs
                    else:
                        arguments = [signature[1]]
                        self.inputs = frozenset(
                            list(inputs) + arguments
                        ) - self.optional_inputs
                else:
                    arguments = list(signature[1:])
                    self.inputs = frozenset(
                        list(inputs) + arguments
                    ) - self.optional_inputs
                self.callable_arguments = arguments
        self.target = target
        glu.framework.add_step(self)

    def get_missing_inputs(self, *valuedicts):
        return self.inputs - glu.framework.keys_from_dicts(*valuedicts)

    def log_result(self, target, values):
        if target is None:
            target = "unnamed"
        if type(values) == str:
            if len(values) > 80:
                log.warning(target + "=\"" + values[0:80] + "\"...")
            else:
                log.warning(target + "=\"" + values+"\"")

    def run(self, *valuedicts):
        call_args = dict()
        if self.callable_arguments:
            for values in valuedicts:
                call_args.update(
                    glu.framework.argument_subset(
                        values,
                        self.callable_arguments
                    )
                )
        fulfilled_dependencies = set(call_args.keys())
        missing_dependencies = self.inputs - fulfilled_dependencies
        if missing_dependencies:
            # Not all parameters fullfilled
            log.warning("Not running " + self.target)
            log.warning(
                "Missing dependencies: " + " ".join(list(missing_dependencies))
            )
            return
        log.warning("Running " + self.target)
        log.warning("with values")
        log.warning("\n"+glu.valuestack.values_as_string(call_args))

        if self.target is None:
            result = self.callable_implementation(**call_args)
        else:
            result = self.callable_implementation(**call_args)
        self.log_result(self.target, result)
        return result

    def is_predecessor_of(self, step):
        return self.target in step.inputs

    def is_successor_of(self, step):
        return step.target in self.inputs

    def __eq__(self, other):
        if not self.target == other.target:
            return False
        if not self.inputs == other.inputs:
            return False
        if self.callable_implementation != other.callable_implementation:
            return False
        if self.callable_implementation is not None and \
            (self.callable_arguments) != set(other.callable_arguments):
            return False
        return True

    def __lt__(self, other):
        if self.target in other.inputs:
            return True
        if self.target in other.optional_inputs:
            return True
        return self.target < other.target

    def __gt__(self, other):
        if other.target in self.inputs:
            return True
        if other.target in self.optional_inputs:
            return True
        return self.target > other.target

    def __repr__(self):
        arguments = []
        for arg in self.callable_arguments:
            try:
                arguments.append(
                    repr(arg) + "=" + repr(self.callable_arguments[arg])
                )
            except:
                arguments.append(repr(arg))
        return repr(
            self.target
        ) +  "(" +  ", ".join(arguments) + ")"

    def __str__(self):
        return self.__repr__()

    def __hash__(self):
        result = hash(self.target)
        for input in self.inputs:
            result += hash(input)
        for optional_input in self.optional_inputs:
            result += hash(optional_input)
        return result

def step_func(func):
    step(func)
