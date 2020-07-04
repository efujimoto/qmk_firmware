#! /usr/bin/env python3
import json
import os
import sys
import re
import argparse

from math import floor
from os.path import dirname
from blessings import Terminal

class Heatmap(object):
    coords = [
        [
            # Row 0
            [ 4,  0], [ 4,  2], [ 2,  0], [ 1,  0], [ 2,  2], [ 3,  0], [ 3,  2],
            [ 3,  4], [ 3,  6], [ 2,  4], [ 1,  2], [ 2,  6], [ 4,  4], [ 4,  6],
        ],
        [
            # Row 1
            [ 8,  0], [ 8,  2], [ 6,  0], [ 5,  0], [ 6,  2], [ 7,  0], [ 7,  2],
            [ 7,  4], [ 7,  6], [ 6,  4], [ 5,  2], [ 6,  6], [ 8,  4], [ 8,  6],
        ],
        [
            # Row 2
            [12,  0], [12,  2], [10,  0], [ 9,  0], [10,  2], [11, 0], [     ],
            [      ], [11,  2], [10,  4], [ 9,  2], [10,  6], [12, 4], [12, 6],
        ],
        [
            # Row 3
            [17,  0], [17,  2], [15,  0], [14,  0], [15,  2], [16,  0], [13,  0],
            [13,  2], [16,  2], [15,  4], [14,  2], [15,  6], [17,  4], [17,  6],
        ],
        [
            # Row 4
            [20,  0], [20,  2], [19,  0], [18,  0], [19,  2], [], [], [], [],
            [19,  4], [18,  2], [19,  6], [20,  4], [20,  6], [], [], [], []
        ],
        [
            # Row 5
            [     ], [23,  0], [22,  2], [22,  0], [22,  4], [21,  0], [21,  2],
            [24, 0], [24,  2], [25,  0], [25,  4], [25,  2], [26,  0], [      ],
        ],
    ]

    def set_attr_at(self, block, n, attr, fn, val):
        blk = self.heatmap[block][n]
        if attr in blk:
            blk[attr] = fn(blk[attr], val)
        else:
            blk[attr] = fn(None, val)

    def coord(self, col, row):
        return self.coords[row][col]

    @staticmethod
    def set_attr(orig, new):
        return new

    def set_bg(self, coords, color):
        (block, n) = coords
        self.set_attr_at(block, n, 'c', self.set_attr, color)
        #self.set_attr_at(block, n, "g", self.set_attr, False)

    def set_tap_info(self, coords, count, cap):
        (block, n) = coords
        def _set_tap_info(o, _count, _cap):
            ns = 4 - o.count('\n')
            return o + '\n' * ns + '%.02f%%' % (float(_count) / float(_cap) * 100)

        if not cap:
            cap = 1
        self.heatmap[block][n + 1] = _set_tap_info (self.heatmap[block][n + 1], count, cap)

    @staticmethod
    def heatmap_color (v):
        colors = [ [0.3, 0.3, 1], [0.3, 1, 0.3], [1, 1, 0.3], [1, 0.3, 0.3]]
        fb = 0
        if v <= 0:
            idx1, idx2 = 0, 0
        elif v >= 1:
            idx1, idx2 = len(colors) - 1, len(colors) - 1
        else:
            val = v * (len(colors) - 1)
            idx1 = int(floor(val))
            idx2 = idx1 + 1
            fb = val - float(idx1)

        r = (colors[idx2][0] - colors[idx1][0]) * fb + colors[idx1][0]
        g = (colors[idx2][1] - colors[idx1][1]) * fb + colors[idx1][1]
        b = (colors[idx2][2] - colors[idx1][2]) * fb + colors[idx1][2]

        r, g, b = [x * 255 for x in (r, g, b)]
        return '#%02x%02x%02x' % (int(r), int(g), int(b))

    def __init__(self, layout):
        self.log = {}
        self.total = 0
        self.max_cnt = 0
        self.layout = layout

    def update_log(self, coords):
        (c, r) = coords
        if not (c, r) in self.log:
            self.log[(c, r)] = 0
        self.log[(c, r)] = self.log[(c, r)] + 1
        self.total = self.total + 1
        if self.max_cnt < self.log[(c, r)]:
            self.max_cnt = self.log[(c, r)]

    def get_dict(self):
        logs = {}
        for key in self.log.keys():
            # Can't serialize a tuple as a key, so turn it into a string
            new_key = f"{key[0]},{key[1]}"
            logs[new_key] = self.log[key]
        return {
            'max_count': self.max_cnt,
            'total': self.total,
            'logs': logs
        }

    def load_dict(self, dictionary):
        self.max_cnt = dictionary['max_count']
        self.total = dictionary['total']
        logs = dictionary['logs']
        # Turn the string keys back into tuples
        for key in logs:
            column, row = key.split(',')
            self.log[(int(column), int(row))] = logs[key]

    def get_heatmap(self, out_dir):
        heatmap_file = '{output_dir}/heatmap-layout.{layout}.json'.format(output_dir=out_dir, layout=self.layout)
        with open(heatmap_file, 'r') as file:
            self.heatmap = json.load(file)

        ## Reset colors
        for row in self.coords:
            for coord in row:
                if coord:
                    self.set_bg(coord, '#d9dae0')

        for (c, r) in self.log:
            coords = self.coord(c, r)
            b, n = coords
            cap = self.max_cnt
            if cap == 0:
                cap = 1
            v = float(self.log[(c, r)]) / cap
            self.set_bg (coords, self.heatmap_color (v))
            self.set_tap_info (coords, self.log[(c, r)], self.total)
        return self.heatmap

    def get_stats(self):
        usage = [
            # left hand
            [0, 0, 0, 0, 0],
            # right hand
            [0, 0, 0, 0, 0]
        ]
        finger_map = [0, 0, 1, 2, 3, 3, 3, 1, 1, 1, 2, 3, 4, 4]
        for (c, r) in self.log:
            if r == 5: # thumb cluster
                if c <= 6: # left side
                    usage[0][4] = usage[0][4] + self.log[(c, r)]
                else:
                    usage[1][0] = usage[1][0] + self.log[(c, r)]
            elif r == 4 and (c == 4 or c == 9): # bottom row thumb keys
                if c <= 6: # left side
                    usage[0][4] = usage[0][4] + self.log[(c, r)]
                else:
                    usage[1][0] = usage[1][0] + self.log[(c, r)]
            else:
                fc = c
                hand = 0
                if fc >= 7:
                    hand = 1
                fm = finger_map[fc]
                usage[hand][fm] = usage[hand][fm] + self.log[(c, r)]
        hand_usage = [0, 0]
        for f in usage[0]:
            hand_usage[0] = hand_usage[0] + f
        for f in usage[1]:
            hand_usage[1] = hand_usage[1] + f

        total = self.total
        if total == 0:
            total = 1
        stats = {
            "total-keys": total,
            "hands": {
                "left": {
                    "usage": round(float(hand_usage[0]) / total * 100, 2),
                    "fingers": {
                        "pinky": 0,
                        "ring": 0,
                        "middle": 0,
                        "index": 0,
                        "thumb": 0,
                    }
                },
                "right": {
                    "usage": round(float(hand_usage[1]) / total * 100, 2),
                    "fingers": {
                        "thumb": 0,
                        "index": 0,
                        "middle": 0,
                        "ring": 0,
                        "pinky": 0,
                    }
                },
            }
       }

        hmap = ['left', 'right']
        fmap = ['pinky', 'ring', 'middle', 'index', 'thumb', 'thumb', 'index', 'middle', 'ring', 'pinky']
        for hand_idx in range(len(usage)):
            hand = usage[hand_idx]
            for finger_idx in range(len(hand)):
                stats['hands'][hmap[hand_idx]]['fingers'][fmap[finger_idx + hand_idx * 5]] = round(float(hand[finger_idx]) / total * 100, 2)
        return stats

