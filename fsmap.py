#!/usr/bin/env python
'''
fsmap(1) - display a file hierarchy in FSML

Copyright (c) 2011 Alexander Holupirek <alex@holupirek.de>

ISC license
'''
import sys
import os

# --- xml formatting and output ------------------------------------------------
def out(str_):
    '''Print string on standard output stream.'''
    sys.stdout.write(str_)

def outln(str_):
    '''Print string and a newline on standard output stream.'''
    out(str_)
    sys.stdout.write('\n')

def indent(str_, width):
    '''Pad string on the left with 2 * width spaces.'''
    ind = "".rjust(2 * width)
    return ind + str_

def escape_xml(string):
    '''Escape characters not allowed in attribute values and tag names'''
    esc = "" 
    for char in string:
        if char == '&':
            esc += '&amp;'
        elif char == '<':
            esc += '&lt;'
        elif char == '>':
            esc += '&gt;'
        elif char == '"':
            esc += '&quot;'
        else:
            esc += char
    return esc

def start_tag(tagname, atts=None):
    '''Construct a start tag string.
    tagname: string
    atts   : dict
    '''
    attributes = "" 
    if atts:
        for name in atts:
            attributes += (" " + name + "=\"" + str(atts[name]) + "\"")
    return "<{0}{1}>".format(tagname, attributes) 

def end_tag(tagname):
    '''Construct end tag string.'''
    return "</{0}>".format(tagname) 

def empty_element(tagname, atts):
    '''Construct an empty element string.
    tagname: string
    atts   : dict'''
    str_ = start_tag(tagname, atts)
    return str_[:-1] + "/>"

def add_stat_attributes(path, atts):
    '''Insert stat(2) info for path into atts dict to build XML attributes.
    path: string, absolute path to file
    atts: dictionary to insert'''
    try:
        stat_ = os.lstat(path) 
        atts['st_mode']  = oct(stat_.st_mode)
        atts['st_dev']   = str(stat_.st_dev)
        atts['st_nlink'] = str(stat_.st_nlink)
        atts['st_uid']   = str(stat_.st_uid)
        atts['st_gid']   = str(stat_.st_gid)
        atts['st_size']  = str(stat_.st_size)
        atts['st_atime'] = str(int(stat_.st_atime))
        atts['st_mtime'] = str(int(stat_.st_mtime))
        atts['st_ctime'] = str(int(stat_.st_ctime))
    except OSError as err:
        sys.stderr.write('(add_stat_attributes): ' + str(err) + '\n')

def get_default_atts(path):
    '''Create dict with name and stat(2) info for path (to build XML attributes)
    path  : string, absolute path to file
    return: atts dict'''
    value = escape_xml(os.path.basename(path))
    atts = { 'name' : value }
    add_stat_attributes(path, atts)
    return atts

# --- file traversal events ----------------------------------------------------
def pre_traversal(path):
    '''Before file hierarchy traversal begins.
    path : string, absolute path to file'''
    outln('<?xml version="1.0"?>')
    if (not os.path.isdir(path)):
        path = os.path.dirname(path)
    atts = { 'name' : escape_xml(path) }
    add_stat_attributes(path, atts)
    outln(start_tag("fsml", atts))

def post_traversal():
    '''After file hierarchy traversal.'''
    outln(end_tag("fsml"))

def visit_enter_directory(path, depth):
    '''Enter directory during file hierarchy traversal.
    path : string, absolute path to directory'''
    atts = get_default_atts(path)
    outln(indent(start_tag("dir", atts), depth))

def visit_leave_directory(depth):
    '''Leave directory during file hierarchy traversal.'''
    outln(indent(end_tag("dir"), depth))

def visit_empty_directory(path, depth):
    '''Empty directory is encountered during file hierarchy traversal.'''
    atts = get_default_atts(path)
    outln(indent(empty_element("dir", atts), depth))

def visit_link(path, depth):
    '''Symbolic or hard link is encountered during file hierarchy traversal.'''
    atts = get_default_atts(path)
    outln(indent(empty_element("link", atts), depth))

def visit_file(path, depth=0, xdcr_map=None):
    '''Regular file is encountered during file hierarchy traversal.
    path    : string, absolute path to regular file 
    depth   : depth of file in file hierarchy
    xdcr_map: dict{ suffix : extract callback function } metadata extractors'''
    atts = get_default_atts(path)
    suffix = os.path.splitext(path)[1]
    atts['suffix'] = suffix 
    if xdcr_map:
        if suffix in xdcr_map:
            outln(indent(start_tag("file", atts), depth))
            xdcr_map[suffix](path, depth + 1) # call transducer's output method
            outln(indent(end_tag("file"), depth))
            return
    outln(indent(empty_element("file", atts), depth))

def descend(dpath, depth=0, xdcr_map=None):
    '''Recursively descend into file hierachry.
    path    :  pathname to directory
    depth   : current depth in file hierarchy
    xdcr_map: metadata extractors (pass through to visit_file)'''
    try:
        dents = os.listdir(dpath)
        if depth != 0:
            if not dents:
                visit_empty_directory(dpath, depth)
                return
            visit_enter_directory(dpath, depth)
        for file_ in dents:
            path = os.path.join(dpath, file_) 
            if os.path.islink(path):
                visit_link(path, depth + 1)
            elif os.path.isdir(path):
                descend(path, depth + 1, xdcr_map)
            else:
                visit_file(path, depth + 1, xdcr_map)
        if depth != 0:
            visit_leave_directory(depth)

    except OSError as err:
        sys.stderr.write('(descend): ' + str(err) + '\n')

def walk(path):
    '''Enter file hierarchy traversal or print single file mapping.
    path    : path to file'''
    abspath = os.path.abspath(path)
    pre_traversal(abspath)
    xdcr_map = None
    level = 0
    if (os.path.isdir(abspath)):
        descend(abspath, level, xdcr_map)
    else:
        visit_file(abspath, level + 1, xdcr_map)
    post_traversal()

if __name__ == '__main__':
    VERSION = .01 
    if len(sys.argv) != 2:
        raise SystemExit(
            'fsmap(1) - display a file hierarchy in FSML (v%.2f)\n' % VERSION +
            'Usage: %s <path>' % sys.argv[0])
    walk(sys.argv[1])
