import copy
import logging
import sys


import taskgraph.debug

#@taskgraph.debug.enable_debug(logger=logging, level=logging.DEBUG)
def get_crossing_char(left=False, up=False, right=False, down=False):
    if left and not up and right and not down:
        return '─'
    if not left and up and not right and down:
        return '│'
    if left and not up and not right and down:
        return '┐'
    if left and up and right and not down:
        return '┴'
    if left and up and not right and down:
        return '┤'
    return ' '


def length_after_last_newline(string):
    pos = string.rfind('\n')
    return len(string) - pos -1


def prefix_all_lines(prefix, string):
    result = list()
    for line in string.split('\n'):
        result.append(prefix + line)
    return '\n'.join(result)


class NotEnoughCols(BaseException):
    pass


class AlignedText():

    @classmethod
    def align_texts(cls, left, right):
        if left.aligned_column < right.aligned_column:
            left.indent(right.aligned_column-left.aligned_column)
        elif right.aligned_column < left.aligned_column:
            right.indent(left.aligned_column-right.aligned_column)

    def __init__(self, text='', aligned_column=0):
        self.text = text
        self.aligned_column = aligned_column
        self.width = None

    def set_aligned_column(self, column):
        self.aligned_column = column

    def get_width(self):
        if self.width is None:
            max_length = 0
            for line in self.text.split('\n'):
                linelen = len(line)
                if linelen > max_length:
                    max_length = linelen
            self.width = max_length
        return self.width

    def indent(self, indentation, character=' '):
        self.text = prefix_all_lines(
            indentation * character,
            self.text,
        )
        self.aligned_column += indentation
        if self.width is not None:
            self.width += indentation

    def align_to(self, column, max_width=None):
        indentation = column-self.aligned_column
        if max_width is not None:
            if self.get_width() + indentation > max_width:
                indentation = max_width - self.get_width()
        self.indent(indentation)

    def __add__(self, other):
        self = copy.copy(self)
        if type(other) == type(self):
            self = copy.copy(self)
            if self.aligned_column < other.aligned_column:
                self.indent(other.aligned_column-self.aligned_column)
            elif other.aligned_column < self.aligned_column:
                other = copy.copy(other)
                other.indent(self.aligned_column-other.aligned_column)
            if self.text and \
                len(self.text) > 0 and \
                    self.text[-1] != '\n':
                self.text += '\n'
            self.text = self.text + other.text
        else:
            self.text += str(other)
            self.width = None
        return self

    def __str__(self):
        return self.text

    def __copy__(self):
        result =  AlignedText(
            text=self.text,
            aligned_column=self.aligned_column,
        )
        result.width = self.width
        return result
class AlignedTree():

    @staticmethod
    def get_asciitree(task):
        parents = []
        for input in task.input_names + task.optional_input_names:
            input_task = taskgraph.dag.get_task(input)
            if input_task:
                parents.append(AlignedTree.get_asciitree(input_task))
            else:
                parents.append(taskgraph.ascii.AsciiTreeItem(contents=input))
        return taskgraph.ascii.AsciiTreeItem(
            contents=task.name,
            parent_list=parents,
        )

    def __init__(self, task_name, width=None):
        self.task_name = task_name
        asciitree = self.get_asciitree(taskgraph.dag.get_task(task_name))
        self.contents = asciitree.get_tree(width=width)
        self.width = length_after_last_newline(self.contents)


    def __len__(self):
        return self.width

    def get_task_length(self):
        return len(self.task_name)

    def set_task_align_column(self, column):
        current_align_column = self.width - len(self.task_name)
        if current_align_column > column:
            raise NotEnoughCols()
        if current_align_column < column:
            alignment = column - current_align_column
            self.contents = prefix_all_lines(
                alignment * ' ', self.contents,
            )
            self.width += alignment


    def __str__(self):
        return self.contents
