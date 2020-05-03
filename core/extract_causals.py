import os
import pandas as pd

from lxml import etree

from core.get_causals import get_causals

PARSER = etree.HTMLParser()

class CausalExtractorError(BaseException):
    """Raise for errors running the causal extractor."""


def clean_text(element):
    """Extract only the text from an XML element (all tags are removed)."""
    return ' '.join(element.itertext())


def extract_metadata(xml_fp):
    """Extract the pmc id, title and abstract text from an XML file."""
    root = etree.parse(xml_fp, PARSER)
    title = clean_text(root.find('.//article-title'))
    pmc_id = clean_text(root.find(".//article-id[@pub-id-type='pmc']"))
    abstracts = root.findall('.//abstract')
    if not abstracts:
        return (pmc_id, title, '')
    abstract = abstracts[0] #sometimes there are mutliple identical abstracts
    cleaned_abstract = clean_text(abstract) 
    return pmc_id, title, cleaned_abstract


def make_txt_csv(texts_dir, output_fp):
    """
    Make a csv of the causals discovered in articles from the texts_dir.

    Args:
        xml_dir (str): filepath to a directory of text files which have
                       one sentence per line
        output_fp (str): filepath to an output csv file
    """
    filenames = os.listdir(texts_dir)
    rows = []
    for i, filename in enumerate(filenames):
        fp =  os.path.join(texts_dir, filename)
        print(f'Searching for causals: {fp}')
        with open(fp, 'r', encoding='utf-8') as infile:
            for line in infile:
                line = line.strip()
                sentence_causals = get_causals(line)
                causals_list = sentence_causals[0] #each line is 1 sentence
                for causal in causals_list:
                    subj, pred, obj, template, sentence = causal
                    d = {
                        'sentence': sentence,
                        'cause': subj,
                        'predicate': pred,
                        'effect': obj,
                        'template': template,
                    }
                    rows.append(d)
    print(f'Processed {i+1} files.')
    df = pd.DataFrame(rows, columns=[
        'sentence', 
        'cause', 
        'predicate', 
        'effect', 
        'template',
    ])
    df.to_csv(output_fp, sep=',')
    print(f'Wrote output to: {output_fp}')


def make_xml_csv(xml_dir, output_fp):
    """
    Make a csv of the causals discovered in xml articles from the xml_dir.

    Args:
        xml_dir (str): filepath to a directory of xml files
                       of articles with <abstract> elements
        output_fp (str): filepath to an output csv file
    """
    filenames = os.listdir(xml_dir)
    rows = []
    for i, filename in enumerate(filenames):
        fp =  os.path.join(xml_dir, filename)
        print(f'Searching for causals: {fp}')
        pmc_id, title, abstract = extract_metadata(fp)
        sentence_causals = get_causals(abstract)
        if sentence_causals:
            for triplets in sentence_causals:
                for triplet in triplets:
                    subj, pred, obj, template, sentence = triplet
                    d = {
                        'sentence': sentence,
                        'cause': subj,
                        'predicate': pred,
                        'effect': obj,
                        'template': template,
                        'article_title': title,
                        'pmc_id': pmc_id,
                        'xml_file': filename 
                    }
                    rows.append(d)
    print(f'Processed {i+1} files.')
    df = pd.DataFrame(rows, columns=[
        'sentence', 
        'cause', 
        'predicate', 
        'effect', 
        'template',
        'article_title', 
        'pmc_id', 
        'xml_file'
    ])
    df.to_csv(output_fp, sep=',')
    print(f'Wrote output to: {output_fp}')


def main(directory, output_csv, input_type):
    """
    Find causals from files in a directory and write
    them to an output csv file. 

    Args:
        directory (str): path to directory of input files
        output_csv (str): path to output csv file to create
        input_type (str): 'xml' or 'txt'
    """
    input_types = ['xml', 'txt']
    if input_type not in input_types:
        raise CausalExtractorError(
            f"Unrecognized input type: {input_type} "\
            f"Expected one of: {input_types}.")
    
    if input_type == 'xml':
        make_xml_csv(directory, output_csv)
    elif input_type == 'txt':
        make_txt_csv(directory, output_csv)


if __name__ == '__main__':
    import fire
    fire.Fire(main)