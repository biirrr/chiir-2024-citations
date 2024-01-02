import xml.etree.ElementTree as ElementTree
from xml.etree.ElementTree import Element


ns = {
    'tei': 'http://www.tei-c.org/ns/1.0',
    'w3': 'http://www.w3.org/XML/1998/namespace'
}


ANALYTIC_FIELDS = {'title', 'author', 'idno', 'ptr'}
AUTHOR_FIELDS = {'persName', 'email', 'idno', 'orgName', 'affiliation'}
PERSONAME_FIELDS = {'forename', 'surname', 'genName'}
MONOGR_FIELDS = {'title', 'meeting', 'imprint', 'idno', 'editor', 'author', 'ptr', 'respStmt'}
IMPRINT_FIELDS = {'biblScope', 'date', 'publisher', 'pubPlace'}
REF_TYPES = {'bibr', 'foot', 'figure', 'table', 'formula'}


def get_name_space(tag: str):
    tag_name_space = ns['tei']
    if tag == 'id':
        tag_name_space = ns['w3']
    return tag_name_space


def has_tag(ele: Element, tag: str):
    tag_name_space = get_name_space(tag)
    return ele.tag == "{" + tag_name_space + "}" + tag


def has_section_head(div: Element):
    child_tags = [clean_tag(child.tag) for child in div]
    return len(child_tags) > 0 and child_tags[0] == 'head'


def make_tei_tag(tag: str):
    tag_name_space = get_name_space(tag)
    return "{" + tag_name_space + "}" + tag


def clean_tag(tag:str):
    for label in ns:
        if ns[label] in tag:
            tag = tag.replace('{' + ns[label] + '}', '')
    return tag


def get_elements_by_tag(ele: Element, tag: str):
    if ns['tei'] not in tag:
        tag = make_tei_tag(tag)
    eles = []
    for child in ele.iter(tag):
        eles.append(child)
    return eles


def get_element_by_tag(ele: Element, tag: str):
    elements = get_elements_by_tag(ele, tag)
    if len(elements) == 0:
        return None
    return elements[0]


def make_bibl_string(bibl_struct: Element):
    text_strings = [text for text in bibl_struct.itertext()]
    return "[\n\t" + '\n\t'.join(text_strings) + "\n]"


def parse_tei_file(tei_file: str):
    tree = ElementTree.parse(tei_file)
    root = tree.getroot()
    tei_header = root.find('tei:teiHeader', ns)
    tei_text = root.find('tei:text', ns)
    return tei_header, tei_text
