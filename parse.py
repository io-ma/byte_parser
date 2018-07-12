import re, argparse

from itertools import *
import os
from struct import *

def debug(*args):
    if 'DEBUG' in os.environ:
        print(*args)

class ImpactEvent(object):
    """Stores impact event data"""
    def __init__(self):
        self.description = ""
        #
        # Samples for each axis are kept in separate lists
        #   self.pre_samples[0] ---> x axis samples
        #   self.pre_samples[1] ---> y axis samples
        #   self.pre_samples[2] ---> z axis samples
        #
        #   self.pre_samples[[],[],[]]
        #
        self.pre_samples = [[], [], []]
        self.post_samples = [[], [], []]

class Parser(object):
    """ Parse CLI arguments"""

    def __init__(self):
        self.parser = argparse.ArgumentParser(description = "Finds raw data file, stores impact events data in a file")

    def get_parser(self):
        self.parser.add_argument('file_in', type=str, help='Raw data file')
        self.parser.add_argument('file_out', type=str, help='File out')
        return self.parser

    def run_parser(self):
        parser = self.get_parser()
        self.args = vars(parser.parse_args())
        return self.args

IMPACT, DATA, MORE_DATA = range(3)
PRE_IMPACT_DATA, POST_IMPACT_DATA = "0a", "0b"

def to_shorts(hex_data):
    """We have to translate to shorts """
    results = []
    for hexes in hex_data:
        debug(">>> %s <<<" % hexes)
        b = bytes.fromhex(hexes)
        short = unpack('h', b)
        results.append(short[0] * 0.001)
    return results

def group_hexes(data):
    """We need to group bytes by 2 """
    results = []
    for i in range(0, len(data), 2):
        y = ''.join(data[i:i+2])
        results.append(y)
    return results

def is_impact_event(event):
    """Check if line logs impact event  """
    if 'T:6-09' and 'P: 09' in event:
        # is start of impact event
        cells = event.split()
        date = " ".join((cells[0], cells[1]))
        return date
    else:
        return None

def is_start_of_impact_data(event):
    if 'T:7-0f' in event:
        return True
    else:
        return False




class ProcessingState(object):

    def __init__(self):
        self.impact_event = None
        self.looking_for = IMPACT
        self.data = []
        self.axes_found = 0
        self.axis = 0
        self.looking_for = IMPACT
        self.curr_data_len = 0
        self.data_type = PRE_IMPACT_DATA
        self.impact_events = []


    def looking_for_impact_events(self, result):
        # we're looking for impact events!
        self.impact_event = ImpactEvent()
        self.impact_event.description = result
        self.looking_for = DATA
        self.data = []
        self.axes_found = 0

    def looking_for_impact_data(self, line, splitted):
        # we're looking for impact data!

        # We found a start of impact data line

        # extract data length byte from current line
        data_length_string = splitted[3] # e.g. 'L:f2'
        data_length = int(data_length_string.split(':')[1], 16)
        debug("dl: %d\n" % data_length)

        # extract data from current line, store in data list
        if splitted[6] != self.data_type:
            raise(ValueError, "Incorrect type found")

        if splitted[5] == '00':
            self.axis = 0
            self.axes_found += 1
        elif splitted[5] == '01':
            self.axis = 1
            self.axes_found += 1
        elif splitted[5] == '02':
            self.axis = 2
            self.axes_found += 1
        else:
            raise(ValueError, "Invalid value for axis")

        debug("axes found: %d\n" % self.axes_found)

        data_bytes = splitted[7:]
        self.looking_for = MORE_DATA

        self.data.extend(data_bytes)
        self.curr_data_len = data_length


    def looking_for_more_data(self, line, splitted):
        shorts = to_shorts(group_hexes(self.data))

        if self.data_type == PRE_IMPACT_DATA:
            self.impact_event.pre_samples[self.axis].extend(shorts)
        elif self.data_type == POST_IMPACT_DATA:
            self.impact_event.post_samples[self.axis].extend(shorts)
        else:
            raise(ValueError, "Unknown data type")

        self.data = []  # empty data list

        if self.axes_found == 3:

            self.axes_found = 0

            if self.data_type == PRE_IMPACT_DATA:
                # found pre data
                debug("Found pre data, looking for post")
                self.data_type = POST_IMPACT_DATA
                self.looking_for = DATA

            elif self.data_type == POST_IMPACT_DATA:
                # found post data, done with this event
                self.looking_for = IMPACT
                self.data_type = PRE_IMPACT_DATA
                self.impact_events.append(self.impact_event)
            else:
                raise ValueError("Incorrect data type value\n")
            self.curr_data_len = 0
        else:
            self.looking_for = DATA
            self.curr_data_len = 0

    def read(self, file_in):
        with open(file_in, 'r') as input_file:

            input_data = ((line, line.split()) for line in input_file)

            for line, splitted in input_data:
                if self.looking_for == IMPACT:
                    result = is_impact_event(line)
                    if result:
                        self.looking_for_impact_events(result)
                elif self.looking_for == DATA:
                    if is_start_of_impact_data(line):
                        self.looking_for_impact_data(line, splitted)
                elif self.looking_for == MORE_DATA:
                    self.data.extend(splitted)

                    if len(self.data) >= self.curr_data_len - 2:
                        self.looking_for_more_data(line, splitted)


class EventOutput(object):

    def __init__(self, state):
        self.state = state

    def write(self, file_out):
        with open(file_out, 'w') as target:
            for event in self.state.impact_events:

                debug(event.pre_samples)
                debug('\n')
                target.write(f"{event.description}\n")
                target.write("PRE SAMPLES:\n")
                for i in range(len(event.pre_samples[0])):
                    try:
                        target.write("\t%0.2f, %0.2f, %0.2f\n" %
                                (event.pre_samples[0][i], event.pre_samples[1][i], event.pre_samples[2][i]))
                    except IndexError:
                        pass

                target.write("\n")
                target.write("POST SAMPLES:\n")
                for i in range(len(event.post_samples[0])):
                    try:
                        target.write("\t%0.2f, %0.2f, %0.2f\n" %
                                (event.post_samples[0][i], event.post_samples[1][i], event.post_samples[2][i]))
                    except IndexError:
                        pass
                target.write("\n")

def main(args):
    state = ProcessingState()
    state.read(args['file_in'])

    output = EventOutput(state)
    output.write(args['file_out'])

    debug("\033[44;77m>>>>> Success! Your file is written.\033[m")
    debug(">>>> Impact events length:", len(state.impact_events))


if __name__ == '__main__':
    parser = Parser()
    args = parser.run_parser()
    debug(args)
    main(args)
