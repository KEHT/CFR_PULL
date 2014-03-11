"""Usage:
  pull.py set
  pull.py auto <from> <to> [--date=<MMDDYY>]
  pull.py move <from> <to> [--date=<MMDDYY>]
  pull.py (-h | --help)
  pull.py (-v | --version)

Options:
  set                   Executes routine with set directories and today's date
  auto                  Executes routine with specified directories and date
  move                  Copies and combines SGM files from source to dest.
  --date=<MMDDYY>       Optional date of the files to pull
  -h --help             Show this screen.
  -v --version          Show version.

"""

__author__ = 'sjohnson'

import sys
import os
import shutil
import glob
import re
import collections
from docopt import docopt
from datetime import date, datetime
from collections import defaultdict

try:
    from schema import Schema, And, Or, Use, SchemaError
except ImportError:
    exit('This example requires that `schema` data-validation library'
         ' is installed: \n    pip install schema\n'
         'https://github.com/halst/schema')


# This class provides the switch functionality we want. You only need to look at
# this if you want to know how this works. It only needs to be defined
# once, no need to muck around with its internals.
class switch(object):
    def __init__(self, value):
        self.value = value
        self.fall = False

    def __iter__(self):
        """Return the match method once, then stop"""
        yield self.match
        raise StopIteration

    def match(self, *args):
        """Indicate whether or not to enter a case suite"""
        if self.fall or not args:
            return True
        elif self.value in args:  # changed for v1.5, see below
            self.fall = True
            return True
        else:
            return False


