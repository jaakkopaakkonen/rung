import copy

class StepBookkeeper:
    """Instances of this class keep track of inputs and targets of added steps
    """
    def __init__(self):
        """Initialize empty bookkeeper
        Doesn't really do anything until you add steps to it

        """
        # Dictionary containing set of all targets
        # which can be fulfilled by the inputs.
        # Key is inputs as frozenset.
        # Value is set of targets.
        self.targets_by_complete_inputs = dict()

        # Dictionary of inputs by target.
        # Key is target name
        # Value is a set of frozen sets of inputs which can make this target.
        self.inputs_of_targets = dict()

        # All targets as set in value having single input as key
        self.targets_having_input = dict()

        # All added steps
        # Key is tuple of target and frozenset of inputs
        # Value is the actual step
        self.steps = dict()

    def add(self, step):
        """ Add step to this bookkeeper
        Adding a step will enable bookkeeper to track target and inputs
        and retrieve the step based on those
        """
        target = step.target
        inputs = frozenset(step.inputs)

        # self.targets_by_complete_inputs
        if inputs not in self.targets_by_complete_inputs:
            self.targets_by_complete_inputs[inputs] = set()
        self.targets_by_complete_inputs[inputs].add(target)

        # self.inputs_of_targets
        self.inputs_of_targets[target] = inputs

        # self.targets_having_input
        for input in inputs:
            if not input in self.targets_having_input:
                self.targets_having_input[input] = set()
            self.targets_having_input[input].add(target)
        self.steps[(target, inputs)] = step

    def get_step(self, target, *inputs):
        """Retrieves the step based on it's target and all non-optional inputs
           Returns None if not found
        """
        inputs = frozenset(inputs)
        try:
            return self.steps[(target, inputs)]
        except KeyError:
            return None

    def get_inputs_to_target(self, target):
        result = []
        inputs = self.inputs_of_targets[target]
        for input in inputs:
            try:
                result.extend(self.get_inputs_to_target(input))
            except KeyError:
                result.append(input)
        result.append(target)
        return(result)

    def __copy__(self):
        new = StepBookkeeper()
        new.targets_by_complete_inputs = self.targets_by_complete_inputs
        new.inputs_of_targets = self.inputs_of_targets
        new.targets_having_input = copy.deepcopy(self.targets_having_input)
        new.steps = self.steps
        return new

class Path:
    stepbookkeeper = StepBookkeeper()
    # We might not need this
    all_paths = set()


    # @classmethod
    # def add_path(cls, path):
    #     self.all_paths.add(path)

    @classmethod
    def add_step(cls, step):
        cls.stepbookkeeper.add(step)
        paths_to_be_added = {Path(step)}
        for registered_path in cls.all_paths:
            if registered_path.step_has_earlier_inputs(step):
                paths_to_be_added.add(copy.copy(registered_path))
                registered_path.add_step_inputs(step)
            if registered_path.step_has_later_target(step):
                paths_to_be_added.add(copy.copy(registered_path))
                registered_path.add_step_target(step)
        # Add the path with only this step
        cls.all_paths.update(paths_to_be_added)

    @classmethod
    def get_path_by_target(cls, target, *inputs):
        return cls.all_paths

    # @classmethod
    # def add_set(cls, path):
    #     target = path.final_target
    #     inputs = frozenset(path.immediate_inputs)
    #     # inputs to target mapping
    #     if not inputs in cls.targets_by_complete_inputs:
    #         cls.targets_by_complete_inputs[inputs] = set()
    #     cls.targets_by_complete_inputs[inputs].update(target)
    #     # inputs of target mapping
    #     if not target in cls.inputs_of_targets:
    #         cls.inputs_of_targets[target] = set()
    #     cls.inputs_of_targets[target].update(inputs)
    #     # mapping from one single input to target
    #     for input in inputs:
    #         if not input in cls.targets_having_input:
    #             cls.targets_having_input[input] = set()
    #         cls.targets_having_input[input].update(target)
        # Are there steps which' target is input of this

    # def get_immediate_inputs_for_target(target):
    #     return inputs_of_targets[target]
    #
    # def get_targets_for_inputs(inputs):
    #     inputs = frozenset(inputs)
    #     return targets_by_complete_inputs[inputs]

    def __init__(self, step=None):
        self.stepbookkeeper = StepBookkeeper()
        self.calculated_inputs = set()
        # self.__class__.add_path(self)
        if step is not None:
            self.final_target = step.target
            self.required_inputs = set(step.inputs)

    def step_has_earlier_inputs(self, step):
        return step.target in self.required_inputs

    def step_has_later_target(self, step):
        return self.final_target in step.inputs

    def add_step_inputs(self, step):
        """ Step provides target matching path required inputs and will
        be added at the beginning of the path
        """
        self.stepbookkeeper.add(step)
        new_required_inputs = required_inputs.copy()
        new_required_inputs.remove(step.target)
        self.calculated_inputs.add(step.target)
        self.required_inputs = new_required_inputs

    def add_step_target(self, step):
        self.stepbookkeeper.add(step)
        self.calculated_inputs.add(self.final_target)
        self.final_target = step.target
    # def add_step(self, step):
    #     # Add old path
    #     self.__class__.add_path(self.copy())
    #     # Add new step to self, which has been already added
    #     self.stepbookkeeper.add(step)

        # belongs_in_path = False
        # i = 0
        # while i < len(self.steps):
        #     if step.is_predecessor_of(self.steps[i]):
        #         if i == 0:
        #             try:
        #                 self.required_inputs.remove(step.target)
        #                 self.calculated_inputs.add(step.target)
        #             except KeyError:
        #                 pass
        #         self.steps.insert(i, step)
        #         belongs_in_path = True
        #         break
        # if i == len(self.steps) and step.is_successor_of(self.steps[i-1]):
        #     self.steps.append(step)
        #     self.final_target = step.target
        #     belongs_in_path = True
        # self.final_target = set()
        # self.required_inputs = set()
        # self.calculated_inputs = set()
        # self.steps = []
        # targets = set()
        # inputs = set()
        # for step in steps:
        #     targets.add(step.target)
        #     inputs.update(step.inputs)
        # self.required_inputs = inputs - targets
        # self.final_target = (targets - inputs).pop()
        # self.calculated_inputs = targets & inputs

    def __copy__(self):
        new = Path()
        new.stepbookkeeper = copy.copy(self.stepbookkeeper)
        new.calculated_inputs = copy.copy(self.calculated_inputs)
        new.final_target = self.final_target
        new.required_inputs = copy.copy(self.required_inputs)
        return new
