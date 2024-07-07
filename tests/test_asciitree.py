import taskgraph.ascii

import logging
import pytest
import random


logging.basicConfig(level=logging.DEBUG, format="%(message)s")

def test_asciitree_single_item():
    contents = "halipatsuippa"
    item = taskgraph.ascii.AsciiTreeItem(contents=contents)
    assert item.get_min_width() == len(contents)
    assert item.get_max_width() == len(contents)
    assert item.get_depth() == 1
    assert item.get_row_count() == 1
    assert item.get_tree() == contents
    with pytest.raises(taskgraph.ascii.NotEnoughCols) as noc:
        item.get_tree(len(contents) - 1)


def test_asciitree_parent_longer_child():
    contentsA = "aposdifa"
    contentsB = "asdopfijapdsofja"

    itemA = taskgraph.ascii.AsciiTreeItem(
        contents=contentsA,
    )
    itemB = taskgraph.ascii.AsciiTreeItem(
        contents=contentsB,
        parent_list=itemA,
    )
    min_width = itemB.get_min_width()
    assert  min_width == len(contentsB)
    max_width = itemB.get_max_width()
    assert max_width == len(contentsA) + 1 + len(contentsB)
    assert itemB.get_depth() == 2
    assert itemB.get_row_count() == 1

    # No limit
    result = itemB.get_tree()
    assert len(result) == max_width
    assert result == contentsA + taskgraph.ascii.get_crossing_char(
        left=True,
        right=True,
    ) + contentsB

    # max_width limit
    result = itemB.get_tree(max_width)
    assert len(result) == max_width
    assert result == contentsA + taskgraph.ascii.get_crossing_char(left=True,right=True) + contentsB

    # min_width limit
    result = itemB.get_tree(min_width)
    assert result == contentsA + "───────┐\n" + contentsB

    # max_width - 1 limit
    result = itemB.get_tree(max_width - 1)
    lines = result.split('\n')
    assert len(lines) == 2
    assert len(lines[1]) == max_width - 1

    with pytest.raises(taskgraph.ascii.NotEnoughCols) as noc:
        itemB.get_tree(itemB.get_min_width() - 1)


def test_asciitree_parent_shorter_child():
    #           "1234567891123456789212345678931234567894"
    contentsA = "123456789112345678921"
    contentsB = "1234567891123456"

    itemA = taskgraph.ascii.AsciiTreeItem(
        contents=contentsA,
    )
    itemB = taskgraph.ascii.AsciiTreeItem(
        contents=contentsB,
        parent_list=itemA,
    )
    min_width = itemB.get_min_width()
    assert  min_width == len(contentsA) + 1

    max_width = itemB.get_max_width()
    assert max_width == len(contentsA) + 1 + len(contentsB)
    assert itemB.get_depth() == 2
    assert itemB.get_row_count() == 1

    # No limit
    result = itemB.get_tree()
    assert len(result) == max_width
    assert result == contentsA + taskgraph.ascii.get_crossing_char(left=True,right=True) + contentsB

    # max_width limit
    result = itemB.get_tree(max_width)
    assert len(result) == max_width
    assert result == contentsA + taskgraph.ascii.get_crossing_char(left=True,right=True) + contentsB

    # min_width limit
    result = itemB.get_tree(min_width)
    lines = result.split('\n')
    assert len(lines[0]) == len(lines[1])

    # max_width - 1 limit
    result = itemB.get_tree(max_width - 1)
    lines = result.split('\n')
    assert len(lines[1]) == max_width-1

    with pytest.raises(taskgraph.ascii.NotEnoughCols) as noc:
        itemB.get_tree(itemB.get_min_width() - 1)


