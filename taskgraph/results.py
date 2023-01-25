import re

# Storage which stores the result values of earlier tasks
# and thus makes them available as input values to tasks executed later on"""


store = dict()


def add(task_name=None, structure=None):
    """Store task results/inputs to the store
    """
    global store
    if task_name not in store:
        store[task_name] = dict()
    for input in structure:
        store[task_name][input] = structure[input]


def extract_values_from_logs(task_name=None, structure=None):
    values = dict()
    for log_extractor in LogValueExtractor.get_extractors(task_name):
        for task_result in structure["result"]:
            for log_chunk in task_result["log"]:
                for line in log_chunk["data"].split("\n"):
                    if line:
                        value = log_extractor.process_line(line)
                        if value is not None:
                            values[log_extractor.value_name] = value
    return values


def process_results(task_name=None, structure=None):
    add(task_name, structure)
    return extract_values_from_logs(task_name, structure)


def get(path, structure=None):
    """Get executed task results or inputs by json schema path
    """
    global store
    if structure is None:
        structure = store
    result = None
    if type(path) == str:
        elements = path.split('.')
        key = elements[0]
        if len(elements) == 1:
            try:
                result = structure[key]
            except KeyError:
                pass
        else:
            if type(structure) == list:
                # Strip out surrounding brackets [ ]
                key = re.sub(
                    r"\[([-0-9]*)\]",
                    r"\1",
                    key,
                )
                key = int(key)
            try:
                result = get(
                    '.'.join(elements[1:]),
                    structure[key],
                )
            except KeyError:
                pass
    return result


class LogValueExtractor:
    # Task name to list of extractors mapping
    extractors = dict()

    def __init__(
        self,
        task_name,
        value_name,
        line_pattern,
    ):
        self.task_name = task_name
        self.value_name = value_name
        self.pattern = re.compile(line_pattern)
        if not task_name in self.__class__.extractors:
            self.__class__.extractors[task_name] = list()
        self.__class__.extractors[task_name].append(self)

    @classmethod
    def get_extractors(cls, task_name):
        try:
            return cls.extractors[task_name]
        except:
            return []

    def process_line(self, line):
        match = self.pattern.search(line)
        if match:
            try:
                return match.group(1)
            except IndexError:
                pass

