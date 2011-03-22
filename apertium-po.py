#! /usr/bin/env python

__author__ = 'Rory McCann <rory@technomancy.org>'
__version__ = '1.0'
__licence__ = 'GPLv3'

import polib, subprocess, re, sys

def translate_subpart(string, lang_direction):
    """Simple translate for just a certin string"""

    for codes in lang_direction.split("/"):
        translater = subprocess.Popen(['apertium', '-u', '-f', 'html', codes], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        translater.stdin.write(string.encode("utf8")+"\n")
        string, _ = translater.communicate()
        string = string[:-1].decode("utf8")

    return string

def translate(string, lang_direction):
    """Takes a string that is to be translated and returns the translated string, doesn't translate the %(format)s parts, they must remain the same text as the msgid"""
    # simple format chars like %s can be 'translated' ok, they just pass through unaffected
    named_format_regex = re.compile(r"%\([^\)]+?\)[sd]", re.VERBOSE)
    matches = named_format_regex.findall(string)
    new = None

    if len(matches) == 0:
        # There are no format specifiers in this string, so just do a straight translation

        # this fails if we've missed a format specifier
        assert "%(" not in string, string

        new = translate_subpart(string, lang_direction)

    else:

        # we need to do complicate translation of the bits inside
        full_trans = translate_subpart(string, lang_direction)

        for match in matches:
            # then, for each format specifier, replace back in the string

            translated_match = translate_subpart(match, lang_direction)

            # during the translation some extra punctuation/spaces might have been added
            # remove them
            translated_match_match = named_format_regex.search(translated_match)
            assert translated_match_match
            translated_match = translated_match_match.group(0)

            # put back the format specifier, the case of the format specifier might have changed
            replace = re.compile(re.escape(translated_match), re.IGNORECASE)
            full_trans = replace.sub(match, full_trans)

        
        new = full_trans

    return new

def translate_po(filename, lang_direction):
    """Given a .po file, Translate it"""
    pofile = polib.pofile(filename)

    # pretend the same plural forms as English
    pofile.metadata['Plural-Forms'] = 'nplurals=2; plural=(n != 1)'

    try:
        total = len(pofile)
        num_done = 0

        for entry in pofile:

            if entry.msgid_plural == '':
                # not a pluralized string
                entry.msgstr = translate(entry.msgid, lang_direction)

            else:
                # pluralised string
                # we just pretend to use the same rules as english
                entry.msgstr_plural['0'] = translate(entry.msgid, lang_direction)
                entry.msgstr_plural['1'] = translate(entry.msgid_plural, lang_direction)

            num_done += 1
            if num_done % 10 == 0:
                print "Translated %d of %d" % (num_done, total)

    finally:
        pofile.save(filename)

if __name__ == '__main__':
    translate_po(sys.argv[1], sys.argv[2])

