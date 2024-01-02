from typing import List
from xml.etree.ElementTree import Element

import pandas as pd

import parse_tei
import parse_bibl_data as parse_bib
import parse_text


def get_references(root: Element):
    refs = {}
    list_bibl = parse_tei.get_element_by_tag(root, 'listBibl')
    for bibl_struct in parse_tei.get_elements_by_tag(list_bibl, 'biblStruct'):
        ref = parse_bib.get_ref_info(bibl_struct)
        id_tag = parse_tei.make_tei_tag('id')
        ref['bid_id'] = bibl_struct.attrib[id_tag]
        refs[ref['bid_id']] = ref
    return refs


def update_section_title(section_title, section):
    if section['level'] is None:
        pass
    else:
        if section['level'] <= len(section_title):
            while section['level'] <= len(section_title):
                section_title.pop(-1)
        section_title.append(section['title'])


def get_para_citation_rows(doc_id: str, cit_count: int, para: dict,
                           section_title: List[str], references: List[dict],
                           publication_metadata: dict, context_size: int = 1):
    rows = []
    citing_id, citing_title, citing_author, citing_raw = parse_bib.get_ref_cited_info(publication_metadata)
    for si, sent in enumerate(para['sentences']):
        # print(sent.keys())
        start = si - context_size if si > context_size else 0
        end = si + 1 + context_size
        citation_context = ' '.join([s['text'] for s in para['sentences'][start:end]])
        for cit in sent['citations']:
            # print('cit:', cit)
            if cit['reference_id'] in references:
                ref = references[cit['reference_id']]
                # print('ref:', ref)
                cited_id, cited_title, cited_author, cited_raw = parse_bib.get_ref_cited_info(ref)
            else:
                # print('missing reference:', cit)
                cited_id, cited_title, cited_author, cited_raw = 'MISSING', None, None, None
            cit_count += 1
            row = [
                doc_id, cit_count,
                citing_id, citing_author, citing_title,
                cited_id, cited_author, cited_title, cited_raw,
                cit['text'], sent['text'], citation_context, ' -- '.join(section_title)
            ]
            # print('SECTION TITLE:', ' -- '.join(section_title))
            rows.append(row)
        # print(sent['text'])
    return rows


def get_citation_rows(tei_file: str, sections, references, publication_metadata):
    section_title = []
    rows = []
    cit_count = 0
    for section in sections:
        update_section_title(section_title, section)
        # print(section_title)
        for para in section['paragraphs']:
            para_rows = get_para_citation_rows(tei_file, cit_count, para,
                                               section_title, references, publication_metadata)
            cit_count += len(para_rows)
            rows.extend(para_rows)
    return rows


def make_citation_context_csv(tei_files: List[str], citation_context_file: str):
    all_rows = []
    for tei_file in tei_files:
        print('parsing citation contexts for file', tei_file)
        tei_header, tei_text = parse_tei.parse_tei_file(tei_file)
        publication_metadata = get_publication_metadata(tei_header)
        sections = parse_text.parse_sections(tei_text)
        references = get_references(tei_text)
        rows = get_citation_rows(tei_file, sections, references, publication_metadata)
        all_rows.extend(rows)
    columns = [
        'doc_id', 'cit_count', 'citing_id', 'citing_author', 'citing_title',
        'cited_id', 'cited_author', 'cited_title', 'cited_raw',
        'citation_ref', 'citation_sent', 'citation_context', 'section_title'
    ]
    df = pd.DataFrame(all_rows, columns=columns)
    df.to_csv(citation_context_file, sep='\t', index=False)


def get_publication_metadata(tei_header: Element):
    bibl_struct = parse_tei.get_element_by_tag(tei_header, 'biblStruct')
    publication_metadata = parse_bib.get_ref_info(bibl_struct)
    title_stmt = parse_tei.get_element_by_tag(tei_header, 'titleStmt')
    publication_metadata['title'] = ' <> '.join([text.strip() for text in title_stmt.itertext() if text.strip() != ''])
    return publication_metadata