def alpha_array():
    """Array of compiled replacement patterns for use with "alpha" function

    @rtype : list
    """
    list_regex = [
        [re.compile("\"", re.DOTALL), "'"],
        [re.compile(re.escape("  "), re.MULTILINE), " "],
        [re.compile(re.escape("  "), re.MULTILINE), " "],
        [re.compile(re.escape("</ACT>"), re.MULTILINE), ""],
        [re.compile(re.escape("</AGENCY>"), re.MULTILINE), ""],
        [re.compile(re.escape("</AGY>"), re.MULTILINE), ""],
        [re.compile(re.escape("</AMDPAR>"), re.MULTILINE), ""],
        [re.compile(re.escape("</APPENDIX>"), re.MULTILINE), ""],
        [re.compile(re.escape("</AUTH>"), re.MULTILINE), ""],
        [re.compile(re.escape("</BILCOD>"), re.MULTILINE), ""],
        [re.compile(re.escape("</BOXHD>"), re.MULTILINE), ""],
        [re.compile(re.escape("</CFR>"), re.MULTILINE), ""],
        [re.compile(re.escape("</CHED>"), re.MULTILINE), ""],
        [re.compile(re.escape("</DATE>"), re.MULTILINE), ""],
        [re.compile(re.escape("</DEPDOC>"), re.MULTILINE), ""],
        [re.compile(re.escape("</ENT>"), re.MULTILINE), ""],
        [re.compile(re.escape("</FEDREG>"), re.MULTILINE), ""],
        [re.compile(re.escape("</FP>"), re.MULTILINE), ""],
        [re.compile(re.escape("</FP-1>"), re.MULTILINE), ""],
        [re.compile(re.escape("</FP-2>"), re.MULTILINE), ""],
        [re.compile(re.escape("</GID>"), re.MULTILINE), ""],
        [re.compile(re.escape("</HD1>"), re.MULTILINE), ""],
        [re.compile(re.escape("</HD2>"), re.MULTILINE), ""],
        [re.compile(re.escape("</HD3>"), re.MULTILINE), ""],
        [re.compile(re.escape("</HED>"), re.MULTILINE), ""],
        [re.compile(re.escape("</LI>"), re.MULTILINE), ""],
        [re.compile(re.escape("</MID>"), re.MULTILINE), ""],
        [re.compile(re.escape("</NAME>"), re.MULTILINE), ""],
        [re.compile(re.escape("</NEWPART>"), re.MULTILINE), ""],
        [re.compile(re.escape("</NO>"), re.MULTILINE), ""],
        [re.compile(re.escape("</P>"), re.MULTILINE), ""],
        [re.compile(re.escape("</PART>"), re.MULTILINE), ""],
        [re.compile(re.escape("</PARTNO>"), re.MULTILINE), ""],
        [re.compile(re.escape("</RIN>"), re.MULTILINE), ""],
        [re.compile(re.escape("</ROW>"), re.MULTILINE), ""],
        [re.compile(re.escape("</RULE>"), re.MULTILINE), ""],
        [re.compile(re.escape("</RULES>"), re.MULTILINE), ""],
        [re.compile(re.escape("</SECAUTH>"), re.MULTILINE), ""],
        [re.compile(re.escape("</SECHD>"), re.MULTILINE), ""],
        [re.compile(re.escape("</SECTION>"), re.MULTILINE), ""],
        [re.compile(re.escape("</SECTNO>"), re.MULTILINE), ""],
        [re.compile(re.escape("</SIG>"), re.MULTILINE), ""],
        [re.compile(re.escape("<STARS/ >"), re.MULTILINE), "<STARS>"],
        [re.compile(re.escape("<STARS />"), re.MULTILINE), "<STARS>"],
        [re.compile(re.escape("<STARS/>"), re.MULTILINE), "<STARS>"],
        [re.compile(re.escape("</STARS>"), re.MULTILINE), ""],
        [re.compile(re.escape("</SUBAGY>"), re.MULTILINE), ""],
        [re.compile(re.escape("</SUBJECT>"), re.MULTILINE), ""],
        [re.compile(re.escape("</SUBPART>"), re.MULTILINE), ""],
        [re.compile(re.escape("</TDESC>"), re.MULTILINE), ""],
        [re.compile(re.escape("</TITLE>"), re.MULTILINE), ""],
        [re.compile(re.escape("</TTITLE>"), re.MULTILINE), ""],
        [re.compile(re.escape("</UNITNAME>"), re.MULTILINE), ""],
        [re.compile(re.escape("</VOL>"), re.MULTILINE), ""],
        [re.compile("\"", re.DOTALL), "'"],
        [re.compile("\n\n", re.DOTALL), "\n"],
        [re.compile("\s*\n\s*", re.DOTALL), "\n"],
        [re.compile("\n\s\n", re.DOTALL), "\n"],
        [re.compile("\n\?>", re.DOTALL), "?>"],
        [re.compile("\:\s\n<", re.DOTALL), ":\n<"],
        [re.compile(re.escape("<RULE>"), re.MULTILINE), "\n\n<RULE>"],
        [re.compile("<\?USGPO Galley End:\s*\?>", re.MULTILINE), ""],
        [re.compile(re.escape("<PART>"), re.MULTILINE), "\n<PART>"],
        [re.compile("\n\n<PART>", re.MULTILINE), "\n<PART>"],
        [re.compile(re.escape("<SECTION>"), re.MULTILINE), "\n<SECTION>"],
        [re.compile("\n\n<SECTION>", re.MULTILINE), "\n<SECTION>"],
        [re.compile(re.escape(" <SUBJECT>"), re.MULTILINE), "<SUBJECT>"],
        [re.compile(re.escape("<SUBJECT> "), re.MULTILINE), "<SUBJECT>"],
        [re.compile("\n<SUBJECT>", re.MULTILINE), "<SUBJECT>"],
        [re.compile("\n</", re.DOTALL), "</"],
        [re.compile("\.\s\n<", re.MULTILINE), ".\n<"],
        [re.compile(re.escape(" &thnsp;"), re.MULTILINE), "&thnsp;"],
        [re.compile(re.escape("&thnsp; "), re.MULTILINE), "&thnsp;"],
        [re.compile("\. \n\n", re.MULTILINE), ".\n"],
        [re.compile(re.escape(". </EXTRACT>"), re.MULTILINE), ".</EXTRACT>"],
        [re.compile(re.escape(". </NOTE>"), re.MULTILINE), ".</NOTE>"],
        [re.compile(re.escape(" </REGTEXT>"), re.MULTILINE), "</REGTEXT>"],
        [re.compile("\n</REGTEXT>", re.MULTILINE), "</REGTEXT>"],
        [re.compile(re.escape("<Q P='04'></REGTEXT>"), re.MULTILINE), "</REGTEXT>"],
        [re.compile(re.escape("<Q P='03'></REGTEXT>"), re.MULTILINE), "</REGTEXT>"],
        [re.compile(re.escape("<Q P='02'></REGTEXT>"), re.MULTILINE), "</REGTEXT>"],
        [re.compile(re.escape("<STARS> "), re.MULTILINE), "<STARS>"],
        [re.compile("\n<STARS>", re.DOTALL), "<STARS>"],
        [re.compile(re.escape("</REGTEXT><STARS>"), re.MULTILINE), "<STARS></REGTEXT>"],
        [re.compile(re.escape("</GPOTABLE></REGTEXT>"), re.MULTILINE), "</GPOTABLE>\n</REGTEXT>"],
        [re.compile("\n</CONTENTS>", re.MULTILINE), "</CONTENTS>"],
        [re.compile(re.escape(". </CONTENTS>"), re.MULTILINE), ".</CONTENTS>"],
        [re.compile(re.escape("<STARS>"), re.MULTILINE), "\n<STARS>"],
        [re.compile("\n\n<STARS>", re.MULTILINE), "\n<STARS>"],
        [re.compile("<STARS>\n</REGTEXT>", re.MULTILINE), "<STARS></REGTEXT>"],
        [re.compile(re.escape("<REGTEXT"), re.MULTILINE), "\n<REGTEXT"],
        [re.compile(re.escape("<LSTSUB>"), re.MULTILINE), "<LSTSUB>"],
        [re.compile(re.escape("<EFFDATE>"), re.MULTILINE), "<EFFDATE>"],
        [re.compile(":\n<P>", re.MULTILINE), ":<P>"],
        [re.compile("^<PART><HED>.*\n\n{0,2}(?=<AMDPAR>)", re.MULTILINE), ""],
        [re.compile("^<SUBPART><HED>.*\n\n{0,2}(?=<AMDPAR>)", re.MULTILINE), ""],
        [re.compile("^<Q P=.*\n\n{0,2}(?=<AMDPAR>)", re.MULTILINE), ""],
        [re.compile("<SUBCHAP><HED>.*\n\n{0,2}(?=<AMDPAR>)", re.MULTILINE), ""],
        [re.compile("\s*<AMDPAR>", re.MULTILINE), "\n<P>"],
        # [re.compile("\n\n<AMDPAR>", re.MULTILINE), "\n<P>"],
        [re.compile("<EXTRACT>\n", re.DOTALL), "<EXTRACT>"],
        [re.compile(re.escape("<SECTNO>&"), re.MULTILINE), "\n<SECTNO>&"],
        [re.compile("\n\n<SECTNO>&", re.MULTILINE), "\n<SECTNO>&"],
        [re.compile(" \n<HED>", re.MULTILINE), "\n<HED>"],
        [re.compile("\n<HED>", re.MULTILINE), "<HED>"],
        [re.compile(re.escape(" <P>"), re.MULTILINE), "<P>"],
        [re.compile(re.escape("<P>"), re.MULTILINE), "\n<P>"],
        [re.compile("\n\n<P>", re.MULTILINE), "\n<P>"],
        [re.compile(re.escape("><E T='04'>Authority:</E>"), re.MULTILINE), ">Authority:"],
        [re.compile(re.escape("&Prime;"), re.MULTILINE), "&sec;"],
        [re.compile(re.escape("&prime;"), re.MULTILINE), "&min;"],
        [re.compile(re.escape("&fnl;"), re.MULTILINE), ""],
        [re.compile(re.escape("<ROW"), re.MULTILINE), "\n<ROW"],
        [re.compile("\n\n<ROW", re.MULTILINE), "\n<ROW"],
        [re.compile(re.escape("<LI>"), re.MULTILINE), "\n<LI>"],
        [re.compile("\n\n<LI>", re.MULTILINE), "\n<LI>"],
        [re.compile("\"", re.MULTILINE), "'"],
        [re.compile(re.escape(",tp0,i1"), re.MULTILINE), ""],
        [re.compile(re.escape(",i1'"), re.MULTILINE), "'"],
        [re.compile(re.escape("L1,i1"), re.MULTILINE), "L1"],
        [re.compile(re.escape("L2,i1"), re.MULTILINE), "L2"],
        [re.compile(re.escape("``"), re.MULTILINE), "&ldquo;"],
        [re.compile(re.escape("''"), re.MULTILINE), "&rdquo"],
        [re.compile(re.escape("<E T='7462'>"), re.MULTILINE), "<E T='03'>"],
        [re.compile(re.escape("&euro;"), re.MULTILINE), "!l*f"],
        [re.compile(re.escape("##"), re.MULTILINE), "\n\n"],
        [re.compile(re.escape("<E T='22'>"), re.MULTILINE), "<E T='52'>"],
        [re.compile(re.escape(", </E>"), re.MULTILINE), ",</E> "],
        [re.compile(re.escape(" </E> "), re.MULTILINE), "</E> "],
        [re.compile(re.escape(". </E>"), re.MULTILINE), ".</E> "],
        [re.compile(re.escape(" </E>"), re.MULTILINE), "</E> "],
        [re.compile(re.escape(" &emsp;"), re.MULTILINE), "&emsp;"],
        [re.compile(re.escape("&emsp; "), re.MULTILINE), "&emsp;"],
        [re.compile(re.escape(" &ensp;"), re.MULTILINE), "&ensp;"],
        [re.compile(re.escape("&ensp; "), re.MULTILINE), "&ensp;"],
        [re.compile("\n<HED", re.MULTILINE), "<HED"],
        [re.compile(" \n<P>", re.MULTILINE), "\n<P>"],
        [re.compile(re.escape(" <P>"), re.MULTILINE), "<P>"],
        [re.compile(re.escape("<P> "), re.MULTILINE), "<P>"],
        [re.compile("\n<P>\n", re.MULTILINE), "\n<P>"],
        [re.compile(re.escape(":<P>("), re.MULTILINE), ":\n<P>("],
        [re.compile(re.escape("&plus;"), re.MULTILINE), "+"],
        [re.compile(re.escape("&equal;"), re.MULTILINE), "="],
        [re.compile(re.escape("&equals;"), re.MULTILINE), "="],
        [re.compile(re.escape("&sol;"), re.MULTILINE), "/"],
        [re.compile(re.escape("+/&minus;"), re.MULTILINE), "&plusmn;"],
        [re.compile(re.escape("+/-"), re.MULTILINE), "&plusmn;"],
        [re.compile(re.escape("&commat;"), re.MULTILINE), "@"],
        [re.compile(re.escape("&apos;"), re.MULTILINE), "'"],
        [re.compile(re.escape("&ast;"), re.MULTILINE), "*"],
        [re.compile(re.escape("&percnt;"), re.MULTILINE), "%"],
        [re.compile(re.escape("&prime;"), re.MULTILINE), "&min;"],
        [re.compile(re.escape("&agr;"), re.MULTILINE), "&alpha;"],
        [re.compile(re.escape("&hairsp;&hairsp;"), re.MULTILINE), "&thnsp;"],
        [re.compile(re.escape("&hairsp;"), re.MULTILINE), ""],
        [re.compile(re.escape("&dollar;"), re.MULTILINE), "$"],
        [re.compile(re.escape("&hyphen;"), re.MULTILINE), "-"],
        [re.compile(re.escape("&mu;"), re.MULTILINE), "&micro;"],
        [re.compile("&fnl;\n<FNP>", re.MULTILINE), " "],
        [re.compile("&fnl;\n<FP>", re.MULTILINE), " "],
        [re.compile(re.escape("<FNP>"), re.MULTILINE), ""],
        [re.compile(re.escape("'L2,tp0,i1'"), re.MULTILINE), "'L2'"],
        [re.compile(re.escape(",i1'"), re.MULTILINE), "'"],
        [re.compile("\n<ENT", re.MULTILINE), "<ENT"],
        [re.compile("<ENT>\s\n", re.MULTILINE), "<ENT>\n"],
        [re.compile("<ENT>\n", re.MULTILINE), ""],
        [re.compile(re.escape("<FNC>"), re.MULTILINE), ""],
        [re.compile(re.escape("&fnl;"), re.MULTILINE), ""],
        [re.compile(re.escape("&rsquo;"), re.MULTILINE), "'"],
        [re.compile(re.escape("&lsquo;"), re.MULTILINE), "`"],
        [re.compile(re.escape("<Q"), re.MULTILINE), "\n<Q"],
        [re.compile("\n\n<Q", re.MULTILINE), "\n<Q"],
        [re.compile(re.escape("&lowbar;"), re.MULTILINE), "&lowbarm;"],
        [re.compile(re.escape("<E T='72'>&lowbarm;"), re.MULTILINE), "&lowbarm;"],
        [re.compile(re.escape("&lowbarm;</E>"), re.MULTILINE), "&lowbarm;"],
        [re.compile(re.escape("&lowbarm;"), re.MULTILINE), "_"],
        [re.compile(re.escape("&llddash;"), re.MULTILINE), "_"],
        [re.compile(re.escape("[Reserved.],"), re.MULTILINE), "[Reserved],"],
        [re.compile(re.escape("[Reserved],."), re.MULTILINE), "[Reserved],"],
        [re.compile(re.escape("&mdash;[Reserved],"), re.MULTILINE), " [Reserved],"],
        [re.compile(re.escape("&mdash;[RESERVED],"), re.MULTILINE), " [RESERVED],"],
        [re.compile(re.escape("&emsp;[Reserved],"), re.MULTILINE), " [Reserved],"],
        [re.compile(re.escape("&emsp;[RESERVED],"), re.MULTILINE), " [RESERVED],"],
        [re.compile(re.escape("&dash;"), re.MULTILINE), "-"],
        [re.compile(re.escape("<HD4>"), re.MULTILINE), "<HD1>"],
        [re.compile(re.escape("<HD6>"), re.MULTILINE), "<HD2>"],
        [re.compile(re.escape("&mdash;</E>"), re.MULTILINE), "</E>&mdash;"],
        [re.compile("\n<FTREF>", re.MULTILINE), "<FTREF>"],
        [re.compile("<FTNT>\n", re.MULTILINE), "<FTNT>"],
        [re.compile("\n</FTNT>", re.MULTILINE), "</FTNT>"],
        [re.compile("\n<SU>", re.MULTILINE), "<SU>"],
        [re.compile("\n<FR>", re.MULTILINE), "<FR>"],
        [re.compile(re.escape("<E T='52'>x</E>"), re.MULTILINE), "<E T='52'>X</E>"],
        [re.compile(re.escape("<AMDPAR>"), re.MULTILINE), "<P>"],
        [re.compile(re.escape("<TTITLE>"), re.MULTILINE), "\n<TTITLE>"],
        [re.compile("\n\n<TTITLE>", re.MULTILINE), "\n<TTITLE>"],
        [re.compile(re.escape("<TDESC>"), re.MULTILINE), "\n<TDESC>"],
        [re.compile("\n\n<TDESC>", re.MULTILINE), "\n<TDESC>"],
        [re.compile("<TTITLE>&emsp;\n", re.MULTILINE), ""],
        [re.compile("<TTITLE>&emsp; \n", re.MULTILINE), ""],
        [re.compile("<TTITLE>&ensp;\n", re.MULTILINE), ""],
        [re.compile("<TTITLE>&ensp; \n", re.MULTILINE), ""],
        [re.compile(re.escape("<BOXHD> "), re.MULTILINE), "<BOXHD>"],
        [re.compile("<BOXHD>\n", re.MULTILINE), "<BOXHD>"],
        [re.compile("\.\n\n<BOXHD>", re.MULTILINE), "\n<BOXHD>"],
        [re.compile(re.escape("<ENT> "), re.MULTILINE), "<ENT>"],
        [re.compile("\n<ENT", re.MULTILINE), "<ENT"],
        [re.compile("\n<ENT", re.MULTILINE), "<ENT"],
        [re.compile(re.escape(" <ENT"), re.MULTILINE), "<ENT"],
        [re.compile(re.escape("<ROW"), re.MULTILINE), "\n<ROW"],
        [re.compile("\n\n<ROW", re.MULTILINE), "\n<ROW"],
        [re.compile("\n</GPO", re.MULTILINE), "</GPO"],
        [re.compile(re.escape(" </GPO"), re.MULTILINE), "</GPO"],
        [re.compile(re.escape("&amp;qdrt;"), re.MULTILINE), "&qdrt;"],
        [re.compile(re.escape(" & "), re.MULTILINE), " &amp; "],
        [re.compile(re.escape(" < "), re.MULTILINE), " &lt; "],
        [re.compile("<EXTRACT>\n", re.MULTILINE), "<EXTRACT>"],
        [re.compile(re.escape(" &thnsp;"), re.MULTILINE), "&thnsp;"],
        [re.compile(re.escape("&thnsp; "), re.MULTILINE), "&thnsp;"],
        [re.compile(re.escape("&hairsp;&hairsp;"), re.MULTILINE), "&thnsp;"],
        [re.compile(re.escape("<E T='61'>&plusmn;</E>"), re.MULTILINE), "&plusmn;"],
        [re.compile(re.escape("<E T='61'>&times;</E>"), re.MULTILINE), "&times;"],
        [re.compile(re.escape("<E T='61'>#</E>"), re.MULTILINE), "&num;"],
        [re.compile(re.escape("<E T='61'>&sec;</E>"), re.MULTILINE), "&sec;"],
        [re.compile(re.escape("<E T='61'>&middot;</E>"), re.MULTILINE), "&middot;"],
        [re.compile(re.escape("<E T='61'>&omega;</E>"), re.MULTILINE), "&omega;"],
        [re.compile(re.escape("<E T='61'>&num;</E>"), re.MULTILINE), "&num;"],
        [re.compile(re.escape("<E T='61'>&mu;</E>"), re.MULTILINE), "&mu;"],
        [re.compile(re.escape("<E T='61'>&deg;</E>"), re.MULTILINE), "&deg;"],
        [re.compile(re.escape("&deg; F"), re.MULTILINE), "&deg;F"],
        [re.compile(re.escape(" &deg;F"), re.MULTILINE), "&deg;F"],
        [re.compile(re.escape("&deg;F"), re.MULTILINE), " &deg;F"],
        [re.compile(re.escape("&deg; C"), re.MULTILINE), "&deg;C"],
        [re.compile(re.escape(" &deg;C"), re.MULTILINE), "&deg;C"],
        [re.compile(re.escape("&deg;C"), re.MULTILINE), " &deg;C"],
        [re.compile(re.escape("^"), re.MULTILINE), "&minus;"],
        [re.compile(re.escape("Register</E>. "), re.MULTILINE), "Register.</E> "],
        [re.compile("Register</E>\. \n", re.MULTILINE), "Register.</E>\n"],
        [re.compile(re.escape("Register</E>, "), re.MULTILINE), "Register,</E> "],
        [re.compile(re.escape("r of the <E T='04'>Federal Register.</E>"), re.MULTILINE), "r of the Federal Register."],
        [re.compile(re.escape("r of the <E T='04'>Federal Register,</E>"), re.MULTILINE), "r of the Federal Register,"],
        [re.compile(re.escape("ce of the <E T='04'>Federal Register.</E>"), re.MULTILINE),
         "ce of the Federal Register."],
        [re.compile(re.escape("ce of the <E T='04'>Federal Register,</E>"), re.MULTILINE),
         "ce of the Federal Register,"],
        [re.compile(re.escape("<FP1-2>"), re.MULTILINE), "<P-2>"],
        [re.compile(re.escape("<FP2-2>"), re.MULTILINE), "<FP2>"],
        [re.compile(re.escape("<CITA TYPE='N'>"), re.MULTILINE), "<CITA>"],
        [re.compile(re.escape(" </E> "), re.MULTILINE), "</E> "],
        [re.compile(re.escape("!l*f"), re.MULTILINE), "&euro"],
        [re.compile(re.escape("<Q P='02'/>"), re.MULTILINE), ""],
        [re.compile(re.escape("<Q P='04'/>"), re.MULTILINE), ""],
        [re.compile(re.escape("<Q"), re.MULTILINE), "\n<Q"],
        [re.compile("\n\n<Q", re.MULTILINE), "\n<Q"],
        [re.compile(re.escape(". </EXAMPLE>"), re.MULTILINE), ".</EXAMPLE>"],
        [re.compile(re.escape(" POSITION='NOFLOAT'"), re.MULTILINE), ""],
        [re.compile(re.escape(" BORDER='NODRAW'"), re.MULTILINE), ""],
        [re.compile(re.escape(" STRIP='YES'"), re.MULTILINE), ""],
        [re.compile(re.escape(" HTYPE='CENTER'"), re.MULTILINE), ""],
        [re.compile(re.escape(" ROTATION='P'"), re.MULTILINE), ""],
        [re.compile("<\?USGPO Galley Info Start\:.*?Galley Info End\?>", re.DOTALL), ""],
        [re.compile("\r", re.MULTILINE), "\n"],
    ]
    return list_regex


