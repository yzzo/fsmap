# vim: set fileencoding=utf-8 :
'''
transducers.py - metadata extractors (aka transducers) for various filetypes

Copyright (c) 2011 Alexander Holupirek <alex@holupirek.de>

ISC license
'''
import atexit
import sys
import subprocess
from subprocess import PIPE

#  Minimal (empty) result (4 lines) --> will not be returned
#  <content>
#  <page number="1" position="absolute" top="0" left="0" ...>
#  </page>
#  </content>
def extract_pdftohtml(path):
    '''Extract text from PDF file.
    path     : string. absolute path to regular (pdf) file.
    pagecount: int. number of pages in pdf file.
    return   : list. extracted text lines wrapped in <page> elements.'''
    try:
        pdftext = [ '  <content>\n' ]
        text = subprocess.check_output( ['pdftohtml', '-nodrm', '-xml'
            , '-enc', 'UTF-8', '-stdout', path])
        lines = str(text).splitlines(True)
        # strip first 4 (header) and last two lines (appendix)
        del lines[:4]
        del lines[-2:]
        has_text = False
        for line in lines:
            if line.lstrip().startswith("<text"):
                has_text = True
                # substitute common ligatures
                # www.alanwood.net/unicode/alphabetic_presentation_forms.html
                line = line.replace("ﬀ ", "ff")   # \uFB00
                line = line.replace("ﬁ", "fi")    # \uFB01
                line = line.replace("ﬂ", "fl")    # \uFB02
                line = line.replace("ﬃ  ", "ffi") # \uFB03
                line = line.replace("ﬄ  ", "ffl") # \uFB04
                pdftext.append('      ' + line)
            else:
                pdftext.append('    ' + line)
        pdftext.append('  </content>\n')
        if has_text:
            return pdftext
        else:
            return []

    except OSError as err:
        sys.stderr.write('(xdcrexiftool): pdftotext path (' + path + '): '
            + str(err) + '.\n')
        sys.exc_clear()
        return None 

