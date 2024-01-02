from xml.etree.ElementTree import Element

import parse_tei


def validate_assumptions(tei_text):
    validate_text_assumptions(tei_text)
    validate_author_assumptions(tei_text)
    validate_bibliographic_assumptions(tei_text)
    validate_reference_assumptions(tei_text)


def validate_text_assumptions(tei_text):
    assert_para_has_only_sents(tei_text)
    assert_sent_has_only_refs(tei_text)


def validate_author_assumptions(tei_text: Element):
    author_tag = parse_tei.make_tei_tag('author')
    expected_author_tags = {parse_tei.make_tei_tag(tag) for tag in parse_tei.AUTHOR_FIELDS}
    expected_person_tags = {parse_tei.make_tei_tag(tag) for tag in parse_tei.PERSONAME_FIELDS}
    for author_ele in tei_text.iter(author_tag):
        for child in author_ele:
            assert child.tag in expected_author_tags, f"unexpected tag in author: '{child.tag}'"
            if parse_tei.has_tag(child, 'persName'):
                for name in child:
                    assert name.tag in expected_person_tags, f"unexpected tag in persName: '{child.tag}'"


def validate_reference_assumptions(tei_text: Element):
    ref_elements = parse_tei.get_elements_by_tag(tei_text, 'ref')

    for ref_ele in ref_elements:
        assert ref_ele.attrib['type'] in parse_tei.REF_TYPES, f"unexpected reference type '{ref_ele.attrib['type']}'."


def validate_bibliographic_assumptions(tei_text: Element):
    list_bibl = parse_tei.get_elements_by_tag(tei_text, 'listBibl')[0]
    bibl_structs = parse_tei.get_elements_by_tag(list_bibl, 'biblStruct')
    for bibl_struct in bibl_structs:
        analytic = parse_tei.get_element_by_tag(bibl_struct, 'analytic')
        monogr = parse_tei.get_element_by_tag(bibl_struct, 'monogr')
        assert monogr is not None, f"bibliographic entry has no monogr element: {parse_tei.make_bibl_string(bibl_struct)}"
        if analytic:
            expected_analytic_tags = {parse_tei.make_tei_tag(tag) for tag in parse_tei.ANALYTIC_FIELDS}
            for child in analytic:
                assert child.tag in expected_analytic_tags, f"unexpected tag in analytic: '{child.tag}'"
        expected_monogr_tags = {parse_tei.make_tei_tag(tag) for tag in parse_tei.MONOGR_FIELDS}
        for child in monogr:
            assert child.tag in expected_monogr_tags, f"unexpected tag in monogr: '{child.tag}'"
        imprint = parse_tei.get_element_by_tag(monogr, 'imprint')
        if imprint:
            expected_imprint_tags = {parse_tei.make_tei_tag(tag) for tag in parse_tei.IMPRINT_FIELDS}
            for child in imprint:
                assert child.tag in expected_imprint_tags, f"unexpected tag in imprint: '{child.tag}'"

def assert_para_has_only_sents(tei_text: Element):
    para_tag = parse_tei.make_tei_tag('p')
    sent_tag = parse_tei.make_tei_tag('s')
    for para in tei_text.iter(para_tag):
        for sent in para:
            assert sent.tag == sent_tag, f"paragraph contains an element tag other than s: '{sent.tag}'"
    return None


def assert_sent_has_only_refs(tei_text: Element):
    sent_tag = parse_tei.make_tei_tag('s')
    ref_tag = parse_tei.make_tei_tag('ref')
    for sent in tei_text.iter(sent_tag):
        for ref in sent:
            assert ref.tag == ref_tag, f"sententce contains an element tag other than ref: '{ref.tag}'"
