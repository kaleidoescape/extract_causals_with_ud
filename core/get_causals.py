import requests
import json
import re

import anytree
from anytree import AnyNode, RenderTree
from anytree.iterators.preorderiter import PreOrderIter

from core.causal_templates import templates as TEMPLATES
from core.config import CORENLP_URL, DEBUG


def get_deps(sentence):
    """
    Get dependency parse and other data of the sentence from Stanford CoreNLP.

    Args:
        sentence (str): a sentence to parse

    Returns:
        data (dict): the dict of the json returned from CoreNLP
    
    Note: see also dependency type docs for CoreNLP: 
          https://universaldependencies.org/en/dep/
    """
    #params = {'properties':'{"annotators": "tokenize,ssplit,lemma,pos,ner,depparse,openie,sentiment"}'}
    params = {'properties':'{"annotators": "depparse,lemma,pos"}'}
    sentence = sentence.encode('utf-8')
    r = requests.post(
        CORENLP_URL, 
        data=sentence, 
        params=params, 
        timeout=60
    )
    data = json.loads(r.text)
    return data


def get_sentence_from_tokens(tokens):
    """Join tokens from CoreNLP into a sentence."""
    return ' '.join([token['originalText'] for token in tokens])


def treeify(deps, tokens):
    """
    Convert the CoreNLP dependency dictionary into a tree representation.

    Args:
        deps (list): a list of CoreNLP basicDependency objects
        tokens (list): a corresponding list of CoreNLP tokens objects

    Returns:
        id_to_node (dict): word id to AnyTree node (root = id_to_node[0])
    """
    id_to_node = {0: 
        AnyNode(
            id=0, 
            gloss=None, 
            dep=None, 
            governor=None, 
            lemma=None,
            pos=None
        )
    }
    id_to_tok = {token['index']:token for token in tokens}

    #create tree nodes
    for item in deps:
        idx = item['dependent']
        id_to_node[idx] = AnyNode(
            id=idx, 
            gloss=item["dependentGloss"],
            dep=item["dep"],
            governor=item['governor'],
            lemma=id_to_tok[idx]['lemma'],
            pos=id_to_tok[idx]['pos']
        )

    #link up all the nodes
    for idx in id_to_node:
        node = id_to_node[idx]
        if idx == 0:
            continue
        else:
            parent_idx = node.governor
            node.parent = id_to_node[parent_idx]

    return id_to_node


def find_dep(node, deps, maxlevel=2):
    """Find specific dependency in the root node."""
    result = anytree.search.findall(
        node,
        lambda node: node.dep in deps, 
        maxlevel=maxlevel
    )
    return result


def remove_dep(node, deps, maxlevel=None):
    """
    Remove specific dependency types from the children of this node. 
    Warning! This cuts up the tree, since we unlink some nodes.
    """
    trash_nodes = find_dep(node, deps, maxlevel) 
    for trash_node in trash_nodes:
        trash_node.parent = None
    return node


def unwrap_conjuncts(node):
    """
    Find child nodes in the node that are labeled with `dep=conj`,
    and return instead a list of nodes, where this node is one 
    element, but with the `conj` children removed from it, and
    each `conj` node is another, separate element.

    Args:
        node (AnyNode): a dependency tree node

    Returns:
        new_nodes (list): a list of this node, and nodes of `dep=conj`

    Warning! This cuts up the tree, since we unlink some nodes.
    """
    new_nodes = []
    conj_ids = set()
    if node.dep in ['nmod', 'obj']:
        conj_nodes = find_dep(node, ['conj'], maxlevel=None) 
        
        new_nodes.extend(conj_nodes)
        conj_ids = set([node.id for node in new_nodes])

        #recreate the children of this node without the conj nodes 
        node.children = tuple([c for c in node.children 
                                 if c.id not in conj_ids])

        new_nodes.append(node) #don't forget to add this node to new nodes

    else:
        new_nodes.append(node)

    #unlink 'and' from these nodes
    for node in new_nodes: 
        for n in PreOrderIter(node):
            if n.lemma in ('and'):
                n.parent = None

    return new_nodes


def get_phrase(node):
    """Convert node back into a correctly ordered string of words."""
    id_to_word = {n.id: n.gloss for n in PreOrderIter(node)}
    phrase = ' '.join([id_to_word[idx] for idx in sorted(id_to_word.keys())])
    return phrase


def linearize_bfs(root): 
    """
    Linearize a dependency tree into a string using breadth-first search.
    """
    visited = {}
    queue = [] 
    linear = []

    queue.append(root) 
    visited[root.id] = True

    while queue: 

        root = queue.pop(0) 
        linear.append(f"{root.id}-{root.dep}-{root.pos}-{root.lemma}")

        for child in root.children: 
            if child.id not in visited: 
                queue.append(child) 
                visited[child.id] = True
    return linear
    

def get_causals(text, debug=None):
    """
    Get causal relationship triples from the sentence of the form
    (sub, predicate, obj).

    Args:
        sentence (string): a sentence ro parse, as a string

    Returns:
        causals_list (list): a list of 5-tuples of
                             (subj, pred, obj, template, sentence) 
    
    """
    if debug is None:
        debug = DEBUG

    deps = get_deps(text)

    sentence_causals = []
    for sentence in deps["sentences"]:
        basic_deps = sentence["basicDependencies"]
        tokens = sentence["tokens"]
        sentence_string = get_sentence_from_tokens(tokens)
        id_to_node = treeify(basic_deps, tokens)
        root = id_to_node[0]
        linear = ' '.join(linearize_bfs(root))

        result = None
        causals = []
        for template in list(TEMPLATES.values()):
            result = template.find(linear)
        
            if not result:
                continue

            if debug:
                print(sentence_string)
                print(RenderTree(root))
                print(linear)
                print(template)

            pred = id_to_node[result['pred']]
            subj = id_to_node[result['subj']]
            obj  = id_to_node[result['obj']]

            #unlink the nodes from their parents to avoid rendering parents
            for elem in [pred, subj]:
                elem.parent = None
                remove_dep(elem, ['punct', 'acl', 'acl:relcl'])

            #unlink children of predicate node to avoid rendering extras
            for child in pred.children:
                #just keep negation which is very important accurate meaning
                if (child.dep == 'advmod' and 
                    child.lemma == 'not' and 
                    child.pos == 'RB'):
                    continue
                child.parent = None

            #relink the case immediately attached to the obj onto the pred
            for child in obj.children:
                case = find_dep(child, ['case'], maxlevel=1) 
                for node in case:
                    node.parent = pred
                remove_dep(child, ['punct', 'acl', 'acl:relcl']) 

            #spread conjuncts out across causals (e.g. w/ 'and' or 'or')
            subjs = unwrap_conjuncts(subj)
            objs = unwrap_conjuncts(obj)
            for subj in subjs:
                for obj in objs:
                    causals.append([
                        get_phrase(subj), 
                        get_phrase(pred), 
                        get_phrase(obj),
                        str(template),
                        sentence_string
                    ])

            break #use the first template that fits
            
        sentence_causals.append(causals)

    return sentence_causals