def test_asciitree_two_long_parents():
    contentsParentA = "1"
    contentsParentB = "12"
    contents =        "123"

    parentA = taskgraph.ascii.AsciiTreeItem(
        contents=contentsParentA,
    )
    parentB = taskgraph.ascii.AsciiTreeItem(
        contents=contentsParentB,
    )
    item = taskgraph.ascii.AsciiTreeItem(
        contents=contents,
        parent_list=[parentA, parentB],
    )

    min_width = item.get_min_width()
    assert min_width == max(
        max(
            len(contentsParentA),
            len(contentsParentB),
        ) + 1,
        len(contents),
    )
    max_width = item.get_max_width()
    assert max_width == max(
        len(contentsParentA),
        len(contentsParentB),
    ) + 1 + len(contents)
    assert item.get_depth() == 2
    # TODO: Is the following correct?
    assert item.get_row_count() == 2
    assert item.parent_list.get_row_count() == 2

    result = item.get_tree()
    assert result == \
"1─┐\n" \
"12┴123"
    print()
    print(result)
    lines = result.split('\n')
    assert len(lines) == 2
    assert len(lines[0]) == len(contentsParentB) + 1
    assert len(lines[1]) == len(contentsParentB) + 1 + len(contents)

    result2 = item.get_tree(max_width)
    assert result == result2

    # TODO: The parent list is right aligned.
    # Instead align parent list left and align item to right
    result = item.get_tree(max_width - 1)
    print()
    print(result)
    assert result == \
"1───┐\n" \
"12──┤\n" \
"  123"
    lines = result.split('\n')
    assert len(lines) == 3
    assert len(lines[2]) == max_width - 1

    result = item.get_tree(min_width)
    print()
    print(result)
    lines = result.split('\n')
    assert len(lines) == 3
    assert len(lines[0]) == min_width
    assert len(lines[1]) == min_width


def test_asciitree_succession():
    #"1234567891123456789212345678931234567894"

    grandparent_contents = "12345678911234"
    parent_contents = "123456"
    contents = "1234567891123"

    grandparent =taskgraph.ascii.AsciiTreeItem(
        contents=grandparent_contents,
    )
    parent = taskgraph.ascii.AsciiTreeItem(
        contents=parent_contents,
        parent_list=grandparent,
    )
    item = taskgraph.ascii.AsciiTreeItem(
        contents=contents,
        parent_list=parent,
    )


    min_width = item.get_min_width()
    assert min_width == len(grandparent_contents) + 2
    result = item.get_tree(min_width)
    print()
    print(result)






    result = item.get_tree()
    max_width = item.get_max_width()
    max_width_result = item.get_tree(max_width)
    assert result == max_width_result
    print(result)

    result = item.get_tree(max_width - 1)
    print(result)


@pytest.mark.skip
def test_random_big_tree():

    def get_contents():
        contents_source = "12345678911234567892123456789312345678941234567895123456789612345678971234567898"
        contents_length = random.randint(1, 80)
        return contents_source[0:contents_length + 1]

    def get_item():
        contents = get_contents()
        print("taskgraph.ascii.AsciiTreeItem(")
        print("\tcontents=\"" + contents + '\",')
        print("\tparent_list=[")
        parent_list = get_parent_list()
        item = taskgraph.ascii.AsciiTreeItem(
            contents=contents,
            parent_list=parent_list,
        )
        print("\t],")
        print(')')
        return item


    def get_parent_list():
        parent_list = []
        for i in range(random.randint(0,3)):
            parent_list.append(
                get_item()
            )
            print(', ')
        if not parent_list:
            parent_list = None
        return parent_list

    print()
    item = get_item()
    result = item.get_tree()
    print()
    print(result)

    result = item.get_tree(item.get_min_width())
    print()
    print(result)


def test_get_subtree():
    assert taskgraph.ascii.AsciiTreeItem(
        contents="12345").get_subtree(5, taskgraph.ascii.ParentConnectionTracker()) == \
"12345"


def test_actual_tree_1():
    tree = taskgraph.ascii.AsciiTreeItem(
        contents="12",
        parent_list=[
            taskgraph.ascii.AsciiTreeItem(
                contents="1234",
                parent_list=[
                    taskgraph.ascii.AsciiTreeItem(
                        contents="1",
                        parent_list=[
                        ],
                    )
                    ,
                    taskgraph.ascii.AsciiTreeItem(
                        contents="123",
                        parent_list=[
                            taskgraph.ascii.AsciiTreeItem(
                                contents="12345",
                            )
                            ,
                        ],
                    )
                    ,
                ],
            )
            ,
        ],
    )
    min_width = tree.get_min_width()
    result = tree.get_tree(min_width)
    print()
    print(result)
    assert result == \