def omega_array():
    """
    Array of compiled replacement patterns for use with "omega" function

    @return: list of compiled substitution regular expressions
    """
    list_regex = [
        [re.compile(re.escape("  "), re.DOTALL), " "],
        [re.compile("\n \n", re.DOTALL), "\n"],
        [re.compile("\. \n</", re.DOTALL), ".</"],
        [re.compile(" \n</", re.DOTALL), "</"],
        [re.compile("\n</", re.DOTALL), "</"],
        [re.compile("(?<=Authority:)\n<P>|(?<=Note:)\n<P>|(?<=Source:)\n<P>|(?<=Example:)\n<P>", re.MULTILINE), "<P>"],
        [re.compile("\n\n", re.DOTALL), "\n"],
        [re.compile("(?<=\S)(?<!<STARS>)</REGTEXT>", re.DOTALL), "\n</REGTEXT>"],
        [re.compile("</REGTEXT>\s+<REGTEXT", re.DOTALL), "</REGTEXT>\n\n<REGTEXT"],
        [re.compile("<REGTEXT", re.DOTALL), "\n<REGTEXT"],
        [re.compile(re.escape("<E T='51'>1</E>"), re.DOTALL), "<SU>1</SU>"],
        [re.compile(re.escape("<E T='51'>2</E>"), re.DOTALL), "<SU>2</SU>"],
        [re.compile(re.escape("<E T='51'>3</E>"), re.DOTALL), "<SU>3</SU>"],
        [re.compile(re.escape("<E T='51'>4</E>"), re.DOTALL), "<SU>4</SU>"],
        [re.compile(re.escape("<E T='51'>5</E>"), re.DOTALL), "<SU>5</SU>"],
        [re.compile(re.escape("<E T='51'>6</E>"), re.DOTALL), "<SU>6</SU>"],
        [re.compile(re.escape("<E T='51'>7</E>"), re.DOTALL), "<SU>7</SU>"],
        [re.compile(re.escape("<E T='51'>8</E>"), re.DOTALL), "<SU>8</SU>"],
        [re.compile(re.escape("<E T='51'>9</E>"), re.DOTALL), "<SU>9</SU>"],
        [re.compile(re.escape("<E T='51'>10</E>"), re.DOTALL), "<SU>10</SU>"],
        [re.compile(re.escape("<E T='51'>11</E>"), re.DOTALL), "<SU>11</SU>"],
        [re.compile(re.escape("<E T='51'>12</E>"), re.DOTALL), "<SU>12</SU>"],
        [re.compile(re.escape("<E T='51'>13</E>"), re.DOTALL), "<SU>13</SU>"],
        [re.compile(re.escape("<E T='51'>14</E>"), re.DOTALL), "<SU>14</SU>"],
        [re.compile(re.escape("<E T='51'>15</E>"), re.DOTALL), "<SU>15</SU>"],
        [re.compile(re.escape("<E T='51'>16</E>"), re.DOTALL), "<SU>16</SU>"],
        [re.compile(re.escape("<E T='51'>17</E>"), re.DOTALL), "<SU>17</SU>"],
        [re.compile(re.escape("<SUBJECT>"), re.MULTILINE), "\n<SUBJECT>"],
        [re.compile(re.escape("</CFRDOC>"), re.DOTALL), "\n\n</CFRDOC>"],
        # [re.compile("(?<!\n{2,n})<SECTION>", re.DOTALL), "\n<SECTION>"],
        [re.compile("<PRTPAG.*?>\n?", re.MULTILINE), ""],
        [re.compile("\n{0,2}^(<SUBPART>.*\n|<PART>.*\n|<HD1>.*\n)?(<SECTION>.*\n)?.*\n.*?<SUBJECT>\[?Removed.*\]?\.?",
                    re.MULTILINE), ""],
        [re.compile("\n{0,2}^(<SUBPART>.*\n|<PART>.*\n|<HD1>.*\n)?(<SECTION>.*\n)?.*\n.*?<SUBJECT>\[?Amended.*\]?\.?",
                    re.MULTILINE), ""],
        [re.compile("\n{0,2}^(<SUBPART>.*\n|<PART>.*\n|<HD1>.*\n)?(<SECTION>.*\n)?.*\n.*?<SUBJECT>\[?Corrected.*\]?\.?",
                    re.MULTILINE), ""],
        [re.compile(
            "\n{0,2}^(<SUBPART>.*\n|<PART>.*\n|<HD1>.*\n)?(<SECTION>.*\n)?.*\n.*?<SUBJECT>\[?Redesignated.*\]?\.?",
            re.MULTILINE), ""],
        [re.compile("<HD1>.*?\[Removed.*\]\n|<HD1>.*?\[?Amended.*\]?\n|<HD1>.*?\[?Corrected.*\]?\n", re.MULTILINE), ""],
        [re.compile("<(GPH.*?)>\s*?(<GID>.*?</GPH>)\s*?<!--(GPH.*?)-->", re.MULTILINE), "<\g<3>>\n\g<2>\n"],
        [re.compile("<(MATH.*?)>\s*?(<MID>.*?</MATH>)\s*?<!--(MATH.*?)-->", re.MULTILINE), "<\g<3>>\n\g<2>\n"],
        [re.compile("<BILCOD>.*\n", re.MULTILINE), ""],
    ]
    return alpha_array() + list_regex