def dump_all(out_dir, heatmaps, save):
    stats = {}
    t = Terminal()
    t.clear()
    sys.stdout.write("\x1b[2J\x1b[H")

    print('{t.underline}{outdir}{t.normal}\n'.format(t=t, outdir=out_dir))

    keys = list(heatmaps.keys())
    keys.sort()
    to_log = {}
    fingers = [
        ('pinky', t.bright_magenta),
        ('ring', t.bright_cyan),
        ('middle', t.bright_blue),
        ('index', t.bright_green),
        ('thumb', t.bright_red)
    ]
    output_file_str = '{output_dir}/{layer}.json'

    for layer in keys:
        if len(heatmaps[layer].log) == 0:
            continue

        output_file = output_file_str.format(output_dir=out_dir, layer=layer)
        with open(output_file, 'w') as file:
            json.dump(heatmaps[layer].get_heatmap(out_dir), file)
        to_log[layer] = heatmaps[layer].get_dict()
        stats[layer] = heatmaps[layer].get_stats()

        left = stats[layer]['hands']['left']
        right = stats[layer]['hands']['right']

        print(
            '{t.bold}{layer}{t.normal} ({total:,} taps):'.format(
                t=t, layer=layer, total=int(stats[layer]['total-keys'])
            )
        )
        print(
            '{t.underline:12s}| left ({left:7.2%})  | right ({right:7.2%}) |{t.normal}'.format(
                t=t, left=left['usage']/100, right=right['usage']/100
            )
        )

        finger_row = ' {color}{finger:>6s}{t.white} | {left:^15.2%} | {right:^15.2%} |'
        for finger, color in fingers:
            left_val = left['fingers'][finger]/100
            right_val = right['fingers'][finger]/100
            print(finger_row.format(left=left_val, right=right_val, t=t, color=color, finger=finger))
        print()

    if save:
        save_file = '{output_dir}/heatmap_data.json'.format(output_dir=out_dir)
        with open(save_file, 'w') as file:
            json.dump(to_log, file)

