"""
    A solver for word ladder puzzle.

    @author: Neil Chintomby <nchintomby@gmail.com>

    TODO:
        Optimizations (deque operations are faster, but more memory intensive)
"""
import argparse
import itertools
import functools
import time
import logging
import threading

from multiprocessing.pool import ThreadPool

from collections import deque
from contextlib import contextmanager


def timethis(what=None):

    @contextmanager
    def benchmark():
        start = time.time()
        yield
        end = time.time()
        try:
            logging.debug('[timing] {}: {:0.04f}s'.format(what.__name__, end-start))
        except AttributeError:
            logging.debug('[timing] {}: {:0.04f}s'.format(what, end-start))

    if hasattr(what, "__call__"):
        @functools.wraps(what)
        def timed(*args, **kwargs):
            with benchmark():
                return what(*args, **kwargs)
        return timed
    else:
        return benchmark()


class Graph(object):
    """ Simple adjacency list graph with breadth first search.
    """
    def __init__(self):
        self._graph = {}

    def add_edge(self, v1, v2):
        # add edge for v1
        try:
            edges = self._graph[v1]
        except KeyError:
            edges = self._graph[v1] = []
        edges.append(v2)
        # add edge for v2
        try:
            edges = self._graph[v2]
        except KeyError:
            edges = self._graph[v2] = []
        edges.append(v1)

    @timethis
    def bfs(self, start, end):
        queue = deque([[start]])
        seen = {start}
        while queue:
            path = queue.popleft()
            v1 = path[-1]
            if v1 == end:
                return path
            for v2 in self._graph.get(v1, []):
                if v2 in seen:
                    # we've queued this vertex, so it cannot be part of the
                    # shortest path here, this also prevent cycles
                    continue
                new_path = list(path)
                new_path.append(v2)
                queue.append(new_path)
                seen.add(v2)
        return None


    def __repr__(self):
        l = []
        for k,v in self._graph.iteritems():
            l.append('{}: {}'.format(k, v))
        return '\n'.join(l)


class WordGraph(Graph):
    """ Graph of words in a dictionary separated
        by a `letter distance` of 1.
    """

    @timethis
    def __init__(self, dictionary='/usr/share/dict/words', word_size=5, with_threads=False):
        # could serialize graph to reduce startup time for large dictionaries
        super(WordGraph, self).__init__()
        self.word_size = word_size
        self.with_threads = with_threads
        self.word_set = set()
        logging.info('Reading dictionary ...')
        with timethis('create word_set'):
            try:
                with open(dictionary, 'r') as f:
                    for word in f:
                        word = word.strip()
                        if len(word) != self.word_size:
                            continue
                        self.word_set.add(word.lower())
            except Exception, e:
                logging.info('Failed to load dictionary: `{}` ({})'.format(dictionary, e))
                return

        pool = ThreadPool()  # create a thread pool w/ N threads, where N is the cpu count
        logging.info('Partitioning {} words of length {} ...'.format(
                    len(self.word_set), self.word_size))
        self.words_by_part = {}
        if self.with_threads:
            self.words_by_part_lock = threading.Lock()
            with timethis('grouping words (with threads)'):
                result = pool.map_async(self._group_word_thread, list(self.word_set))
                result.wait()  # wait for all threads to finish
        else:
            with timethis('grouping words'):
                for word in list(self.word_set):
                    for i in range(self.word_size):
                        part = '{}?{}'.format(word[:i], word[i+1:])
                        try:
                            words = self.words_by_part[part]
                        except KeyError:
                            words = self.words_by_part[part] = []
                        words.append(word)

        logging.info('Building word graph ...')
        with timethis('create word graph'):
            for part,words in self.words_by_part.iteritems():
                for v1,v2 in itertools.combinations(words, 2):
                    self.add_edge(v1, v2)


    def _group_word_thread(self, word):
        with self.words_by_part_lock:
            for i in range(self.word_size):
                part = '{}?{}'.format(word[:i], word[i+1:])
                try:
                    words = self.words_by_part[part]
                except KeyError:
                    words = self.words_by_part[part] = []
                words.append(word)


    @timethis
    def find_transformation(self, start, end):
        if start not in self.word_set:
            print '`{}` not in dictionary'.format(start)
            return []
        if end not in self.word_set:
            print '`{}` not in dictionary'.format(end)
            return []

        vertex_count = len(self._graph.keys())
        edge_count = sum(len(v) for v in self._graph.itervalues())  // 2  # undirected graph represented as 2 directed edges
        logging.info('Finding word transformations in word graph '
                '(vertices={}, edges={}) ...'.format(vertex_count, edge_count))
        return self.bfs(start, end)


def test():
    wg = WordGraph(dictionary='words')
    path = wg.find_transformation("smart", "brain")
    assert path == ["smart", "start",
            "stark", "stack", "slack", "black", "blank", "bland",
            "brand", "braid", "brain"]


@timethis
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dictionary', '-d', default='/usr/share/dict/words')
    parser.add_argument('--debug', default='INFO')
    parser.add_argument('--with-threads', '-t', action='store_true', default=False)
    parser.add_argument('start')
    parser.add_argument('end')
    args = parser.parse_args()
    logging.basicConfig(
            format='[%(asctime)s][%(levelname)s][%(filename)s:%(lineno)s] %(message)s',
            level=getattr(logging, args.debug))

    if len(args.start) != len(args.end):
        print 'start word `{}`({}) is not the same length as end word `{}`({})'.format(
            args.start, len(args.start), args.end, len(args.end))
        return

    wg = WordGraph(dictionary=args.dictionary, word_size=len(args.start), with_threads=args.with_threads)
    path = wg.find_transformation(args.start, args.end)
    if not path:
        print 'No path from `{}` to `{}`'.format(args.start, args.end)
    else:
        print 'Found path from `{}` to `{}`:'.format(args.start, args.end)
        for i,word in enumerate(path, 1):
            print '  {}: {}'.format(i, word)


if __name__ == '__main__':
    main()
