import re

class CausalTemplate(object):
    def __init__(self, caus, pred, subj, obj, order=['pred', 'subj', 'obj']):
        self.inputs = (caus, pred, subj, obj, order)
        self.pred = f"(?P<pred>\d+-{pred}-{caus})"
        self.subj = f"(?P<subj>\d+-{subj}-\w+)"
        self.obj  = f"(?P<obj>\d+-{obj}-\w+)"
        self.order = order
        self.regex = self.compile()

    def compile(self):
        r = f"{getattr(self, self.order[0])}.*? " \
            f"{getattr(self, self.order[1])}.*? " \
            f"{getattr(self, self.order[2])}"
        return r

    def find_substrings(self, sentence):
        matches = re.search(self.regex, sentence)
        if not matches:
            return {}
        result = {
            'pred': matches['pred'],
            'subj': matches['subj'],
            'obj': matches['obj'],
        }
        return result

    def find(self, sentence):
        substrings = self.find_substrings(sentence)
        if not substrings:
            return {}
        result = {
            'pred': int(substrings['pred'].split('-', maxsplit=1)[0]),
            'subj': int(substrings['subj'].split('-', maxsplit=1)[0]),
            'obj': int(substrings['obj'].split('-', maxsplit=1)[0]),
        }
        return result

    def __str__(self):
        return f"caus={self.inputs[0]}, " \
               f"pred={self.inputs[1]}, " \
               f"subj={self.inputs[2]}, " \
               f"obj={self.inputs[3]}, "  \
               f"order={self.inputs[4]}"

    def __repr__(self):
        return f"<CausalTemplate({str(self)})>"

templates1 = [
    CausalTemplate(
        caus='cause', 
        pred='ROOT-NN', 
        subj='nsubj-NN', 
        obj='nmod-NN',
        order=['pred', 'subj', 'obj']
    ),
    CausalTemplate(
        caus='inhibit', 
        pred='xcomp-VB', 
        subj='nsubj:pass-NNP', 
        obj='obj-NN',
        order=['subj', 'pred', 'obj']
    ),
    CausalTemplate(
        caus='cause', 
        pred='ccomp-VB', 
        subj='nsubj-NN', 
        obj='obj-NNS',
        order=['pred', 'subj', 'obj']
    ),
    CausalTemplate(
        caus='cause', 
        pred='acl:relcl-VBZ', 
        subj='nsubj-NNS?', 
        obj='obj-NN',
        order=['subj', 'pred', 'obj']
    ),
    CausalTemplate(
        caus='lead', 
        pred='ROOT-VBZ', 
        subj='nsubj-NN', 
        obj='obl-NN',
        order=['pred', 'subj', 'obj']
    ),
]

templates2 = [
    CausalTemplate(
        caus='associate', 
        pred='ccomp-VBN', 
        subj='nsubj:pass-NN', 
        obj='obl-NN',
        order=['pred', 'subj', 'obj']
    ),
    CausalTemplate(
        caus='result', 
        pred='acl:relcl-VBZ', 
        subj='nsubj-NN', 
        obj='obl-NN',
        order=['subj', 'pred', 'obj']
    ),
    CausalTemplate(
        caus='result', 
        pred='acl:relcl-VBZ', 
        subj='ROOT-NN', 
        obj='obl-NN',
        order=['subj', 'pred', 'obj']
    ),
    CausalTemplate(
        caus='cause', 
        pred='conj-NN', 
        subj='nsubj-NN', 
        obj='nmod-NN',
        order=['subj', 'pred', 'obj']
    ),
    CausalTemplate(
        caus='effective', 
        pred='xcomp-JJ', 
        subj='nsubj-NNP', 
        obj='obj-NN',
        order=['subj', 'pred', 'obj']
    ),
]

templates = {}
i = 0
#these ones are gathered from the simple examples
for template in templates1:
    templates[str(template)] = template
    i += 1
#these are gathered from the xml files
for template in templates2:
    templates[str(template)] = template
    i += 1