"1─────┐\n" \
"12345┐│\n" \
"   123┤\n" \
"   1234┐\n" \
"      12"


def test_actual_tree_3():
    tree = taskgraph.ascii.AsciiTreeItem(
        contents="123",
        parent_list=[
            taskgraph.ascii.AsciiTreeItem(
                contents="1234567",
                parent_list=[
                    taskgraph.ascii.AsciiTreeItem(
                        contents="1",
                        parent_list=[
                            taskgraph.ascii.AsciiTreeItem(
                                contents="12",
                            ),
                        ],
                    ),
                ],
            ),
            taskgraph.ascii.AsciiTreeItem(
                contents="1234",
                parent_list=[
                    taskgraph.ascii.AsciiTreeItem(
                        contents="12345",
                    ),
                    taskgraph.ascii.AsciiTreeItem(
                        contents="123456",
                    ),
                ],
            ),
        ],
    )
    result = tree.get_tree()
    print()
    print(result)
    assert result == \
"12─1─1234567┐\n" \
"12345──┐    │\n" \
"123456─┴1234┴123"
#123456789112345678


def test_actual_tree_31():
    tree = taskgraph.ascii.AsciiTreeItem(
        contents="1",
        parent_list=[
            taskgraph.ascii.AsciiTreeItem(
                contents="1234",
            ),
            taskgraph.ascii.AsciiTreeItem(
                contents="12",
                parent_list=[
                    taskgraph.ascii.AsciiTreeItem(
                        contents="123",
                    ),
                ],
            ),
        ],
    )
    width = tree.get_max_width()
    assert width == 8
    result = tree.get_tree()
    print()
    print(result)
    assert result == \
"1234──┐\n" \
"123─12┴1"
#123456789




def test_actual_tree_4():
    tree = taskgraph.ascii.AsciiTreeItem(
        contents="12345678",
        parent_list=[
            taskgraph.ascii.AsciiTreeItem(
                contents="1234567891123456789212345678931234567894123456789512345678961234567897123",
                parent_list=[
                    taskgraph.ascii.AsciiTreeItem(
                        contents="123456",
                        parent_list=[
                            taskgraph.ascii.AsciiTreeItem(
                                contents="1234567",
                            ),
                        ],
                    ),
                ],
            ),
            taskgraph.ascii.AsciiTreeItem(
                contents="12345678911234567892123456",
                parent_list=[
                    taskgraph.ascii.AsciiTreeItem(
                        contents="12345678911234567892123456789312345678941234567895123456789612345",
                    ),
                    taskgraph.ascii.AsciiTreeItem(
                        contents="123456789112345678921234567893123456789412345678951234567896123456789",
                    ),
                ],
            ),
        ],
    )
    min_width = tree.get_min_width()
    result = tree.get_tree(min_width)
    print()
    print(result)


