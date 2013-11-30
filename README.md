###Problem
Given two five letter words, A and B, and a dictionary of five letter words,
find a shortest transformation from A to B, such that only one letter can be
changed at a time and all intermediate words in the transformation must exist
in the dictionary.

For example, if A and B are "smart" and "brain", the result may be:

    smart
        start
        stark
        stack
        slack
        black
        blank
        bland
        brand
        braid
    brain

Your implementation should take advantage of multiple CPU cores. Please also
include test cases against your algorithm.


###Implementation Notes

Intuitively, this is a shortest path problem which a BFS (breadth-first search) algorithm could be used to solve.

Using this approach, the work of building a graph of words is bounded by the number of 5-letter words in the dictionary.

  1. trying a naive solution to build the graph:

    build the graph by comparing every single word in the dictionary to determine if its `letter distance` is 1.
    this is O(n^2) where n is the number of words in the dictionary

  2. trying word-group solution to build the graph:

    build the graph using words grouped by `word part`

      for example, group words `smart` and `start`:

        {
            '?mart': ['smart'],
            's?art': ['start'],
            'sma?t': [],
            'smar?': [],
        }

      this is O(n)

Build the graph using an adjacency list since the graph should be sparse (i.e. assumes relatively few 5-letter words have a `letter distance` of 1 with eachother)

BFS is O(|V| + |E|).

###Testing

####Run unittest using test dictionary:

    $ nosetests word_ladder.py
    Reading dictionary ...
    Grouping words ...
    Building word graph ...
    Finding word transformations ...
    .
    ----------------------------------------------------------------------
    Ran 1 test in 0.002s

    OK

####Testing using system dictionary:

  Testing 3-letter words:

    $ time python word_ladder.py one two
    Reading dictionary ...
    Grouping 1294 words ...
    Building word graph ...
    Finding word transformations in word graph (vertices=1294, edges=12711) ...
    Found path from `one` to `two`:
      1: one
      2: ona
      3: ora
      4: tra
      5: twa
      6: two

    real    0m0.461s
    user    0m0.430s
    sys     0m0.028s

  Testing 4-letter words:
    $ time python word_ladder.py four five
    Reading dictionary ...
    Grouping 4994 words ...
    Building word graph ...
    Finding word transformations in word graph (vertices=4994, edges=28297) ...
    Found path from `four` to `five`:
      1: four
      2: foud
      3: ford
      4: fore
      5: fire
      6: five

    real    0m0.612s
    user    0m0.577s
    sys     0m0.033s

  Testing 5-letter words:

    $ time python word_ladder.py smart brain
    Reading dictionary ...
    Grouping 9972 words ...
    Building word graph ...
    Finding word transformations in word graph (vertices=9972, edges=21891) ...
    Found path from `smart` to `brain`:
      1: smart
      2: slart
      3: slait
      4: slain
      5: blain
      6: brain

    real    0m1.493s
    user    0m1.417s
    sys     0m0.075s

###Optimizations
BFS could be expensive (cpu and memory) for large graphs.
