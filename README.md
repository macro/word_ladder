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

Build the graph using an adjacency list since the graph should be sparse (i.e.
assumes relatively few 5-letter words have a `letter distance` of 1 with each other)

In either case, building the graph means iterating over 2-word combinations of
the word groups and adding edges for each combination.  The upper bound of n^2,
meaning every word is 1-letter distance away from the others, but on average
it's a lot less.

Traversing the graph using BFS is O(|V| + |E|), where |V| is the number of
vertices and |E| is the number of edges.

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

    real    0m0.173s
    user    0m0.158s
    sys     0m0.014s

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

    real    0m0.246s
    user    0m0.229s
    sys     0m0.016s

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

    real    0m0.360s
    user    0m0.338s
    sys     0m0.020s


####Optimizations:

A large amount of time is spent creating the word graph.  This is easiest to see with large words. Let's see if we can improve that.

* Baseline (non-threaded)
  
        $ python word_ladder.py --debug DEBUG vivification minification
        [2013-12-03 23:28:55,910][INFO][word_ladder.py:106] Reading dictionary ...
        [2013-12-03 23:28:56,029][DEBUG][word_ladder.py:32] [timing] create word_set: 0.1195s
        [2013-12-03 23:28:56,035][INFO][word_ladder.py:120] Grouping 20447 words ...
        [2013-12-03 23:28:56,934][DEBUG][word_ladder.py:32] [timing] grouping words: 0.8991s
        [2013-12-03 23:28:56,935][INFO][word_ladder.py:132] Building word graph ...
        [2013-12-03 23:28:57,166][DEBUG][word_ladder.py:32] [timing] create word graph: 0.2316s
        [2013-12-03 23:28:57,166][DEBUG][word_ladder.py:30] [timing] __init__: 1.2566s
        [2013-12-03 23:28:57,167][INFO][word_ladder.py:170] Finding word transformations in word graph (vertices=20447, edges=1804) ...
        [2013-12-03 23:28:57,167][DEBUG][word_ladder.py:30] [timing] bfs: 0.0000s
        [2013-12-03 23:28:57,167][DEBUG][word_ladder.py:30] [timing] find_transformation: 0.0002s
        Found path from `vivification` to `minification`:
          1: vivification
          2: vinification
          3: minification
        [2013-12-03 23:28:57,285][DEBUG][word_ladder.py:30] [timing] main: 1.3762s

  It takes `0.6988`s to create the word graph, about 60% of the runtime.

* Use a thread pool to build word graph

  Use [multiprocessing's ThreadPool](http://hg.python.org/cpython/file/181ced5bf0be/Lib/multiprocessing/pool.py#l713)
  The `ThreadPool` creates a Pool of N threads with jobs and results `Queue`s,
  where N is the number cpu cores on the host.

  Running with the `ThreadPool`:

        $ python word_ladder.py --debug DEBUG vivification minification
        [2013-12-03 13:34:53,591][INFO][word_ladder.py:105] Reading dictionary ...
        [2013-12-03 13:34:53,715][DEBUG][word_ladder.py:32] [timing] create word_set: 0.1242s
        [2013-12-03 13:34:53,721][INFO][word_ladder.py:119] Grouping 20447 words ...
        [2013-12-03 13:34:54,672][DEBUG][word_ladder.py:32] [timing] grouping words: 0.9510s
        [2013-12-03 13:34:54,672][INFO][word_ladder.py:127] Building word graph ...
        [2013-12-03 13:34:54,915][DEBUG][word_ladder.py:32] [timing] create word graph: 0.2422s
        [2013-12-03 13:34:54,915][DEBUG][word_ladder.py:30] [timing] __init__: 1.3242s
        [2013-12-03 13:34:54,915][INFO][word_ladder.py:154] Finding word transformations in word graph (vertices=20447, edges=1804) ...
        [2013-12-03 13:34:54,915][DEBUG][word_ladder.py:30] [timing] bfs: 0.0000s
        [2013-12-03 13:34:54,915][DEBUG][word_ladder.py:30] [timing] find_transformation: 0.0002s
        Found path from `vivification` to `minification`:
          1: vivification
          2: vinification
          3: minification
        [2013-12-03 13:34:54,915][DEBUG][word_ladder.py:30] [timing] main: 1.3259s

  It's slower than the non-threaded version!  There are two reasons for this:

    1. Function calls in Python is very expensive and the threaded
       implmentation adds function call overhead (mostly in `ThreadPool`.)
    2. The Python Global Interpreter Lock (GIL) prevents Python threads from
       executing concurrently in the interpreter. So, threads in Python don't
       have all the benefits for computationally expensive tasks that they do in
       other languages.