def test_get_min_width():
    assert taskgraph.ascii.AsciiTreeItem(
        contents="1",
    ).get_min_width() == 1
    assert taskgraph.ascii.AsciiTreeItem(
        contents="12345",
    ).get_min_width() == 5
    assert taskgraph.ascii.AsciiTreeItem(
        contents="123",
        parent_list=taskgraph.ascii.AsciiTreeList(
            [
                taskgraph.ascii.AsciiTreeItem(contents="12345"),
            ]
        ),
    ).get_min_width() == 6
    assert taskgraph.ascii.AsciiTreeItem(
        contents="1234",
        parent_list=taskgraph.ascii.AsciiTreeList(
            [
                taskgraph.ascii.AsciiTreeItem(contents="1"),
                taskgraph.ascii.AsciiTreeItem(
                    contents="123",
                    parent_list=taskgraph.ascii.AsciiTreeList(
                        [
                            taskgraph.ascii.AsciiTreeItem(
                                contents="12345",
                            )
                        ]
                    )
                )
            ]
        )
    ).get_min_width() == 7

    # 12345678
    # 1─────┐
    # 12345┐│
    #    123┤
    #    1234┐
    #       12
    assert taskgraph.ascii.AsciiTreeItem(
        contents="12",
        parent_list=taskgraph.ascii.AsciiTreeList(
            [
                taskgraph.ascii.AsciiTreeItem(
                    contents="1234",
                    parent_list=taskgraph.ascii.AsciiTreeList(
                        [
                            taskgraph.ascii.AsciiTreeItem(
                                contents="1",
                            ),
                            taskgraph.ascii.AsciiTreeItem(
                                contents="123",
                                parent_list=taskgraph.ascii.AsciiTreeList(
                                    [
                                        taskgraph.ascii.AsciiTreeItem(
                                            contents="12345",
                                        )
                                    ]
                                )
                            )
                        ]
                    )
                )
            ]
        )
    ).get_min_width() == 8

    assert taskgraph.ascii.AsciiTreeItem(contents="1").get_min_width() == 1
    assert taskgraph.ascii.AsciiTreeItem(contents="12345").get_min_width() == 5
    assert taskgraph.ascii.AsciiTreeItem(
        contents="123",
        parent_list=taskgraph.ascii.AsciiTreeList(
            [
                taskgraph.ascii.AsciiTreeItem(
                    contents="12345",
                )
            ]
        )
    ).get_min_width() == 6

    # 12345678
    # 1─────┐
    # 12345┐│
    #    123┤
    #    1234
    assert taskgraph.ascii.AsciiTreeItem(
        contents="1234",
        parent_list=taskgraph.ascii.AsciiTreeList(
            [
                taskgraph.ascii.AsciiTreeItem(
                    contents="1",
                ),
                taskgraph.ascii.AsciiTreeItem(
                    contents="123",
                    parent_list=taskgraph.ascii.AsciiTreeList(
                        [
                            taskgraph.ascii.AsciiTreeItem(
                                contents="12345",
                            )
                        ]
                    )
                )
            ]
        )
    ).get_min_width() == 7

    # 12345678
    # 1─────┐
    # 12345┐│
    #    123┤
    #    1234┐
    #       12
    assert taskgraph.ascii.AsciiTreeItem(
        contents="12",
        parent_list=taskgraph.ascii.AsciiTreeList(
            [
                taskgraph.ascii.AsciiTreeItem(
                    contents="1234",
                    parent_list=taskgraph.ascii.AsciiTreeList(
                        [
                            taskgraph.ascii.AsciiTreeItem(
                                contents="1",
                            ),
                            taskgraph.ascii.AsciiTreeItem(
                                contents="123",
                                parent_list=taskgraph.ascii.AsciiTreeList(
                                    [
                                        taskgraph.ascii.AsciiTreeItem(
                                            contents="12345",
                                        )
                                    ]
                                )
                            )
                        ]
                    )
                )
            ]
        )
    ).get_min_width() == 8

    assert taskgraph.ascii.AsciiTreeItem(contents="1").get_min_width() == 1
    assert taskgraph.ascii.AsciiTreeItem(contents="12345").get_min_width() == 5

    assert taskgraph.ascii.AsciiTreeItem(
        contents="123",
        parent_list=taskgraph.ascii.AsciiTreeList(
            [
                taskgraph.ascii.AsciiTreeItem(
                    contents="12345",
                )
            ]
        )
    ).get_min_width() == 6

    assert taskgraph.ascii.AsciiTreeItem(contents="12345").get_min_width() == 5



def test_actual_tree_5():
    tree = taskgraph.ascii.AsciiTreeItem(
        contents="123",
        parent_list=taskgraph.ascii.AsciiTreeList(
            [
                taskgraph.ascii.AsciiTreeItem(
                    contents="1",
                ),
                taskgraph.ascii.AsciiTreeItem(
                    contents="12",
                    parent_list=taskgraph.ascii.AsciiTreeList(
                        [
                            taskgraph.ascii.AsciiTreeItem(
                                contents="1234",
                            )
                        ]
                    )
                )
            ]
        )
    )
    result = tree.get_tree(width=6)
    print()
    print(result)
    assert result == \
