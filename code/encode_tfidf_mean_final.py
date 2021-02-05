import gensim
import pdb
from pprint import pprint  # pretty-printer
from sklearn.feature_extraction.text import TfidfTransformer, CountVectorizer
from nltk.tokenize import word_tokenize
import time
import numpy as np

from gensim import corpora, models, similarities
from nltk.corpus import stopwords as s_words

from six import iteritems
import codecs
import string
from keras.preprocessing.sequence import pad_sequences


AVERAGE_WORDS_IN_SENTENCE = 15

def isINT(w):
    try:
        w = int(w)
    except ValueError:
        return 0
    return 1


# WIKIPEDIA_DATASET_PATH="/home/pinkesh/DATASETS/WIKIPEDIA_DATASET/enwiki-latest-pages-articles.xml.bz2"
# documents = ["Human machine interface for lab abc computer applications",
#              "A survey of user opinion of computer system response time",
#              "The EPS user interface management system",
#              "System and human system engineering testing of EPS",
#              "Relation of user perceived response time to error measurement",
#              "The generation of random binary unordered trees",
#              "The intersection graph of paths in trees",
#              "Graph minors IV Widths of trees and well quasi ordering",
#              "Graph minors A survey"]
# 
# 
# # Tokenize the document & Lowercase it
# texts = [[word for word in document.lower().split()] for document in documents]
# print(texts)
# 
# # remove common words and tokenize
# #stoplist = set('for a of the and to in'.split())
# #texts = [[word for word in document if word not in stoplist] for document in texts]
# 
# # remove words that appear only once
# from collections import defaultdict
# frequency = defaultdict(int)
# for text in texts:
#     for token in text:
#         frequency[token] += 1
# 
# texts = [[token for token in text if frequency[token] > 1] for text in texts]
# 
# dictionary = gensim.corpora.Dictionary(texts)
# #dictionary.save('/tmp/deerwester.dict')  # store the dictionary, for future reference
# print(dictionary)
# 
# new_doc = "Human computer interaction"
# new_vec = dictionary.doc2bow(new_doc.lower().split())
# print(new_vec)  # the word "interaction" does not appear in the dictionary and is ignored
# 
# 
# #corpus = [dictionary.doc2bow(text) for text in texts]
# print "Creating wiki corpus"
# wiki = gensim.corpora.wikicorpus.WikiCorpus(WIKIPEDIA_DATASET_PATH) # create word->word_id mapping, takes almost 8h
# pdb.set_trace()
# print "Saving the corpus to file!"
# gensim.corpora.MmCorpus.serialize('wiki_en_vocab200k.mm', wiki) # another 8h, creates a file in MatrixMarket format plus file with id->word
# #gensim.corpora.MmCorpus.serialize('/tmp/deerwester.mm', corpus)  # store to disk, for later use
# #pprint(corpus)
# 
# 
# # Create a TF-IDF transform
# tfidf = gensim.models.TfidfModel(corpus) # step 1 -- initialize a model
# print(tfidf[new_vec]) # step 2 -- use the model to transform vectors


class TFIDFweightedMeanWord2vec(object):
    def __init__(self, samples):
        # tfidf.shape = (no_of_documents x vocab_size)
        self.model = gensim.models.KeyedVectors.load_word2vec_format('GoogleNews-vectors-negative300.bin', binary=True)

        self.stopwords = set(s_words.words('english') + [w for w in string.punctuation])
        self.WIKI_SAVED_DATA_DIR = "/home/pinkesh/250GB_disk/wiki_en_WITH_ALL_TOKENS/"
        # Saved wiki data using gensim script
        if self.WIKI_SAVED_DATA_DIR[-1] != "/":
            sys.exit(1)
        #self.count_transformer, self.tfidf_transformer = self.load_wiki_from_mm()
        self.raw_docs = []
        for i, doc in enumerate(samples):
            split_doc = [sent.lower().split() for (sent, gt) in doc]
            self.raw_docs.append([])
            for sent in split_doc:
                self.raw_docs[-1].extend(sent)
        self.dictionary = corpora.Dictionary(self.raw_docs)
        stoplist = set('for a of the and to in'.split())
        stop_ids = [self.dictionary.token2id[stopword] for stopword in stoplist
            if stopword in self.dictionary.token2id]
        once_ids = [tokenid for tokenid, docfreq in iteritems(self.dictionary.dfs) if docfreq == 1]
        self.dictionary.filter_tokens(stop_ids + once_ids)  # remove stop words and words that appear only once
        self.dictionary.compactify()  # remove gaps in id sequence after words that were removed

        self.id2word = {v:k for k,v in self.dictionary.token2id.iteritems()}
        self.raw_docs = [self.dictionary.doc2bow(doc) for doc in self.raw_docs]
        self.tfidf = models.TfidfModel(self.raw_docs)


