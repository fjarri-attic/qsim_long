import sys, re
from unidecode import unidecode
import codecs

def loadMendeleyBib(fname):

    f = codecs.open(fname, 'r', 'utf-8')
    text = f.read()
    f.close()

    raw_entries = ('\n' + text).split('\n@')[1:]

    # parse bib file
    entries = []
    for raw_entry in raw_entries:
        lines = raw_entry.split('\n')

        # read header
        mo = re.match(r'^(\w+)\{(.*),$', lines[0])
        entry_type = mo.group(1)
        entry_key = unidecode(mo.group(2))

        # read fields
        entry_fields = {}
        for line in lines[1:]:

            if line == '}':
                break

            mo = re.match(r'^([\w-]+)\s+=\s+(.*?),?$', line)

            value = mo.group(2)
            if value[0] == '{':
                assert value[-1] == '}'
                value = value[1:-1]

            entry_fields[mo.group(1)] = value

        entries.append((entry_type, entry_key, entry_fields))

    return entries

def saveTexBib(fname, entries):
    f = open(fname, 'w')
    for entry_type, entry_key, entry_fields in entries:
        f.write('@' + entry_type + '{' + entry_key + ',\n')
        for field in entry_fields:
            f.write('\t' + field + ' = {' + entry_fields[field] + '},\n')
        f.write('}\n\n')

    f.close()

def removeFields(entries):
    for entry_type, entry_key, entry_fields in entries:
        for field in ('file', 'keywords', 'mendeley-tags', 'abstract', 'month', 'issn', 'url', 'isbn'):
            if field in entry_fields:
                del entry_fields[field]

def fixArxivReferences(entries):
    for entry_type, entry_key, entry_fields in entries:
        if 'arxivId' in entry_fields:
            if 'journal' in entry_fields:
            # already published, no need to cite arxiv
                del entry_fields['arxivId']
            else:
                aid = entry_fields['arxivId']
                #del entry_fields['arxivId']
                #del entry_fields['year']

                entry_fields['archivePrefix'] = 'arXiv'
                entry_fields['eprint'] = aid[:4] + '.' + aid[5:]
                entry_fields['SLACcitation'] = "%%CITATION=" + aid[:4] + aid[5:] + ";%%"

def authorsGeneral(entries):
    for entry_type, entry_key, entry_fields in entries:
        if 'author' in entry_fields:
            entry_fields['author'] = entry_fields['author'].replace('\\o ', '{\\o}')

def truncateAuthorList(entries, limit=4):
    for entry_type, entry_key, entry_fields in entries:
        if 'author' in entry_fields:
            authors = entry_fields['author'].split(' and ')
            if len(authors) >= limit:
                entry_fields['author'] = authors[0] + ' and others'

def initialsToFront(entries):
    """AIP style authors: A. B. Smith"""
    for entry_type, entry_key, entry_fields in entries:
        if 'author' in entry_fields:
            authors = entry_fields['author'].split(' and ')
            new_authors = []
            for author in authors:
                surname, names = author.split(', ')
                names = [name if re.match(r'^[A-Z]\.$', name) else name[0] + '.' for name in names.split(' ')]
                new_authors.append(' '.join(names) + ' ' + surname)
            entry_fields['author'] = ' and '.join(new_authors)

def initialsToBack(entries):
    """IOP style authors: Smith A B"""
    for entry_type, entry_key, entry_fields in entries:
        if 'author' in entry_fields:
            authors = entry_fields['author'].split(' and ')
            new_authors = []
            for author in authors:
                surname, names = author.split(', ')
                new_authors.append(surname + ' ' + ' '.join(name[0] for name in names.split(' ')))
            entry_fields['author'] = ' and '.join(new_authors)

def journalAbbreviations(entries):
    # replace journal names with abbreviations
    abbreviations = {
        'Physical Review A': 'Phys. Rev. A',
        'Journal of Physics B: Atomic, Molecular and Optical Physics': 'J. Phys. B',
        'Physical Review Letters': 'Phys. Rev. Lett.',
        'The European Physical Journal B': 'Eur. Phys. J. B',
        'Europhysics Letters (EPL)': 'Europhys. Lett.',
        'SIAM Journal on Scientific Computing': 'SIAM J. Sci. Comput.',
    }

    for entry_type, entry_key, entry_fields in entries:
        if 'journal' in entry_fields and entry_fields['journal'] in abbreviations:
            entry_fields['journal'] = abbreviations[entry_fields['journal']]

def removePaperTitles(entries):
    for entry_type, entry_key, entry_fields in entries:
        if entry_type == 'article' and 'title' in entry_fields and 'arxivId' not in entry_fields:
            del entry_fields['title']

def prepare(entries):
    authorsGeneral(entries)
    #truncateAuthorList(entries, limit=4)
    #initialsToBack(entries) # required for unsrt style
    journalAbbreviations(entries)
    removeFields(entries)
    fixArxivReferences(entries)
    removePaperTitles(entries)

if __name__ == '__main__':
    entries = loadMendeleyBib(sys.argv[1])
    prepare(entries)
    saveTexBib(sys.argv[2], entries)