def get_from_dict(val, my_dict, hilo="prev"):
    """
    Searches a dictionary with positions:value to return either previous or next value to the specified "val" position

    @rtype : str
    @param val: location to search either up or down
    @param my_dict: dictionary of all occurance locations (key = location, value = searched string)
    @param hilo: count up to the next or down to previous
    @return: value of that location
    """
    ret_value = None
    od = collections.OrderedDict(sorted(my_dict.items(), key=lambda t: t[0]))
    for case in switch(hilo):
        if case('prev'):
            for k, v in od.items():
                if int(k) < val:
                    ret_value = v
            break
        if case('next'):
            for k, v in od.items():
                if int(k) > val:
                    ret_value = val
    return ret_value


def replace(filename, regexes):
    """
    Replaces occurences of patterns in a dict with corresponding string in a given file

    @type filename: str
    @type regexes: list
    @param filename: filename where replacements should take place
    @param regexes: list of compiled replacement patterns [search pattern, replacement string]
    """
    with open(filename, 'rb') as content_file:
        file_string = content_file.read().decode()

    # Use RE package to allow for replacement (also allowing for (multiline) REGEX)
    for pattern in regexes:
        try:
            file_string = pattern[0].sub(pattern[1], file_string)
        except Exception as e:
            exit("Bad regular expression: " + pattern)

    # Write contents to file.
    # Using mode 'w' truncates the file.
    with open(filename, 'w') as file_handle:
        file_handle.write(file_string)
    return


