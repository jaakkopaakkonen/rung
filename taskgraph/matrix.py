import taskgraph.dag


def fill_matrix_none_to_width(matrix):
    max_row_length = len(max(matrix, key=len))
    for row in matrix:
        to_pad = max_row_length - len(row)
        if to_pad:
            row += [None] * (to_pad)


def remove_trailing_none(matrix):
    row_idx = 0
    while row_idx < len(matrix):
        row = matrix[row_idx]
        column_idx = len(row) - 1
        while column_idx >= 0 and row[column_idx] is None:
            column_idx -= 1
        matrix[row_idx] = matrix[row_idx][:column_idx+1]
        row_idx += 1
    return matrix


def task_to_matrix(target):
    matrix = []
    task_to_submatrix(target, matrix, 0, 0)
    return(matrix)


def task_to_submatrix(target, matrix=[], row=0, column=0):
    """ Creates a matrix of task and it's inputs.
        [
            [target, input1, input1_of_input1],
            [None  , input2, input1_of_input2],
            [None  , None  , input2_of_input2],
            [None  , input3,...

    """
    original_row = row
    add_to_matrix(matrix, row, column, target)
    task = taskgraph.dag.get_task(target)
    if task:
        column += 1
        all_inputs = task.input_names + task.optional_input_names
        # Reverse now to maintain the correct order after transpose()
        all_inputs.reverse()
        for input in all_inputs:
            rows_processed = task_to_submatrix(input, matrix, row, column)
            if rows_processed > 1:
                row += rows_processed
            else:
                row += 1
    return row - original_row


def add_to_matrix(matrix, row, col, value):
    if len(matrix) <= row:
        matrix.append([None] * col + [value])
    else:
        if len(matrix[row]) <= col:
            matrix[row].append(value)
    return matrix
