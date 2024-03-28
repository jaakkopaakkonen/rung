import taskgraph.util
import taskgraph.matrix


def test_transpose():
    assert taskgraph.util.transpose(
        [
            ["changePriority", "host"               , "radioId", ],
            [ None           , "authorizationHeader", "username",],
            [ None           , None                 , "password",],
            [ None           , "priority"           ,            ],
            [ None           , "sender"             ,            ],
            [ None           , "timestamp"          ,            ],
        ],
    ) == [
        ["radioId"  , "host"               ],
        ["username" ,                      ],
        ["password" , "authorizationHeader"],
        [ None      , "priority"           ],
        [ None      , "sender"             ],
        [ None      , "timestamp"           , "changePriority"]
    ]


def test_format_tree_box_1():
    assert taskgraph.util.format_tree_box(
        [
            ["radioId"  , "host"               ],
            ["username"],
            ["password" , "authorizationHeader"],
            [ None      , "priority"           ],
            [ None      , "sender"             ],
            [ None      , "timestamp"           , "changePriority"]
        ]
    ).strip() == \
"""
radioId──host───────────────┐               
username┐                   │               
password┴authorizationHeader┤               
         priority───────────┤               
         sender─────────────┤               
         timestamp──────────┴changePriority 
""".strip()

def test_format_tree_box_2():
    assert taskgraph.util.format_tree_box(
        [
            ["priority"  , None               ],
            ["timestamp"], None
            ["sender" , None],
            [ "authorizationHeader", None   ],
            ["host"      , "changePriority"],
        ]
    ).strip() == \
"""
radioId──host───────────────┐               
username┐                   │               
password┴authorizationHeader┤               
         priority───────────┤               
         sender─────────────┤               
         timestamp──────────┴changePriority 
""".strip()


def test_add_to_matrix():
    matrix = []
    row = 0
    column = 0
    value = "name"
    assert taskgraph.matrix.add_to_matrix(matrix, row, column, value) == [["name"]]
    column += 1
    value = "input1"
    assert taskgraph.matrix.add_to_matrix(matrix, row, column, value) == [
        ["name", "input1"]
    ]
    column += 1
    value = "input1.1"
    assert taskgraph.matrix.add_to_matrix(matrix, row, column, value) == [
        ["name", "input1", "input1.1"]
    ]
    row += 1
    value= "input1.2"
    assert taskgraph.matrix.add_to_matrix(matrix, row, column, value) == [
        ["name", "input1", "input1.1"],
        [None    , None    , "input1.2"]
    ]
    column = 1
    row += 1
    value = "input2"
    assert taskgraph.matrix.add_to_matrix(matrix, row, column, value) == [
        ["name", "input1", "input1.1"],
        [None    , None    , "input1.2"],
        [None    , "input2"],
    ]

