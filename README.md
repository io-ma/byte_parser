# Byte Parser

This script needs to parse chunks of hexes, order them in 3 PRE and  3 POST event columns and write them to an ouput file. 
## Stage of the project: 
🐓

## Files

1. input_file.txt - the truncated version of the original input file. It contains the last lines, the part with the impact events I need
2. original_input.txt - the original input file, has 15000 lines or so
3. output_file.txt - the result - parsed bytes, in short formats. This data is going to be extracted into an excel sheet. This will make graph plotting more easy.
4. parser.py - the script that does the parsing

## What it does

I have a generated log of around 15000 lines. It contains all sorts of logged events.
I truncated it and kept only the part that contains the buffers I am interested in.
I search for impact events(that line should contain 2 specific strings that never change). After finding that line,
I need to split it and search for the date the inpact event occured at. 
The logged data follows.
Every impact event generates 6 buffers: 3 pre event, 3 post event.
The buffers are in hex format. I need to group hexes by 2, translate them to bytes then to shorts.
What I need my script to do is extract the date of the event, followed by the pre-impact data on 3 columns (x,y,z) then the post-impact data on 3 columns (x,y,z).
Then I need to write it all to an output file.

## How to run

Simply run the command: 

python3.6 [file_in] [file_out]

## How to test

Do:

python3.6 -m pytest test_parse.py 