def move_files(from_dir, to_dir, file_date):
    """Moves the files from one dir to another. Optional date specifies particular date, otherwise today's used
    @type from_dir: str
    @type to_dir: str
    @type file_date: str

    @param from_dir: Where to get files from
    @param to_dir: Where to move files to
    @param file_date: Date of the files to move
    """
    if file_date is None:
        file_date = date.today().strftime("%m%d%y")
    sMM = file_date[0:2]
    sDD = file_date[2:4]
    sYY = file_date[4:6]
    sMMM = ''

    for case in switch(sMM):
        if case('01'):
            sMM = "JA"
            sMMM = "JAN"
            break
        if case('02'):
            sMM = "FE"
            sMMM = "FEB"
            break
        if case('03'):
            sMM = "MR"
            sMMM = "MAR"
            break
        if case('04'):
            sMM = "AP"
            sMMM = "APR"
            break
        if case('05'):
            sMM = "MY"
            sMMM = "MAY"
            break
        if case('06'):
            sMM = "JN"
            sMMM = "JUN"
            break
        if case('07'):
            sMM = "JY"
            sMMM = "JUL"
            break
        if case('08'):
            sMM = "AU"
            sMMM = "AUG"
            break
        if case('09'):
            sMM = "SE"
            sMMM = "SEP"
            break
        if case('10'):
            sMM = "OC"
            sMMM = "OCT"
            break
        if case('11'):
            sMM = "NO"
            sMMM = "NOV"
            break
        if case('12'):
            sMM = "DE"
            sMMM = "DEC"
            break
        if case():
            sys.exit("Missing month!!!")

    dest_file = open(os.path.join(to_dir, sYY + sMMM + sDD), 'wb')
    file_set = glob.glob(os.path.join(from_dir, sDD + sMM + 'R*.SGM'))
    if file_set:
        for filename in file_set:
            if os.path.isfile(filename):
                if not os.path.exists(to_dir):
                    os.makedirs(to_dir)
                shutil.copyfileobj(open(filename, 'rb'), dest_file)
            else:
                sys.exit("Input is not a file!!! -> " + filename)
    else:
        sys.exit("No input files located for a specified date!!!")
    dest_file.close()
    return dest_file


