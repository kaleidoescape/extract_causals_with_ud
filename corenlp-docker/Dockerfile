FROM ubuntu:latest


ARG CORENLP_RELEASE="2020-04-20"
ARG TZ_REGION="Europe"


RUN apt-get update -y
RUN DEBIAN_FRONTEND="noninteractive" TZ="Europe" apt-get -y install tzdata
RUN apt-get install -y apt-utils \
		default-jre \
		default-jdk \
		ant \
		unzip \
		wget \
		git


RUN wget http://nlp.stanford.edu/software/stanford-corenlp-full-${CORENLP_RELEASE}.zip; \
	unzip stanford-corenlp-full-${CORENLP_RELEASE}.zip; \
	mv stanford-corenlp-full-${CORENLP_RELEASE} CoreNLP; \
	cd CoreNLP; \
	export CLASSPATH=""; for file in `find . -name "*.jar"`; do export CLASSPATH="$CLASSPATH:`realpath $file`"; done

ENV PORT 9000

EXPOSE 9000

WORKDIR CoreNLP

CMD java -cp '*' -mx4g edu.stanford.nlp.pipeline.StanfordCoreNLPServer