"1────┐\n" \
"1234┐│\n" \
"   12┤\n" \
"   123"
#123456


def test_actual_tree_6():
    tree = taskgraph.ascii.AsciiTreeItem(
        contents="123456789112345678921234567",
        parent_list=[
            taskgraph.ascii.AsciiTreeItem(
                contents="123456789112345678921",
                parent_list=[
                ],
            )
            ,
            taskgraph.ascii.AsciiTreeItem(
                contents="1234567891123456789212345678931234567894123456789512345678961",
                parent_list=[
                    taskgraph.ascii.AsciiTreeItem(
                        contents="1234567891",
                        parent_list=[
                            taskgraph.ascii.AsciiTreeItem(
                                contents="123456789112345678921234567893",
                                parent_list=[
                                ],
                            )
                            ,
                        ],
                    )
                    ,
                ],
            )
            ,
        ],
    )
    width = tree.get_min_width()
    result = tree.get_tree(width)
    print()
    print(result)


def test_actual_tree_7():
    tree = taskgraph.ascii.AsciiTreeItem(
        contents="1234",
        parent_list=[
            taskgraph.ascii.AsciiTreeItem(
                contents="12",
                parent_list=[
                    taskgraph.ascii.AsciiTreeItem(
                        contents="123456",
                        parent_list=[
                            taskgraph.ascii.AsciiTreeItem(
                                contents="1",
                                parent_list=[
                                    taskgraph.ascii.AsciiTreeItem(
                                        contents="12345",
                                        parent_list=[
                                        ],
                                    )
                                    ,
                                    taskgraph.ascii.AsciiTreeItem(
                                        contents="1234567",
                                        parent_list=[
                                            taskgraph.ascii.AsciiTreeItem(
                                                contents="123",
                                                parent_list=[
                                                ],
                                            )
                                            ,
                                        ],
                                    )
                                    ,
                                    taskgraph.ascii.AsciiTreeItem(
                                        contents="12345678",
                                        parent_list=[
                                        ],
                                    )
                                    ,
                                ],
                            )
                            ,
                        ],
                    )
                    ,
                ],
            )
            ,
        ],
    )
    width = tree.get_min_width()
    result = tree.get_tree(width)
    print()
    print(result)


def test_actual_tree_8():
    tree = taskgraph.ascii.AsciiTreeItem(
        contents="123456789112345678921234567893123",
        parent_list=[
            taskgraph.ascii.AsciiTreeItem(
                contents="123456789112345678921234567893",
                parent_list=[
                    taskgraph.ascii.AsciiTreeItem(
                        contents="1234567891123456789212345678931234567894123456789512345678961234567897",
                        parent_list=[
                            taskgraph.ascii.AsciiTreeItem(
                                contents="1234567891123456",
                                parent_list=[
                                    taskgraph.ascii.AsciiTreeItem(
                                        contents="12345678911234567892123456789312345678",
                                        parent_list=[
                                        ],
                                    )
                                    ,
                                    taskgraph.ascii.AsciiTreeItem(
                                        contents="1234567891123456789212345678931234567894123456789512345678961234567897123456789",
                                        parent_list=[
                                            taskgraph.ascii.AsciiTreeItem(
                                                contents="12345678911234567892123456789312",
                                                parent_list=[
                                                ],
                                            )
                                            ,
                                        ],
                                    )
                                    ,
                                    taskgraph.ascii.AsciiTreeItem(
                                        contents="12345678911234",
                                        parent_list=[
                                        ],
                                    )
                                    ,
                                ],
                            )
                            ,
                        ],
                    )
                    ,
                ],
            )
            ,
        ],
    )
    width = tree.get_min_width()
    result = tree.get_tree(width)
    print()
    print(result)