def alpha(tmp_file):
    """Applies replacement pattern to data files

    @type tmp_file: str
    @param tmp_file: combined file
    """
    if os.path.isfile(tmp_file):
        replace(tmp_file, alpha_array()),
    return


def omega(tmp_file):
    """Applied final replacement patterns to data file

    @rtype : object
    @param tmp_file: str
    @return:
    """
    if os.path.isfile(tmp_file):
        replace(tmp_file, omega_array()),
    return


def partext(temp_file, file_date):
    """
    Extract REGTEXT blocks and expend their date, etc. properties

    @rtype : str
    @param temp_file: Input file to process
    @param file_date: Date of the file
    @return: Processed file
    """
    file_string = ''
    if file_date is None:
        eff_date = date.today().strftime("%Y%m%d")
    else:
        eff_date = datetime.strptime(file_date, "%m%d%y").strftime("%Y%m%d")
    if os.path.isfile(temp_file):
        # Read contents from file as a single string
        with open(temp_file, 'rb') as content_file:
            file_string = content_file.read().decode()

    new_file_string = ''
    vol_num = re.findall('<VOL>(\d*)', file_string)[0]

    # Get a dictionary of Effective dates and their location for attaching to REGTEXT
    effdates_info = defaultdict(list)
    effdates_info[0].append(datetime.strptime(eff_date, "%Y%m%d"))
    effdates_info[0].append("Pull date: {0:%B} {0.day}, {0:%Y}".format(datetime.strptime(eff_date, "%Y%m%d")))
    for eff_date_itr in re.finditer(re.compile("DATE.?><HED>DATES.*\n?<P>(.*)", re.MULTILINE), file_string):
        if eff_date_itr.group():
            eff_date_str = re.findall("(\w*) (\d{1,2}), (\d{4})", eff_date_itr.group())

            if len(eff_date_str) == 1:
                effdates_info[eff_date_itr.start()].append(
                    datetime.strptime(" ".join(str(i) for i in eff_date_str[0]), "%B %d %Y"))
                effdates_info[eff_date_itr.start()].append("{0:%B} {0.day}, {0:%Y}".format(
                    datetime.strptime(" ".join(str(i) for i in eff_date_str[0]), "%B %d %Y")))
            elif len(eff_date_str) > 1:
                effdates_info[eff_date_itr.start()].append(
                    datetime.strptime(" ".join(str(i) for i in eff_date_str[0]), "%B %d %Y"))
                effdates_info[eff_date_itr.start()].append(eff_date_itr.group(1))
            else:
                effdates_info[eff_date_itr.start()].append(None)
                effdates_info[eff_date_itr.start()].append(eff_date_itr.group(1))
        else:
            effdates_info[eff_date_itr.start()].append(None)
            effdates_info[eff_date_itr.start()].append(eff_date_itr.group(1))

    # Get a dictionary of PRTPAGE tag numbers and their location for attaching to REGTEXT
    prtpage_info = dict()
    prtpage_info[0] = ['00000']
    for prt_page_itr in re.finditer(re.compile("\s*<PRTPAGE P=\'(\d+)\'>\s*"), file_string):
        if prt_page_itr.group():
            pg_num = re.findall("\d+", prt_page_itr.group())
            prtpage_info[prt_page_itr.start()] = pg_num
        else:
            prtpage_info[prt_page_itr.start()] = '00000'

    # Retrieve REGTEXT clauses and attach dates and page number tags and attributes to them
    id_seq = 0
    for reg in re.finditer('(<REGTEXT TITLE.*?</REGTEXT>)', file_string, re.S):
        id_seq += 1
        reg_eff_date = get_from_dict(reg.start(), effdates_info)
        if reg_eff_date[0]:
            effdate_attrib = reg_eff_date[0].strftime("%Y%m%d")
            effdate_element = reg_eff_date[1]
        else:
            effdate_attrib = "{0:%Y}0000".format(datetime.strptime(eff_date, "%Y%m%d"))
            effdate_element = reg_eff_date[1]
        reg_prt_num = get_from_dict(reg.start(), prtpage_info)
        regtxt_attrb = ' EFFDATE=\'' + effdate_attrib + '\' ID=\'' + eff_date + '-' + str(id_seq) + \
                       '\' FRPAGE=\'' + vol_num + 'FR' + reg_prt_num[
                           0] + '\'><EFFDATES>' + effdate_element
        reg_txt = re.sub(">", regtxt_attrb, reg.group(0), 1)
        new_file_string += reg_txt
    new_file_string = "<CFRDOC ED='XX' REV='XX'>\n\n" + new_file_string + "\n</CFRDOC>"
    new_file_name = os.path.join(os.path.dirname(temp_file), eff_date + ".AMD")
    with open(new_file_name, "w") as text_file:
        text_file.write(new_file_string)
    return new_file_name