class ParentConnectionTracker:
    def __init__(self):
        self.connection_columns = []


    def add_connection_column(self, column):
        self.connection_columns.append(column)
        self.connection_columns = sorted(self.connection_columns)

    def remove_connection_column(self, column):
        self.connection_columns.remove(column)

    #@taskgraph.debug.enable_debug(logger=logging, level=logging.DEBUG)
    def get_line_suffix(
            self,
            line,
            child_direction="down",
            last_item='',
            width=None,
    ):
        result = ""
        to_be_added = None
        line_length = length_after_last_newline(line)
        if width is None or \
           (line_length + len(last_item)) < width:
            crossing_char_args = {
                "left": True,
                "up": (line_length + 1) in self.connection_columns,
                "right": False,
                "down": False,
            }
            crossing_char_args[child_direction]= True
            result += get_crossing_char(**crossing_char_args)
            line_length += 1
            if crossing_char_args["up"] and \
                not crossing_char_args["down"]:
                self.remove_connection_column(line_length)
            elif child_direction == "down":
                to_be_added = line_length

        last_item_inserted = False
        column_idx = 0
        while column_idx < len(self.connection_columns):
            # We have parent columns to process
            # The column for next parent connection
            parent_column = self.connection_columns[column_idx]
            if last_item:
                # There is still space to insert last_item
                last_item_len = len(last_item)
                if last_item_len and \
                    (line_length + last_item_len) <= min(parent_column, width):
                    # Last item fits here
                    result += last_item
                    line_length += len(last_item)
                    last_item = None
                    last_item_inserted = True
            if parent_column <= line_length:
                # Parent column connection expired
                self.remove_connection_column(parent_column)
            else:
                if parent_column == line_length + 1:
                    crossing_char_args = {
                        "up": True,
                        "right": False,
                        "down": False,
                        "left": (last_item_inserted and child_direction=="right"),
                    }
                    crossing_char_args[child_direction] = True
                    result += get_crossing_char(**crossing_char_args)
                    line_length += 1
                    if crossing_char_args["up"] and \
                        not crossing_char_args["down"]:
                        self.remove_connection_column(line_length)
                    column_idx += 1
                else:
                    # There's a gap until next parent column
                    gap = ''
                    if child_direction == "down":
                        gap = (parent_column - line_length - 1) * ' '
                    else:
                        if line_length < width:
                            gap = (parent_column - line_length - 1) * get_crossing_char(left=True, right=True)
                        column_idx += 1
                    result += gap
                    line_length += len(gap)


        # Add the parent connection created in the beginning
        if to_be_added is not None:
            self.add_connection_column(to_be_added)
        return result

    #@taskgraph.debug.enable_debug(logger=logging, level=logging.DEBUG)
    def get_padded_left_side(self, item, align="left", width=0):
        result = ""
        if align == "right":
            result += (width - len(item)) * ' '
            result += item
        else:
            result += item
            result += (width - len(item)) * get_crossing_char(
                left=True,
                right=True,
            )
        return result

    def __repr__(self):
        return "ParentConnectionTracker(" + \
            str(self.connection_columns) + ")"