class TransducerExifTool():
    '''
    Metadata extractor for various multimedia files.

        Starring the one and only, great and powerful
             *** ExifTool by Phil Harvey ***
        http://www.sno.phy.queensu.ca/~phil/exiftool/
    '''

    exiftool = None

    def __init__(self):
        '''Constructor'''
        self._init_exiftool()
        atexit.register(self._destroy_exiftool)

    def _init_exiftool(self):
        '''Create exiftool(1) process and keep it alive.'''
        try:
            self.exiftool = subprocess.Popen(
                [ 'exiftool', "-stay_open", "True", "-@", "-" ]
              , stdin=PIPE, stdout=PIPE, stderr=PIPE
            )

        except OSError as err:
            sys.stderr.write('(xdcrexiftool): Error ' + str(err) + '.\n')

    def _destroy_exiftool(self):
        '''Terminate exiftool(1) process.'''
        self.exiftool.stdin.write("-stay_open")
        self.exiftool.stdin.write("\n")
        self.exiftool.stdin.write("False")
        self.exiftool.stdin.write("\n")
        self.exiftool.stdin.flush()

    def expose_transducer(self):
        '''Report suffixes exiftool(1) can handle and a pointer to the
        handler aka extract function.'''
        # 215 suffixes in v8.60
        # $ for i in `exiftool -listf | grep -v Supp | \
        #   tr '[A-Z]' '[a-z]'`; do printf "'.$i', "; done;
        suffixes = [
            '.3fr', '.3g2', '.3gp', '.3gp2', '.3gpp', '.acfm', '.acr', '.afm',
            '.ai', '.aif', '.aifc', '.aiff', '.ait', '.amfm', '.ape', '.arw',
            '.asf', '.avi', '.bmp', '.btf', '.ciff', '.cos', '.cr2', '.crw',
            '.cs1', '.dc3', '.dcm', '.dcp', '.dcr', '.dfont', '.dib', '.dic',
            '.dicm', '.divx', '.djv', '.djvu', '.dll', '.dng', '.doc', '.docm',
            '.docx', '.dot', '.dotm', '.dotx', '.dv', '.dvb', '.dylib', '.eip',
            '.eps', '.eps2', '.eps3', '.epsf', '.erf', '.exe', '.exif', '.f4a',
            '.f4b', '.f4p', '.f4v', '.fla', '.flac', '.flv', '.fpx', '.gif',
            '.gz', '.gzip', '.hdp', '.htm', '.html', '.icc', '.icm', '.iiq',
            '.ind', '.indd', '.indt', '.itc', '.jng', '.jp2', '.jpeg', '.jpg',
            '.jpm', '.jpx', '.k25', '.kdc', '.key', '.kth', '.lnk', '.m2t',
            '.m2ts', '.m2v', '.m4a', '.m4b', '.m4p', '.m4v', '.mef', '.mie',
            '.mif', '.miff', '.mka', '.mks', '.mkv', '.mng', '.mos', '.mov',
            '.mp3', '.mp4', '.mpc', '.mpeg', '.mpg', '.mpo', '.mqv', '.mrw',
            '.mts', '.mxf', '.nef', '.newer', '.nmbtemplate', '.nrw',
            '.numbers', '.odp', '.ods', '.odt', '.ogg', '.orf', '.otf',
            '.pages', '.pbm', '.pct', '.pdf', '.pef', '.pfa', '.pfb', '.pfm',
            '.pgf', '.pgm', '.pict', '.pmp', '.png', '.pot', '.potm', '.potx',
            '.ppm', '.pps', '.ppsm', '.ppsx', '.ppt', '.pptm', '.pptx', '.ps',
            '.ps2', '.ps3', '.psb', '.psd', '.psp', '.pspframe', '.pspimage',
            '.pspshape', '.psptube', '.qif', '.qt', '.qti', '.qtif', '.ra',
            '.raf', '.ram', '.rar', '.raw', '.rif', '.riff', '.rm', '.rmvb',
            '.rpm', '.rsrc', '.rtf', '.rv', '.rw2', '.rwl', '.rwz', '.so',
            '.sr2', '.srf', '.srw', '.svg', '.swf', '.thm', '.thmx', '.tif',
            '.tiff', '.ts', '.ttc', '.ttf', '.tub', '.vob', '.vrd', '.vsd',
            '.wav', '.wdp', '.webm', '.webp', '.wma', '.wmv', '.x3f', '.xcf',
            '.xhtml', '.xla', '.xlam', '.xls', '.xlsb', '.xlsm', '.xlsx',
            '.xlt', '.xltm', '.xltx', '.xmp', '.zip'
        ]
        return (suffixes, self.extract_exiftool)

    # exiftool(1) is called with:
    #  $ exiftool -b -X --Exiftool:* --File:* --System:* <filename>
    #  0 <?xml version='1.0' encoding='UTF-8'?>
    #  1 <rdf:RDF xmlns:rdf='http://www.w3.org/1999/02/22-rdf-syntax-ns#'>
    #  2
    #  3 <rdf:Description rdf:about='/home/holu/Demo/Images/unisignet.jpg'
    #  4   xmlns:et='http://ns.exiftool.ca/1.0/' et:toolkit='Image::ExifTool 8.'
    #  5   xmlns:JFIF='http://ns.exiftool.ca/JFIF/JFIF/1.0/'
    #  6   xmlns:Ducky='http://ns.exiftool.ca/Ducky/Ducky/1.0/'
    #  7   xmlns:Adobe='http://ns.exiftool.ca/APP14/Adobe/1.0/'
    #  8   xmlns:Composite='http://ns.exiftool.ca/Composite/1.0/'>
    #  .  <JFIF:JFIFVersion>1.02</JFIF:JFIFVersion>
    #  .  <JFIF:ResolutionUnit>None</JFIF:ResolutionUnit>
    #  ...
    #  .  <FlashPix:UsedExtensionNumbers>
    #  .    <rdf:Bag>
    #  .      <rdf:li>1</rdf:li>
    #  .      <rdf:li>2</rdf:li>
    #  .    </rdf:Bag>
    #  .  </FlashPix:UsedExtensionNumbers>
    # -2 </rdf:Description>
    # -1 </rdf:RDF>
    #
    # Strategy:
    # - init output list with '<meta xmlns:rdf=...'
    # - skip first four lines from exif output (0-3)
    # - copy output (starting at 4) into output list
    # - minimal result (if no metadata is found):
    #   ['<meta xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#r"\n'
    #   , " xmlns:et='http://ns.exiftool.ca/1.0/' et:toolkit='...Tool 8.60'>\n"
    #   , '</rdf:Description>\n'
    #   , '</rdf:RDF>\n']
    # - do not return empty meta element, i.e. len(lines) == 4, but []
    # - otherwise delete last line -1 </rdf:RDF> from result
    #   and replace -2 </rdf:Description> with </meta>
    def extract_exiftool(self, path, suffix):
        '''Extracts metadata from path and constructs a result list.
        path  : string, absolute path to regular file
        return: list of strings. <meta>...</meta>'''

        self.exiftool.stdin.write("-b")
        self.exiftool.stdin.write("\n")
        self.exiftool.stdin.write("-X")
        self.exiftool.stdin.write("\n")
        self.exiftool.stdin.write("--Exiftool:*")
        self.exiftool.stdin.write("\n")
        self.exiftool.stdin.write("--File:*")
        self.exiftool.stdin.write("\n")
        self.exiftool.stdin.write("--System:*")
        self.exiftool.stdin.write("\n")
        self.exiftool.stdin.write(path)
        self.exiftool.stdin.write("\n")
        self.exiftool.stdin.write("-execute")
        self.exiftool.stdin.write("\n")
        self.exiftool.stdin.flush()

        line_count = 0
        lines = [
            '<meta xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#r"\n' ]
        while True:                                      # read from exiftool(1)
            line = self.exiftool.stdout.readline()
            if line.strip() == '{ready}':
                break
            if line_count < 4:                  # skip first lines from exiftool
                line_count += 1
                continue
            lines.append(' ' + line)
        if len(lines) <= 4:                          # no metadata from exiftool
            return []
        del lines[-2:] # has metadata, remove '</rdf:RDF>', '</rdf:Description>'
        if suffix == '.pdf':
            fulltext = extract_pdftohtml(path)
            if fulltext:
                lines.extend(fulltext)
        lines.append('</meta>\n')      # replace </rdf:Description> with </meta>
        return lines