if __name__ == "__main__":
    args = docopt(__doc__, version='\nPULL 2.3.6')

    if args['set']:
        from_dir = r'\\hqnapdcm0734\ofr\ofr_gpo\TOOFR'
        to_dir = r'\\hqnapdcm0734\ofr\e_cfr\Regtext'
        if os.path.exists(from_dir) and os.path.exists(to_dir):
            temp_file = move_files(from_dir, to_dir, None)
            alpha(temp_file.name)
            final_file = partext(temp_file.name, None)
            omega(final_file)
            print("\n*** Auto Processing Completed! File is located here: " + final_file + " ***")
        else:
            print(
                "\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
                "!!! Either <from> or <to> or both directories are invalid !!!\n"
                "!!! Make sure 'M:\Toofr' and 'L:\Regtext' are present     !!!\n"
                "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

    elif args['auto']:
        schema = Schema({
            '<from>': And(os.path.exists, error='\n<from> directory must exist!!!'),
            '<to>': And(os.path.exists, error='\n<to> directory must exist!!!'),
            '--date': Or(None, And(lambda n: datetime.strptime(n, "%m%d%y")),
                         error='\n--date= must be in a <MMDDYY> format!!!'),
            str: object
        })
        try:
            args = schema.validate(args)
        except SchemaError as e:
            sys.exit(e)
        temp_file = move_files(args['<from>'], args['<to>'], args['--date'])
        alpha(temp_file.name)
        final_file = partext(temp_file.name, args['--date'])
        omega(final_file)
        print("\n*** Auto Processing Completed! File is located here: " + final_file + " ***")

    elif args['move']:
        schema = Schema({
            '<from>': And(os.path.exists, error='\n<from> directory must exist!!!'),
            '<to>': And(os.path.exists, error='\n<to> directory must exist!!!'),
            '--date': Or(None, And(lambda n: datetime.strptime(n, "%m%d%y")),
                         error='\n--date= must be in a <MMDDYY> format!!!'),
            str: object
        })
        try:
            args = schema.validate(args)
        except SchemaError as e:
            sys.exit(e)
        temp_file = move_files(args['<from>'], args['<to>'], args['--date'])
        print("\n*** Files Moved & Combined! Destination file is located here: " + temp_file.name + " ***")