class AsciiTreeItem:
    #@taskgraph.debug.enable_debug(logger=logging, level=logging.DEBUG)
    def __init__(self, contents, parent_list=None):
        self.parent_list = None
        self.contents = contents
        if parent_list:
            if isinstance(parent_list, type(self)):
                parent_list = AsciiTreeList(items=[parent_list])
            elif isinstance(parent_list, list):
                parent_list = AsciiTreeList(items=parent_list)
            self.parent_list = parent_list

    def get_min_width(self):
        result = 0
        if self.parent_list:
            result = max(
                len(self.contents),
                self.parent_list.get_min_width(),
            )
        else:
            result = len(self.contents)
        return result

    def get_max_width(self):
        max_width = 0
        if self.parent_list:
            max_width = self.parent_list.get_max_width()
        max_width += len(self.contents)
        return max_width

    def get_depth(self):
        depth = 0
        if self.parent_list:
            depth = self.parent_list.get_depth()
        return depth + 1

    def get_row_count(self):
        if self.parent_list:
            return self.parent_list.get_row_count()
        else:
            return 1

    #@taskgraph.debug.enable_debug(logger=logging, level=logging.DEBUG)
    def get_subtree(self, width=sys.maxsize, connection_tracker=None):
        min_width = len(self.contents)
        if min_width > width:
            raise NotEnoughCols(
                "Minimun width required " +
                str(min_width) +
                ", only " +
                str(width) + " given.",
            )
        max_width = self.get_max_width()
        if self.parent_list:
            if width >= max_width:
                # All fits without compression
                result = self.parent_list.get_subtree(
                    width=width-len(self.contents),
                    connection_tracker=connection_tracker,
                )
                result += connection_tracker.get_line_suffix(
                    line=result,
                    child_direction="right",
                    width=width-len(self.contents),
                )
                result += self.contents
            else:
                # Does not fit. We have to compress to several lines
                min_width = max(
                    self.parent_list.get_min_width(),
                    len(self.contents),
                )
                if min_width > width:
                    raise NotEnoughCols(
                        "Minimun width required " +
                        str(min_width) +
                        ", only " +
                        str(width) +
                        " given."
                    )
                result = self.parent_list.get_subtree(
                    width=width,
                    connection_tracker=connection_tracker,
                )
                result += connection_tracker.get_line_suffix(
                    line=result,
                    width=width,
                )
                result += '\n'
                result += connection_tracker.get_padded_left_side(
                    self.contents,
                    align="right",
                    width=width,
                )
        else:
            # No parent list
            result = connection_tracker.get_padded_left_side(
                self.contents,
                align="left",
                width=width,
            )
        return result

    #@taskgraph.debug.enable_debug(logger=logging, level=logging.DEBUG)
    def get_tree(self, width=None):
        # Check we can fit a tree in the given width

        min_width = len(self.contents)
        if width is not None:
            if min_width > width:
                raise NotEnoughCols(
                    "Minimun width required " +
                    str(min_width) +
                    ", only " +
                    str(width) +
                    " given."
                )

        # Truncate witdth argument to sensible value
        max_width = self.get_max_width()
        if width is None or \
            width >= max_width:
            width = max_width

        # Create connection tracker
        connection_tracker = ParentConnectionTracker()

        if self.parent_list:
            if width >= max_width:
                # All fits without compression

                # Get tree for the items
                result = self.parent_list.get_subtree(
                    width=width-len(self.contents),
                    connection_tracker=connection_tracker,
                )
                result += connection_tracker.get_line_suffix(
                    line=result,
                    child_direction="right",
                    width=width-len(self.contents),
                )
                result += self.contents
            else:
                # Does not fit.
                # We have to compress to several lines
                min_width = self.get_min_width()
                if min_width > width:
                    raise NotEnoughCols(
                        "Minimun width required " +
                        str(min_width) +
                        ", only " + str(width) + " given."
                    )
                result = self.parent_list.get_subtree(
                    width=width,
                    connection_tracker=connection_tracker,
                )
                result += connection_tracker.get_line_suffix(
                    line=result,
                    width=width,
                )
                result += '\n'
                result += connection_tracker.get_padded_left_side(
                    self.contents,
                    align="right",
                    width=width,
                )
        else:
            # No parent list
            result = connection_tracker.get_padded_left_side(
                self.contents,
                width=width,
            )
        return result

    def __str__(self):
        return self.contents

    def __repr__(self):
        parent_list_repr = ""
        if self.parent_list:
            parent_list_repr = ", parent_list=" + \
               repr(self.parent_list)
        return "AsciiTreeItem(contents=\"" + \
            self.contents + \
            "\"" + parent_list_repr + ')'

class AsciiTreeList:
    #@taskgraph.debug.enable_debug(logger=logging, level=logging.DEBUG)
    def __init__(self, items):
        self.items = items

    def get_min_width(self):
        max_width = 0
        for item in self.items:
            width = item.get_min_width()
            if width > max_width:
                max_width = width
        return max_width + 1

    def get_max_width(self):
        max_width = 0
        for item in self.items:
            width = item.get_max_width()
            if width > max_width:
                max_width = width
        return max_width + 1

    def get_depth(self):
        max_depth = 0
        for item in self.items:
            depth = item.get_depth()
            if depth > max_depth:
                max_depth = depth
        return max_depth

    def get_row_count(self):
        return len(self.items)

    def get_items_width(self):
        max_width= 0
        for item in self.items:
            width = len(item.contents)
            if max_width < width:
                max_width = width
        return max_width

    #@taskgraph.debug.enable_debug(logger=logging, level=logging.DEBUG)
    def get_subtree(self, width=sys.maxsize, connection_tracker=None):
        """
        Returns a subtree with set width.
        The width of last line will be `width-1`.
        Even if it is the only line
        :param width:
        :param parent_columns:
        :return:
        """
        result = ""
        if len(self.items) == 1:
            # Ony one item. Get the item subtree
            result = self.items[0].get_subtree(
                width=width-1,
                connection_tracker=connection_tracker,
            )
        else:
            # Several items
            # Loop through them and get each individual item tree
            itemidx = 0
            while itemidx < len(self.items):
                item = self.items[itemidx]
                tree_piece = item.get_subtree(
                    width=width-1,
                    connection_tracker=connection_tracker,
                )
                result += tree_piece
                if itemidx < len(self.items) - 1:
                    # Not the last item
                    result += connection_tracker.get_line_suffix(
                        line=tree_piece,
                        width=width,
                    )
                    result += '\n'
                itemidx += 1
        return result

    def __str__(self):
        return ','.join(self.items)

    def __repr__(self):
        itemlist = []
        for item in self.items:
            itemlist.append(repr(item))
        return "AsciiTreeList([" + ", ".join(itemlist) + "])"