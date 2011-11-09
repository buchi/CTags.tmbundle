#!/usr/bin/env python
import os.path
import sys
import re
from ctags import CTags, TagEntry
from ctags import TAG_PARTIALMATCH, TAG_IGNORECASE, TAG_FULLMATCH, TAG_OBSERVECASE

# fix up path
tm_support_path = os.path.join(os.environ["TM_SUPPORT_PATH"], "lib")
if not tm_support_path in os.environ:
    sys.path.insert(0, tm_support_path)

from webpreview import html_header, html_footer
from dialog import get_string, menu


CTAGS_KINDS_PRIORITIES = {
    '.py': {
        'c': 100,
        'f': 200,
        'm': 300,
        'v': 400,
        'i': 500,
    },
    '.zcml': {
        'n': 310, #name
        'g': 310, #profile 
        'p': 310, #permission 
        'i': 310, #id 
        's': 310, #schema 
        'h': 310, #handler 
        'm': 310, #component 
        'f': 310, #factory 
        'c': 310, #class 
        't': 310, #type 
    }
}

def priority(entry):
    """Returns the priority of an entry.
    """
    root, ext = os.path.splitext(entry[2])
    if ext in CTAGS_KINDS_PRIORITIES:
        return CTAGS_KINDS_PRIORITIES[ext][entry[1]]
    return entry[1]

def position(file_, pattern):
    """Returns the line and column number where the given pattern matches in
       the given file.
    """
    pattern = pattern[1:-1]
    pattern = pattern.replace('(', '\(')
    pattern = pattern.replace(')', '\)')
    file_obj = open(file_, 'rU')
    for line_number, line in enumerate(file_obj):
        m = re.search(pattern, line)
        if m is not None:
            return line_number, m.pos
    file_obj.close()
    return 0, 0

    
def ctags():
    """Open tags file and return ctags instance."""
    proj_dir = os.environ['TM_PROJECT_DIRECTORY']
    tag_file = os.path.normpath(os.path.join(proj_dir, '../../tags'))

    if not os.path.isfile(tag_file):
        print "Tag File not found (%s)." % tag_file
        print html_footer()
        sys.exit()

    return CTags(tag_file)


def find_tag(prompt=False):
    tags = ctags()
    if prompt:
        current_word = get_string()
    else:
        current_word = os.environ['TM_CURRENT_WORD']
    entry = TagEntry()
    res = tags.find(entry, current_word, TAG_FULLMATCH | TAG_OBSERVECASE)
    print html_header('CTags', 'Find Tag')
    if res==0:
        print "Not found."
        sys.exit()
    matches = [(entry['name'], entry['kind'], entry['file'], entry['pattern'])]
    while tags.findNext(entry):
         matches.append((entry['name'], entry['kind'], entry['file'], entry['pattern']))

    matches.sort(key=priority)

    for entry in matches:
        line, col = position(entry[2], entry[3])
        # Try to figure out package name from file path
        m = re.search(r'/([^/]+)\-[^-]+\-py\d\.\d\.egg/', entry[2])
        if m:
            package_name = m.group(1)
        else:
            m = re.search(r'/src/([^/]+)', entry[2])
            if m:
                package_name = m.group(1)
            else:
                package_name = '-'
        # #short_file = re.sub(r'(.*)\-[^-]+\-py\d\.\d\.egg/', r'\1', entry[2])
        #short_file = re.sub(r'.*/src/', '', short_file)
        print ("""<a href="txmt://open?url=file://%(file)s&line="""
              """%(line)s">%(name)s</a>"""
              """&nbsp;(%(kind)s, %(package_name)s)<pre>%(file)s:%(line)s</pre>""" % (dict(
              line=line+1,
              col=col+1,
              name=entry[0],
              kind=entry[1],
              file=entry[2],
              pattern=entry[3],
              package_name=package_name,)))

    print html_footer()

def complete_tag():
    tags = ctags()
    current_word = os.environ['TM_CURRENT_WORD']
    entry = TagEntry()
    res = tags.find(entry, current_word, TAG_PARTIALMATCH | TAG_IGNORECASE)
    if res==0:
        sys.exit()
    matches = set([entry['name']])
    while tags.findNext(entry):
        matches.add(entry['name'])
    selected = menu(list(matches))
    if selected:
        sys.stdout.write(selected)
    else:
        sys.stdout.write(current_word)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "prompt":
            find_tag(prompt=True)
        elif sys.argv[1] == "complete":
            complete_tag()
    else:
        find_tag()
