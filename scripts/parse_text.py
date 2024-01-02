import re
from xml.etree.ElementTree import Element

import parse_tei


def get_section_divs(text_ele: Element):
    body = parse_tei.get_element_by_tag(text_ele, 'body')
    divs = parse_tei.get_elements_by_tag(body, 'div')
    return [div for div in divs if parse_tei.has_section_head(div) is True]


def get_section_title_info(div: Element):
    if parse_tei.has_section_head(div) is False:
        return None
    head_ele = parse_tei.get_element_by_tag(div, 'head')
    section_title = {
        'title': ' '.join([text for text in head_ele.itertext()]),
        'number': None,
        'level': None
    }
    if 'n' in head_ele.attrib:
        section_title['number'] = head_ele.attrib['n']
        if re.match(r'\d+(\.\d+)*', section_title['number']):
            section_title['level'] = len(section_title['number'].split('.'))
    return section_title


def parse_sections(text_ele: Element):
    section_divs = get_section_divs(text_ele)
    sections = []
    for section_div in section_divs:
        section = parse_section(section_div)
        sections.append(section)
    return sections


def parse_section(section_div: Element):
    section = get_section_title_info(section_div)
    section['paragraphs'] = parse_paragraphs(section_div)
    return section


def parse_paragraphs(text_ele: Element):
    para_tag = parse_tei.make_tei_tag('p')
    paragraphs = []
    for pi, para_ele in enumerate(text_ele.iter(para_tag)):
        paragraph = parse_paragraph(para_ele, pi)
        paragraphs.append(paragraph)
    return paragraphs


def parse_paragraph(para_ele: Element, para_index: int):
    paragraph = {
        'para_index': para_index,
        'sentences': []
    }
    for si, sent_ele in enumerate(para_ele):
        sentence = parse_sentence(sent_ele, si)
        paragraph['sentences'].append(sentence)
    return paragraph


def get_text_references(text_ele: Element, ref_type: str = None):
    reference_elements = [child for child in text_ele if parse_tei.has_tag(child, 'ref')]
    if ref_type:
        reference_elements = [ref for ref in reference_elements if ref.attrib['type'] == ref_type]
    return reference_elements


def parse_sentence(sent_ele: Element, sent_index: int):
    sentence = {
        'sentence_index': sent_index,
        'text': '',
        'text_strings': [sent_ele.text] if sent_ele.text else [],
        'citations': []
    }
    citation_elements = get_text_references(sent_ele, ref_type='bibr')
    for ci, citation_ele in enumerate(citation_elements):
        text_length = sum([len(text_string) for text_string in sentence['text_strings']])
        citation = parse_citation(citation_ele, ci, text_length)
        if citation['text'] is None:
            # an empty reference element, e.g.
            # "<ref type="bibr"></ref>" in 5cGJUhg2MBsJ.1.grobid.tei.xml
            continue
            # print('citation has no text:', citation, [text for text in citation_ele.itertext()])
            # print(sentence['citations'])
            # print(sentence)
        sentence['citations'].append(citation)
        sentence['text_strings'].append(citation['text'])
        if citation_ele.tail:
            sentence['text_strings'].append(citation_ele.tail)
    sentence['text'] = ''.join(sentence['text_strings'])
    for citation in sentence['citations']:
        if citation['text'] is None:
            print("citation['text'] is None, citation:", citation)
            print("sentence:", sentence)
        assert sentence['text'][citation['char_index']:].startswith(citation['text'])
    return sentence


def parse_citation(citation_ele: Element, citation_index: int, text_length: int):
    # if 'target' not in citation_ele.attrib:
    #     print('no reference:', [text for text in citation_ele.itertext()], citation_ele.attrib)
    ref_id = citation_ele.attrib['target'][1:] if 'target' in citation_ele.attrib else None
    citation = {
        'citation_index': citation_index,
        'reference_id': ref_id,
        'char_index': text_length,
        'text': citation_ele.text
    }
    return citation


def parse_footnotes(text_ele: Element):
    footnote_ref_elements = get_text_references(text_ele, ref_type='foot')
    footnote_elements = parse_tei.get_elements_by_tag(text_ele, 'note')