#    def load_wiki_from_mm(self):
#        # Load all the data
#        id2word = gensim.corpora.Dictionary.load_from_text(self.WIKI_SAVED_DATA_DIR + 'wiki_en_wordids.txt.bz2')
#        print 'Loaded %d words in dictionary!' %(len(id2word))
#        mm = gensim.corpora.MmCorpus(self.WIKI_SAVED_DATA_DIR + 'wiki_en_tfidf.mm')
#        start = time.time()
#        tfidf = gensim.models.TfidfModel(mm)
#        print "tfidf loading took:", time.time() - start, "seconds"
#    
#    
#        word2id = {v: k for (k, v) in id2word.items()}
#        # To convert from [(0, 1), (4, 1)] -> [(0, 0.5753529387638757), (4, 0.8179052487029117)] use tfidf[vec]
#        # Example tfidf[id2word.doc2bow(['Tom', 'is', 'a', 'boy'])]
#    
#        count_vect = CountVectorizer(vocabulary=word2id)
#        count_vect.vocabulary_ = word2id
#        tfidf_transformer = TfidfTransformer(use_idf=True)
#        return count_vect, tfidf_transformer
  

    def convert_sequence_sample_to_vec(self, sample, groundTruths):
        """ For type2 samples
        """
        # g_ths: Groundtruths
        sample_vec, g_ths = [], []
        for i, sentence in enumerate(sample):
            sent_word = []
            vec = []
            for w in word_tokenize(codecs.decode(sentence, "utf-8")):
                w = w.lower()
                if (w not in self.stopwords) and (not isINT(w)):
                    try:
                        #vec.append(self.model[w])
                        sent_word.append(w)
                    except KeyError:
                        # Skip all the words whose vector representation is not present in the word2vec pre-trained model
                        continue
            if len(sentence) > 0:
                sent_bow = self.dictionary.doc2bow(sent_word)
                sent_tfidf = self.tfidf[sent_bow]
                if len(sent_tfidf) > 0:
                    #sample_vec.append([b for (a,b) in sent_tfidf])
                    for (a,b) in sent_tfidf: 
                        try:
                            vec.append(self.model[self.id2word[a]]*b)
                        except KeyError:
                            # Skip all the words whose vector representation is not present in the word2vec pre-trained model
                            continue
                    if len(vec) > 0:
                        sample_vec.append(np.mean(vec, axis=0))
                        #print len(sample_vec), np.mean(vec,axis=0).shape, sample_vec[-1].shape
                        #pdb.set_trace()
                        g_ths.append(groundTruths[i])

        #sample_vec = pad_sequences(sample_vec, maxlen=AVERAGE_WORDS_IN_SENTENCE, padding="post", truncating="post", value=0.0, dtype=np.float32)

        # Check vstack() or hstack()
        return np.asarray(sample_vec), np.asarray(g_ths).reshape((len(g_ths), 1)) 
    
    def convert_sample_to_vec(self, sample):
        # Convert a whole sample into a vectorized sample directly to be fed to the classifier
        sample_vec = []
        for i, doc in enumerate(sample):
            #assert(type(doc), type([])) # "doc" should be a list of sentences
            doc = " ".join(doc)         # Doc is a list of sentences
    
            tfidf_mat = self.tfidf_transformer.fit_transform(self.count_transformer.fit_transform([doc]))
            sample_vec.append(tfidf_mat)
        
        #np.concatenate((tfidf_mat2.todense(), tfidf_mat2.todense()), axis=1)
        return np.hstack([doc_mat.todense() for doc_mat in sample_vec])
        #tfidf_mat2.todense(), tfidf_mat2.todense(), tfidf_mat2.todense())).shape    
    

if __name__ == "__main__":
    documents = ['This is a boy', 'This is 2nd document']
    vectors = []
    for doc in documents:
        vectors.append(convert_doc_to_vector(doc))
    pdb.set_trace()
