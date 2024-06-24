import logging
import sys


import taskgraph.debug

@taskgraph.debug.enable_debug(logger=logging, level=logging.DEBUG)
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



class NotEnoughCols(BaseException):
    pass


class ParentConnectionTracker:
    @staticmethod
    def length_after_last_newline(string):
        pos = string.rfind('\n')
        return len(string) - pos -1

    def __init__(self):
        self.connection_columns = []

    @taskgraph.debug.enable_debug(logger=logging, level=logging.DEBUG)
    def get_line_suffix(self, line, child_direction="down"):
        line_length = self.length_after_last_newline(line)

        if line_length in self.connection_columns:
            # A parent connection ends here
            self.connection_columns.remove(line_length)
            # Insert the immediate crossing
            crossing_char_args = {
                "left": True,
                child_direction: True, # Right or down
                "up": True,
            }
        else:
            # No parent connection here
            # Insert the immediate crossing
            crossing_char_args = {
                "left": True,
                child_direction: True, # Right or down
                "up": False,
            }
        result = get_crossing_char(**crossing_char_args)

        # Calculate crossings inherited from parents
        column_idx = 0
        while column_idx < len(self.connection_columns):
            parent_column = self.connection_columns[column_idx]
            if parent_column < (line_length + len(result)):
                # Remove ended connections
                self.connection_columns.pop(column_idx)
            else:
                left = False
                if parent_column != (line_length + len(result)):
                    if child_direction == "down":
                        result += (parent_column - line_length - len(result)) * ' '
                    elif child_direction == "right":
                        left = True
                        result += (parent_column - line_length - len(result)) * get_crossing_char(left=left, right=True)
                crossing_char_args = {
                    "up": True,
                    "left": left,
                    child_direction: True,
                }
                result += get_crossing_char(**crossing_char_args)
                column_idx += 1
        if child_direction == "down":
            self.connection_columns.append(line_length)
            self.connection_columns = sorted(self.connection_columns)
        return result

    @taskgraph.debug.enable_debug(logger=logging, level=logging.DEBUG)
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
    @taskgraph.debug.enable_debug(logger=logging, level=logging.DEBUG)
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

    @taskgraph.debug.enable_debug(logger=logging, level=logging.DEBUG)
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
                    width - len(self.contents),
                    connection_tracker,
                )
                result += connection_tracker.get_line_suffix(result, "right")
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
                result += connection_tracker.get_line_suffix(result)
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

    @taskgraph.debug.enable_debug(logger=logging, level=logging.DEBUG)
    def get_tree(self, width=sys.maxsize):
        min_width = len(self.contents)
        if min_width > width:
            raise NotEnoughCols(
                "Minimun width required " +
                str(min_width) +
                ", only " +
                str(width) +
                " given."
            )
        connection_tracker = ParentConnectionTracker()
        max_width = self.get_max_width()
        if width >= max_width:
            width = max_width
        if self.parent_list:
            if width >= max_width:
                # All fits without compression
                result = self.parent_list.get_subtree(
                    width - len(self.contents),
                    connection_tracker,
                )
                result += connection_tracker.get_line_suffix(
                    result,
                    "right",
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
                result = self.parent_list.get_subtree(width, connection_tracker)
                result += connection_tracker.get_line_suffix(result)
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
    @taskgraph.debug.enable_debug(logger=logging, level=logging.DEBUG)
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

    @taskgraph.debug.enable_debug(logger=logging, level=logging.DEBUG)
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
            result = self.items[0].get_subtree(width-1, connection_tracker)
        else:
            # items_width = self.get_items_width()
            itemidx = 0
            while itemidx < len(self.items):
                item = self.items[itemidx]
                tree_piece = item.get_subtree(width - 1, connection_tracker)
                result += tree_piece
                if itemidx < len(self.items) - 1:
                    # Not the last item
                    result += connection_tracker.get_line_suffix(tree_piece)
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