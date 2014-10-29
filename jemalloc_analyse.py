#!/usr/bin/env python

"""Given the output of jemalloc's `malloc_stats_print`, analyse and show
utilization information. Insipired by:
http://www.canonware.com/pipermail/jemalloc-discuss/2013-November/000675.html
"""

from __future__ import division

import re
import sys


def sizeof_fmt(num):
    for x in ('bytes', 'KB', 'MB', 'GB', 'TB'):
        if num < 1024.0:
            return '{:3.1f} {}'.format(num, x)
        num /= 1024.0


def main():
    with open(sys.argv[1]) if len(sys.argv) > 1 else sys.stdin as stats:
        line = stats.readline()
        while line:
            if line.startswith('Merged arenas stats:'):
                calc_bin_stats(stats, "merged")
            elif line.startswith('arenas['):
                m = re.search('arenas\[(\d+)\]', line)
                calc_bin_stats(stats, m.group(1))

            line = stats.readline()

    # Some explanation of the table(s)
    print """
    utilization = allocated / (size * regions_per_run * cur runs)
    % of small  = allocated / total allocated
    frag memory = (size * regions_per_run * cur runs) - allocated
    % of blame  = frag memory / total frag memory
"""


def calc_bin_stats(stats, arena_ID):
    FMT = '  {0:<6}{1:<10}{2:<13}{3:<9}{4:<15}{5:<8}{6:<7}{7:<8}{8:<17}{9:<8}'
    KEYS = ('size', 'ind', 'allocated', 'nmalloc', 'ndalloc',
            'nrequests', 'cur regs', 'regs', 'pgs', 'nfills', 'nflushes', 'newruns', 'reruns', 'cur runs')

    # Scan down to the table
    line = stats.readline()
    while not line.startswith('bins:'):
        line = stats.readline()
    line = stats.readline()
    if line.startswith('['):
        line = stats.readline()

    # Extract the raw stats, recording in a list of size classes.
    classes = list()
    while not line.startswith('large:'):
        fields = [int(x) for x in line.split()]
        c = dict(zip(KEYS, fields))

        # Derive some stats from each class, additional ones (see below) need
        # totals...
        try:
            c['utilization'] = c['allocated'] / (c['size'] * c['regs'] *
                                                 c['cur runs'])
        except ZeroDivisionError:
            c['utilization'] = 1
        c['frag_memory'] = ((c['size'] * c['regs'] * c['cur runs']) -
                            c['allocated'])
        classes.append(c)

        line = stats.readline()

    # Calculate totals
    total_allocated = sum([c['allocated'] for c in classes])
    total_frag_memory = sum([c['frag_memory'] for c in classes])

    print "=== Stats for Arena '{}' ===".format(arena_ID)
    print "small allocation stats:"
    print FMT.format('bin', 'size (B)', 'regions', 'pages', 'allocated (B)',
                     'cur runs', '', '% of small', '               % of blame',
                     '')
    print FMT.format('', '', 'per run', 'per run', '', '', 'utilization    ',
                     'frag memory (B)', '', '')
    print

    # Finally, calculate per-class stats which need the totals.
    for c in classes:
        c['pct_of_small'] = c['allocated'] / total_allocated
        c['pct_of_blame'] = c['frag_memory'] / total_frag_memory

        print FMT.format(c['ind'], c['size'], c['regs'], c['pgs'],
                         c['allocated'], c['cur runs'],
                         '{:.0f}%'.format(c['utilization'] * 100),
                         '{:.0f}%'.format(c['pct_of_small'] * 100),
                         c['frag_memory'],
                         '{:.0f}%'.format(c['pct_of_blame'] * 100))
    print
    print FMT.format('total', '', '', '', sizeof_fmt(total_allocated), '', '',
                     '', sizeof_fmt(total_frag_memory), '')

if __name__ == '__main__':
    main()
