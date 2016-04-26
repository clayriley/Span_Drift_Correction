# -*- coding: utf-8 -*-
"""
Created on Tue Apr 19 15:24:36 2016

@author: clay

MAE 2.1.0 has some issues with newlines, occasionally incrementing tag span 
counts to include them rather than ignoring them.  This script creates a new 
set of .xml files that correct this.

This script is to be run from the terminal with a directory path argument.

e.g.:

$ python fix_spans.py Some_Path/

The XML files to be adjusted have a uniform format.  There is always an XML 
field <TEXT> that contains the text for which the annotation has been created.  
Later in the file, items in the text are pointed to using a series of extent 
tags are designated by character offsets, labeled that tag's "spans".  

e.g.:

<?xml version="1.0" encoding="UTF-8" ?>
<ProjectName>
<TEXT><![CDATA[Lorem ipsum dolor sit amet, consectetur adipiscing elit.]]></TEXT>
<TAGS>
<Tag1 id="t0" spans="6~11" text="ipsum" attribute="att1"/>
<Tag2 id="t1" spans="12~17" text="dolor" attribute="att2" />
</TAGS>
</ProjectName>

"""

# correct spans in MAE-annotated xml files that have been offset due to newlines


import sys, time, re, os

# NOTE THAT THIS MAY NOT WORK IF YOU HAVE ANY SPANS THAT CROSS LINE BOUNDARIES.
# REVIEW YOUR FILES IF THIS MAY BE A CONCERN.
def run(fname):
    """
    Takes a filename as input.
    """
    
    # basic sanitation checks
    if fname[-4:].lower() != '.xml':
        print ("Not an XML file!") # honestly given the main how did this even happen
        return
    with open(fname,'r') as f:
        
        # saves as a new file each time you run it
        t=time.localtime()
        now = "_".join([str(t[0]),str(t[1]),str(t[2]),str(t[3])+str(t[4]),str(t[5])])
        outname = fname[:-4]+"-"+now+".xml"
        with open(outname, 'w') as newfile:
            
            # look through all lines, storing information about the text
            line_info = []
            char_count = 0
            in_text = False
            l = f.readline()
            t_start = re.compile(r'^<TEXT>')
            # loop until we're in the text
            while not in_text:
                # if we've hit the text, stop reading (in case text is 1 line long)
                if re.search(t_start, l):
                    in_text = True
                else:
                    # write the current line to the new file
                    newfile.write(l)
                    # and read the next
                    l = f.readline()
                    
            # loop until we're out of the text again
            t_end = re.compile(r'</TEXT>\n$')
            while in_text:
                # write the current line to the new file
                newfile.write(l)
                # this line of the text has i characters, including newlines.
                # 
                # We want to store this information on a per-line basis
                # so that we can neutralize the newlines' effects later on.
                # 
                # Note that we still subtract 1, because MAE is reading newlines 
                # as 1 char each, while Python reads them as 2 chars each.
                # 
                # For last line, we don't have to cut out the beautiful soup.
                # But for the first, we have to cut the first 15 chars.
                if char_count == 0:
                    char_count += len(l[15:]) -1
                else:
                    char_count += len(l) - 1
                # what is the char count in text up to this line?
                line_info.append(char_count) 
                # if we've hit the end of the text, stop storing line info
                if re.search(t_end, l):
                    in_text = False
                else:
                    l = f.readline()
            # sanity check
            #print ("line_info for current document: \n{}".format(line_info))
            
            # finish up the rest of the file
            s_find = re.compile(r'(?<=\bspans=")([0-9]+)~([0-9]+)')
            for l in f.readlines():
                # watch for spans to fix!
                spans = re.split(s_find, l)
                # no span?
                if len(spans) == 1:
                    # write the whole line to the new file
                    newfile.write(l)
                else:
                    # old span values:
                    old_start = int(spans[1])
                    old_end = int(spans[2])
                    # what are the new span values?
                    # we need to know which line these spans fall under 
                    # (INCLUDING the newline chars!)
                    for i in range(0,len(line_info)):
                        # the span starts in this line!
                        if old_start <= line_info[i]:
                            # set new span values including the offset!
                            # as currently designed offset == line number
                            new_start = old_start - i
                            #print("os={}, ns={}, i={}".format(old_start,new_start,i))
                            new_end = old_end - i
                            break # stop looking for the line
                        # TODO: if you want to allow for cross-line spans this is where you could make the change
                    # the line to write to the new file:
                    new_line = spans[0]+str(new_start)+'~'+str(new_end)+spans[3]
                    # write it up
                    newfile.write(new_line)

# run script
if __name__ == '__main__':
    # the directory of filenames to correct is provided in command-line input
    PATH = sys.argv[1]
    print('Please be aware that any spans that cross line boundaries may not be fixed correctly!')
    for FILENAME in os.listdir(PATH):
        if FILENAME[-4:].lower() == '.xml':
            run(os.path.join(PATH,FILENAME))