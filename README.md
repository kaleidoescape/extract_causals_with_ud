# Extract Causals with UD

Extract causal relationships from sentences from scientific articles, using a rule-based approach with Universal Dependencies. Causal relationships consist of cause-effect relationships, which in this case, will be represented as a triplet of `(subject, predicate, object)` (SPO), where the cause is represented as the subject and the effect is represented as the object. For example:

```
The Norwalk virus is the prototype virus that causes epidemic gastroenteritis infecting predominantly older children and adults.
SPO: The Norwalk virus - causes - epidemic gastroenteritis
```

## Quickstart

Install the requirements to run these python scripts (recommended to install into an environment, e.g. virtualenv or conda):

```
pip install -r requirements.txt
```

### CoreNLP docker

First, build and run the included docker for Stanford CoreNLP. This will run a server on your local host at port 9000, which will be used by the rest of the code to get Universal Dependency information for help in finding causal relationships in sentences.

```
docker build -f ./corenlp-docker/Dockerfile -t corenlp .
docker run -it -p 9000:9000 --name corenlp corenlp
```

### Extracting causals

You can run this script on your own .txt or .xml files, using the following arguments. Input types include `xml` for a directory of xml files, from which only the `<abstract>` section will be parsed, and `txt` for a directory of text files with one sentence per line.

```
python run.py DIRECTORY OUTPUT_CSV INPUT_TYPE

DESCRIPTION
    Find causals from files in a directory and write them to an output csv file.

POSITIONAL ARGUMENTS
    DIRECTORY
        path to directory of input files
    OUTPUT_CSV
        path to output csv file to create
    INPUT_TYPE
        'xml' or 'txt'
```


To run the sample txt or xml files:

```
python run.py data/txts txts.csv txt
```

```
python run.py data/xmls xmls.csv xml
```

## Approach

In this solution, we follow a template based approach, making use of Universal Dependencies (UD) and parts of speech provided by CoreNLP. The UDs from CoreNLP's json output are converted into a tree structure and the tree is linearized using a breadth-first approach. 

Templates search over these linearized dependencies to find subject-predicate-object matches. Templates are constructed from the following subparts:

```
caus:  the lemma of the causal word that makes up the head of the predicate
pred:  the UD dependency type, part of speech, and caus (lemma of causal head)
subj:  the UD dependency type and the part of speech of the subject head 
obj:   the UD dependency type and the part of speech of the object head
order: the order of these structures in the linearized dependency (SPO or PSO); e.g. passives have reversed order 
```

The final template constructed from these pieces is a regular expression that searches over the string of the linearized dependency, extracting nodes with their index. For example, the following template 

```
caus='cause', 
pred='ROOT-NN', 
subj='nsubj-NN', 
obj='nmod-NN',
order=['pred', 'subj', 'obj']
```

would create the following regex:

```
"?P<pred>\d+-ROOT-NN-cause).*? (?P<subj>\d+-nsubj-NN-\w+).*? (?P<obj>\d+-nmod-NN-\w+)"
```

This regex will capture a 'ROOT' predicate node with a 'cause' lemma, followed by an 'nsubj' subject node (with any lemma), followed by an 'nmod' node (with any lemma). Any number and type of nodes can appear in between these nodes.

Following this, some simple heuristics are applied to attempt to:
- separate conjunctions into separate entries, 
- move 'case' words from the object onto the predicate e.g. to convert ('x', 'cause', 'of something') into ('x', 'cause of', 'something')
- remove extra adjuncts (such as relative clauses) from the nodes, which would add too much extraneous information to the cause-effect extractions
- remove punctuation

## Future Work

Our approach has a number of limitations. Crucially, the regular expression templates search for nodes from the left to the right. A better approach would be to search outward from the predicate node, as in [Khoo et al. 2000](https://www.aclweb.org/anthology/P00-1043.pdf). Additional methods are described in a detailed survey from [Asghar 2016](https://arxiv.org/pdf/1605.07895.pdf). More recently, [Dasgupta et al. 2018](https://www.aclweb.org/anthology/W18-5035.pdf) used a BiLSTM incorporating word embeddings and linguistic features into one system. 
