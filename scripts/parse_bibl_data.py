from typing import List, Union
from xml.etree.ElementTree import Element

import parse_tei


def get_authors(tei_ele: Element):
    author_tag = parse_tei.make_tei_tag('author')
    authors = []
    for author in tei_ele.iter(author_tag):
        author_info = {}
        for child in author:
            tag = parse_tei.clean_tag(child.tag)
            if tag == 'persName':
                author_info['author_name'] = get_author_name(child)
            else:
                tag_info = {
                    'text': ' -- '.join([text.strip() for text in child.itertext() if text.strip() != '']),
                    'attrs': child.attrib
                }
                author_info[tag] = tag_info
        authors.append(author_info)
    return authors


def get_author_name(name_ele):
    return {parse_tei.clean_tag(child.tag): ' '.join([t for t in child.itertext()]) for child in name_ele}


def get_ref_id(bibl_struct: Element) -> Union[str, None]:
    id_tag = parse_tei.make_tei_tag('id')
    if id_tag in bibl_struct.attrib:
        return bibl_struct.attrib[id_tag]
    else:
        return None


def get_raw_ref(bibl_struct: Element):
    notes = parse_tei.get_elements_by_tag(bibl_struct, 'note')
    for note in notes:
        if 'type' in note.attrib and note.attrib['type'] == 'raw_reference':
            return note.text
    return None


def get_ref_info(bibl_struct):
    analytic = get_analytic(bibl_struct)
    monogr = get_monogr(bibl_struct)
    raw_ref = get_raw_ref(bibl_struct)
    idno = get_ref_idno(bibl_struct)
    ref_ids = get_ref_idno(bibl_struct)
    doi = get_doi(ref_ids)
    if doi:
        pub_id = doi
    elif ref_ids and len(ref_ids) > 0:
        pub_id = ref_ids[0]['value']
    else:
        pub_id = None
    return {
        'analytic': analytic, 'monogr': monogr,
        'raw_ref': raw_ref,
        'idno': idno, 'doi': doi,
        'id': pub_id
    }


def get_doi(ref_ids: List[dict]):
    dois = [ref_id['value'] for ref_id in ref_ids if ref_id['type'] == 'DOI'] if ref_ids else []
    if len(dois) > 1:
        raise ValueError(f'multiple DOIs for ref: {dois}')
    elif len(dois) == 1:
        return dois[0]
    else:
        return None


def get_title(tei_ele: Element):
    tei_title = parse_tei.get_element_by_tag(tei_ele, 'title')
    if tei_title is not None:
        title = ' ---- '.join([text_string for text_string in tei_title.itertext()])
    else:
        title = None
    return title


def get_analytic(bibl_struct: Element):
    analytic = parse_tei.get_element_by_tag(bibl_struct, 'analytic')
    if analytic is None:
        return None
    analytic_title = parse_tei.get_element_by_tag(analytic, 'title')
    if analytic_title is not None:
        title = ' ---- '.join([text_string for text_string in analytic_title.itertext()])
    else:
        title = None
    ref_ids = get_ref_idno(analytic)
    analytic_info = {
        'id': get_ref_id(bibl_struct),
        'title': title,
        'authors': get_authors(analytic),
        'ref_ids': ref_ids,
        'doi': get_doi(ref_ids)
    }
    return analytic_info


def get_monogr(bibl_struct: Element):
    monogr = parse_tei.get_elements_by_tag(bibl_struct, 'monogr')[0]
    monogr_info = {'authors': get_authors(monogr)}
    for child in monogr:
        if parse_tei.has_tag(child, 'author'):
            continue
        if parse_tei.has_tag(child, 'imprint'):
            monogr_info['imprint'] = get_imprint(child)
        else:
            tag = parse_tei.clean_tag(child.tag)
            tag_info = {
                'text': ' '.join([text for text in child.itertext()]),
                'attrs': child.attrib
            }
            monogr_info[tag] = tag_info
    return monogr_info


def get_imprint(bibl_struct: Element):
    imprint = parse_tei.get_elements_by_tag(bibl_struct, 'imprint')[0]
    imprint_info = {}
    for child in imprint:
        tag = parse_tei.clean_tag(child.tag)
        tag_info = {
            'text': ' '.join([text for text in child.itertext()]),
            'attrs': child.attrib
        }
        imprint_info[tag] = tag_info
    return imprint_info


def get_ref_idno(analytic: Element) -> Union[List[dict], None]:
    idno_list = parse_tei.get_elements_by_tag(analytic, 'idno')
    if len(idno_list) == 0:
        return None
    else:
        try:
            return [{'type': idno.attrib['type'] if 'type' in idno.attrib else 'unknown', 'value': idno.text} for idno in idno_list]
        except KeyError:
            print([(idno.attrib, idno.text) for idno in idno_list])
            raise


def parse_ref_author_name(author):
    name_dict = author['author_name']
    author_name = ''
    known_fields = {'surname', 'forename', 'roleName', 'genName'}
    for field in name_dict:
        if field not in known_fields:
            print(name_dict)
    if 'surname' in name_dict and 'forename' in name_dict:
        author_name = f"{name_dict['forename']} {name_dict['surname']}"
    elif 'surname' in name_dict:
        author_name = name_dict['surname']
    return author_name


def get_ref_cited_info(ref: dict):
    assert isinstance(ref, dict), "ref must be a dictionary"
    cited_title, cited_author, cited_raw = None, None, None
    if 'analytic' in ref and ref['analytic'] and 'title' in ref['analytic'] and ref['analytic']['title'] is not None:
        cited_title = ref['analytic']['title']
    elif 'monogr' in ref and ref['monogr'] and 'title' in ref['monogr'] and ref['monogr']['title'] is not None:
        cited_title = ref['monogr']['title']['text']
    if 'analytic' in ref and ref['analytic'] and 'authors' in ref['analytic'] and ref['analytic']['authors'] is not None:
        cited_author = ref['analytic']['authors']
    elif 'monogr' in ref and ref['monogr'] and 'authors' in ref['monogr'] and ref['monogr']['authors'] is not None:
        cited_author = ref['monogr']['authors']
    if 'raw_ref' in ref and ref['raw_ref'] is not None:
        cited_raw = ref['raw_ref']
    if cited_author is not None:
        cited_author = ', '.join([parse_ref_author_name(aut) for aut in cited_author if 'author_name' in aut])
    if 'id' not in ref:
        print('no id in ref:', ref)
    return ref['id'], cited_title, cited_author, cited_raw

