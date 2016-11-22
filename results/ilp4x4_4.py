
coords = [
    (0, 0), (1, 0), (2, 0), (3, 0),
    (0, 1), (1, 1), (2, 1), (3, 1),
    (0, 2), (1, 2), (2, 2), (3, 2),
    (0, 3), (1, 3), (2, 3), (3, 3),
]

neighbours = {
    1: {2, 5},
    2: {1, 3, 6},
    3: {2, 4, 7},
    4: {3, 8},
    5: {1, 6, 9},
    6: {2, 5, 7, 10},
    7: {3, 6, 8, 11},
    8: {4, 7, 12},
    9: {5, 10, 13},
    10: {6, 9, 11, 14},
    11: {7, 10, 12, 15},
    12: {8, 11, 16},
    13: {9, 14},
    14: {10, 13, 15},
    15: {11, 14, 16},
    16: {12, 15},
}

normal_messages = 7
fake_messages = 0
messages = 7
slots_per_second = 7

used_edges = """[{<4 4>} {<4 4>} {<4 4>} {<4 4>} {<4 4>} {<4 4>} {<4 4>} {<4 4>} {
        <4 4>} {<4 4>} {<4 4>} {<4 4>} {<4 4>} {<4 4>} {<4 4>} {
        <4 4>} {<4 4>} {<4 4>} {<4 4>} {<4 4>} {<4 4>} {<4 4>} {
        <4 4>} {<4 4>} {<4 4>} {<4 4>} {<4 4>} {<4 4>} {<4 4>} {
        <4 4>} {<4 4>} {<4 8>} {<8 8>} {<8 8>} {<8 8>} {<8 8>} {
        <8 8>} {<8 8>} {<8 8>} {<8 8>} {<8 8>} {<8 8>} {<8 8>} {
        <8 8>} {<8 8>} {<8 8>} {<8 12>} {<12 12>} {<12 12>} {
        <12 16>}]"""
broadcasted_at = """[[{1} {8} {15} {22} {29} {36} {43}]
         [{} {34} {25} {31} {37} {} {}]
         [{} {} {} {} {} {} {}]
         [{} {} {} {} {} {} {}]
         [{34} {} {} {} {} {43} {45}]
         [{} {35} {26} {43} {42} {} {}]
         [{} {} {30} {} {} {} {}]
         [{} {} {31} {} {} {} {}]
         [{38} {} {} {} {} {45} {46}]
         [{45} {37} {} {44} {43} {} {48}]
         [{46} {} {} {} {45} {} {}]
         [{48} {} {40} {} {46} {} {}]
         [{} {} {} {} {} {46} {47}]
         [{} {42} {} {46} {} {47} {48}]
         [{} {46} {} {47} {} {48} {49}]
         [{} {} {} {49} {} {} {}]]"""