def process_line(line, heatmaps, opts):
    m = re.search('KL: col=(\d+), row=(\d+), layer=(.*)', line)
    if not m:
        return False

    (column, row, layer) = (int(m.group(2)), int(m.group(1)), m.group(3))
    if (column, row) not in opts.allowed_keys:
        return False

    heatmaps[layer].update_log((column, row))

    return True

def setup_allowed_keys(opts):
    if len(opts.only_key):
        incmap={}
        for v in opts.only_key:
            m = re.search ('(\d+),(\d+)', v)
            if not m:
                continue
            (c, r) = (int(m.group(1)), int(m.group(2)))
            incmap[(c, r)] = True
    else:
        incmap={}
        for r in range(0, 6):
            for c in range(0, 14):
                incmap[(c, r)] = True

        for v in opts.ignore_key:
            m = re.search ('(\d+),(\d+)', v)
            if not m:
                continue
            (c, r) = (int(m.group(1)), int(m.group(2)))
            del(incmap[(c, r)])

    return incmap

def main(opts):
    heatmaps = {
        'Symb': Heatmap('Symb'),
        'Mdia': Heatmap('Mdia'),
        'Base': Heatmap('Base')
    }
    out_dir = opts.outdir

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    opts.allowed_keys = setup_allowed_keys(opts)

    if not opts.one_shot:
        try:
            saved_data_file = '{output_dir}/heatmap_data.json'.format(output_dir=out_dir)
            with open(saved_data_file, 'r') as file:
                data = json.load(file)
                for layer in data:
                    heatmaps[layer].load_dict(data[layer])
        except FileNotFoundError:
            pass

    raw_data_file = '{output_dir}/stamped-log'.format(output_dir=out_dir)
    with open(raw_data_file, 'r') as file:
        while True:
            line = file.readline()
            if not line:
                break
            if not process_line(line, heatmaps, opts):
                continue

    dump_all(out_dir, heatmaps, not opts.one_shot)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = 'keylog to heatmap processor')
    parser.add_argument('outdir', action = 'store',help = 'Output directory')
    parser.add_argument(
        '--ignore-key',
        dest = 'ignore_key',
        action = 'append',
        type = str,
        default = [],
        help = 'Ignore the key at position (x, y)'
    )
    parser.add_argument(
        '--only-key',
        dest = 'only_key',
        action = 'append',
        type = str,
        default = [],
        help = 'Only include key at position (x, y)'
    )
    parser.add_argument(
        '--one-shot',
        dest = 'one_shot',
        action = 'store_true',
        help = 'Do not load previous data, and do not update it, either.'
    )
    args = parser.parse_args()
    if len(args.ignore_key) and len(args.only_key):
        print ('--ignore-key and --only-key are mutually exclusive, please only use one of them!', file = sys.stderr)
        sys.exit(1)
    main(args)