def test_parent_connection_tracker_length_after_last_newline():
    assert taskgraph.ascii.length_after_last_newline(
        "all this will be ignored\n12345───",
    ) == 8
    assert taskgraph.ascii.length_after_last_newline(
        "12345───",
    ) == 8


def test_parent_connection_tracker():
    pct = taskgraph.ascii.ParentConnectionTracker()
    result = pct.get_line_suffix("all this will be ignored\n12345───")
    print(result)
    assert result == '┐'

    result = pct.get_line_suffix("this also will be ignored\n123────")
    print(result)
    assert result == "┐│"

    result = pct.get_line_suffix("blablablapoaijgaporij\nafa\nadisfhaldsfal\n 1234567")
    print(result)
    assert result == '┤'

    result = pct.get_line_suffix("apodfiapgriug oiuhfao\n12345678")
    print(result)
    assert result == '┤'

    result = pct.get_line_suffix("apodfiapgriug oiuhfao\n        1")
    print(result)
    assert result == '┐'

    result = pct.get_line_suffix(
        "apodfiapgriug oiuhfao\n    123456",
    )
    print(result)
    assert result == '┐'

    result = pct.get_line_suffix(
        "apodfiapgriug oiuhfao\n         12",
    )
    print(result)
    assert result == '┐'


def test_get_line_suffix():
    pct = taskgraph.ascii.ParentConnectionTracker()
    result = pct.get_line_suffix(line="host─────────", width=14)
    assert result == "┐"
    assert pct.connection_columns == [14]

    result = pct.get_line_suffix(line="size", width=5)
    assert result == "┐        │"
    assert pct.connection_columns == [5, 14]

    result = pct.get_line_suffix(
        line="size┐        │\nDate",
        child_direction="right",
        width=13,
        last_item="mailBody",
    )
    assert result == "┴mailBody┴"
    assert pct.connection_columns == []
    #12345678911234567890
    #host─────────┐
    #size┐        │
    #Date┴mailBody┴


def test_sendSmtpMail():
    tree = taskgraph.ascii.AsciiTreeItem(
        contents="sendSmtpMail",
        parent_list=[
            taskgraph.ascii.AsciiTreeItem(
                contents="host",
            ),
            taskgraph.ascii.AsciiTreeItem(
                contents="mailBody",
                parent_list=[
                    taskgraph.ascii.AsciiTreeItem(
                        contents="size",
                    ),
                    taskgraph.ascii.AsciiTreeItem(
                        contents="Date",
                    ),
                ],
            ),
        ],
    )
    assert tree.get_max_width() == 26
    result = tree.get_tree()
    print(result)
    assert result == \
"host─────────┐\n" \
"size┐        │\n" \
"Date┴mailBody┴sendSmtpMail"


def test_sendSmtpMail_1():
    tree = taskgraph.ascii.AsciiTreeItem(
        contents="sendSmtpMail",
        parent_list=[
            taskgraph.ascii.AsciiTreeItem(
                contents="host",
            ),
            taskgraph.ascii.AsciiTreeItem(
                contents="mailBody",
                parent_list=[
                    taskgraph.ascii.AsciiTreeItem(
                        contents="size",
                    ),
                    taskgraph.ascii.AsciiTreeItem(
                        contents="Date",
                    ),
                ],
            ),
        ],
    )
    assert tree.get_max_width() == 26
    result = tree.get_tree()
    print(result)
    assert result == \
"host─────────┐\n" \
"size┐        │\n" \
"Date┴mailBody┴sendSmtpMail"

def test_sendSmtpMail_2():
    tree = taskgraph.ascii.AsciiTreeItem(
        contents="mailBody",
        parent_list=[
            taskgraph.ascii.AsciiTreeItem(
                contents="size",
            ),
            taskgraph.ascii.AsciiTreeItem(
                contents="Date",
            ),
        ],
    )
    connection_tracker = taskgraph.ascii.ParentConnectionTracker()
    connection_tracker.connection_columns = [13]
    result = tree.get_subtree(
        width=13,
        connection_tracker=connection_tracker,
    )
    print(result)
