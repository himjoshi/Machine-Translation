

#Importing python modules and .Net localization.dll
import csv
import unicodedata
import numpy as np
from phrasestring import word
from phrasestring import PhraseString
import MTUtils
import MTLangUtils
from functools import reduce
import re
import os
import glob
from shutil import move
from os.path import abspath, exists
from statemachine2 import StateMachine

exec_path = os.path.dirname(os.path.realpath(__file__))+'\\'
test_path =exec_path+'Test'+'\\'
hin_lang_dll=exec_path+'Localization.dll'

#print (test_path)
#
QAMode = False
logtrace=False
local_hot_folder='e:/mt/'
network_hot_folder='//192.168.14.25/public/mt/'
evaluation_path='evaluate/'
evaluation_hot_folder='//192.168.14.25/public/mt/evaluate/'
hot_folder=network_hot_folder
stats_file='mtstats.txt'
stats_path = hot_folder+stats_file
#'//19168.14.25/public/mt/mtstats.txt' #abspath("mtstats.txt")
#stats_path = abspath("mtstats.txt")

#import clr
#Add full path to Localization.dll here
#clr.AddReference(hin_lang_dll)
#from Localization.P9Translation import languageMap

# In[197]:

#Globle variables
ngrams=3
#lang='guph'
lang='gu'
language='Gujarati'
vocseperator='\t'
#vocfile='iit-hi'+lang+'.csv'
vocfile='hi-'+lang+'.voc'


translations = {}
dictstats={}
nGramlog={'newwords':{},'onegrams':{},'ngrams':{},'testfile':''}
#Hindi to language map translator from localization.dll
#hindi2lang = languageMap()
uniquetokens={}
eop_phrase=' ~'


# In[198]:

gu_rep = {" ની ~ના~":"ના ","~વા ~માં~":"વામાં ",
          "~વી આપો": "વી દો","~વી ": "વી "," નો$": "નો"," ના ": "ના ", " ની ": "ની ", " નો ": "નો "," ને ": "ને "," નું ": "નું ", " થી ": "થી ", " માં ": "માં " , " માંથી ": "માંથી ",
          "~માં~":"","~વા ":"વા ","~ના~":""} # define desired replacements here
#gu_rep = {"~વી આપો": "વી દો","~વી": "વી"," નો$": "નો"," ના ": "ના ", " ની ": "ની ", " નો ": "નો "," ને ": "ને "," નું ": "નું ", " થી ": "થી ", " માં ": "માં " , " માંથી ": "માંથી "} # define desired replacements here
mr_rep = { "~ची ~च्या~": "~च्या ","~चा ~ची~": "~चा "}
#mr_rep = {"~ची ~च्या~": "~च्या ", "~ची ~चा~": "~चा ","~चा ~ची~": "~ची ", "~ा~ ~": "ा ~","~च्या~ ": "", "~ा~ ": "", "~ची~ ": "" , "~चा~ ": ""," ~": "",}
# define desired 
bn_repls = (" ~", ""),("~", "")
mr_repls = ("~ची ~च्या~", "~च्या "), ("~ची ~चा~", "~चा "), ("~चा ~ची~", "~ची "),("~ची ~चे~", "~चे "), ("~चा ~चे~", "~चे "), ("~च्या~", ""), ("~ची~", ""),("~चा~", ""),("~चे~", ""),("~ा~ ~", "ा ~"),(" ~", ""),("~ा~", ""),("~ा", "")
gu_repls = (" બધા ~ની~", " ~ની~બધી "),(" ની ~ના~", "ના "),(" નો ~ની~", "ની "),(" ના ~ની~", "ની "),("~વા ~માં~","વામાં "),\
("~વી આપો", "વી દો"),("~વી ", "વી "),(" નો$", "નો"),(" ના ", "ના "),(" નાં ", "નાં "), (" ની ", "ની "), (" નો ", "નો "),(" ને ", "ને "),(" નું ", "નું "), (" થી ", "થી "), (" માં ", "માં "), (" માંથી ", "માંથી "), (" વાળા ", "વાળા "),\
("~યે છે.","યે છીએ."),("~યે છે ","યે છીએ "),("નું ~માં~","માં "),("~માં~",""),("~વા ","વા "),("~ના~", ""),("~ની~", ""),(" ~", ""),("~", "")

# use these three lines to do the replacement
gu_rep = dict((re.escape(k), v) for k, v in gu_rep.items())
gu_pattern = re.compile("|".join(gu_rep.keys()))
mr_rep = dict((re.escape(k), v) for k, v in mr_rep.items())
mr_pattern = re.compile("|".join(mr_rep.keys()))

#Hindi to punjabi scripters
PunjabiScrtipter = {
    
    "ऊंगा" : "वांगा",
    "ऊंगी" : "वांगी",
    "ाता" : "ांदा",
    "ाती" : "ांदी",
    "ाते" : "ांदे",
    "ों" : "ां",
    "ें" : "ो",
    "ूंगी" : "ांगी",
    "ुंगी" : "ांगी",
    "ूंगा" : "ांगा",
    "ुंगा" : "ांगा",
    "ता" : "दा",
    "ती" : "दी",
    "ते" : "दे",
    "एंगे" : "वांगे",
    "ीयता" : "ीअता",
    "ियता" : "िअता",
    "ाएं" : "ाओ"
}

def listJobFolders(atpath):
    subfolders = [f.name for f in os.scandir(atpath) if f.is_dir() ]
    return subfolders
	
def listTextFiles(atpath):
    return next(os.walk(atpath))[2]
    #return glob.glob(atpath+'*.txt")
# In[213]:
def find_ngrams(input_list, n):
    return zip(*[input_list[i:] for i in range(n)])
 
def merge_ngrams(nxgrams,tokens,size,nsize):
    for ngrams in nxgrams:
        biagram=''
        ncount=0
        for ngram in ngrams:
            #print (ngram['type'])
            if ngram['type']=='Zs' and ncount==0:
                break;
            if ngram['type']=='ALP' or ngram['type']=='Zs':
               biagram=biagram+ngram['token']
               ncount +=1
            else:
               break
        if ncount==size:
            #print (biagram.encode('utf-8'))
            tokens.append({'token':biagram,'type':'ALP','ngram':nsize,'ref':ngrams[0]['ref']})
def mapAlphanum(word):
    if (word==''):
        return word
    l=len(word)
    #if l==1:
    #    return word
    if (word[0]>='0' and word[0]<='9'):
        if (word[l-1]>='0' and word[l-1]<='9'):
            return "_CD_"
    if (word[0]>='A' and word[0]<='Z'):
        if (word[l-1]>='0' and word[l-1]<='9'):
            return "_ID_"
    return word
	
def tokenize(sentence):
    tokens=[]
    lastword=''
    nsentence=' '.join(sentence.split())
    for char in nsentence:
        chtype=unicodedata.category(char)
        print (chtype)
        if chtype.startswith('P') or chtype.startswith('Z'):
            if not lastword=='':
                tokens.append({'token':mapAlphanum(lastword),'type':'ALP','ngram':1,'ref':sentence})
                lastword=''
            tokens.append({'token':char,'type':chtype,'ngram':1,'ref':''})
        else:
            lastword=lastword+char
    if not lastword=='':
        tokens.append({'token':mapAlphanum(lastword),'type':'ALP','ngram':1,'ref':sentence})

    bigrams=find_ngrams(tokens,3)
    trigrams=find_ngrams(tokens,5)
    merge_ngrams(bigrams,tokens,3,2)
    merge_ngrams(trigrams,tokens,5,3)
    
    #return tokens

def mapTranslate(word, language):
    if language=='Marathi':
        return word
    #if language=='Punjabi':
    #    return mapTranslatePun(word,language)
    return MTLangUtils.mapHindiString(word, language)
    #return hindi2lang.mapString(word, language, '')
def normalizeTranslation(text,language):
    if language=='Gujarati':
       return reduce(lambda a, kv: a.replace(*kv), gu_repls, text)
       #return gu_pattern.sub(lambda m: gu_rep[re.escape(m.group(0))], text) 
    if language=='Bengali':
       return reduce(lambda a, kv: a.replace(*kv), bn_repls, text)
    if language=='Marathi':
       return reduce(lambda a, kv: a.replace(*kv), mr_repls, text)
       #return mr_pattern.sub(lambda m: mr_rep[re.escape(m.group(0))], text) 
    return text

def mapTranslatePun(word, language):
    """
    this method made changes on words using trans-script, and then translate to the target language
        word     : word to translate
        language : target language 
    """
    
    length = len(word)
    for key in sorted(PunjabiScrtipter, key=len, reverse=True):
        l = len(key)*-1 #geting negative length
        if(word[l:] == key):
            word = word[0:length+l] + PunjabiScrtipter[key] 

    return MTLangUtils.mapHindiString(word, language).replace(u'੍',u'').replace('ਾੰ','ਾਂ').replace('ਾਇ','ਾਈ')
    #return hindi2lang.mapString(word, language, '').replace(u'੍',u'').replace('ਾੰ','ਾਂ').replace('ਾਇ','ਾਈ')


# In[211]:

def loadTranslationFrom(file) :
    """
    load translations from file; columns should be tab saprated
    this method have hardcode settings for punjabi language
    """
    fieldnames = ['lang', 'hin','state','label']
    dictstats['words']=0
    dictstats['ngrams']=0
    dictstats['language']=language

    with open(file, encoding='utf-8') as csvFile:
        reader = csv.DictReader(csvFile, fieldnames=fieldnames, delimiter=vocseperator)
        i=1
        for row in reader:
            #print(row)
            try:
                hwords=row['hin'].split(',')
                for nextword in hwords:
                    hword=MTLangUtils.normalizeHindi(nextword)
                    if hword not in translations:
                        langword=row['lang']
                        state=row['state']
                        translations[hword] = {'translation':langword,'length':0,'state':state}
                        #source ngram skip length
                        words=hword.split(' ')
                        l=len(words)
                        #translations[hword]['length']=l
                        if len(words)==1:
                            dictstats['words'] +=1
                        else:
                            dictstats['ngrams'] +=1
            except:
                print('Exception:Read Dict'+str(i))
            i+=1
    print (dictstats['words'])
# In[200]:
def getTranslationWithContext(text,language=None):
    """
    returns translation from dictionary if available, else returns empty string
        return: str
    """
    #print (text.encode('utf-8'))
    if text in translations:
        return translations[text]['translation'],'DICT',translations[text]['length']
    if language is None:
        return '','',0
    return mapTranslate(text, language),'ALGO',1

def getTranslation(text,language=None):
    """
    returns translation from dictionary if available, else returns empty string
        return: str
    """
    #print (text.encode('utf-8'))
    if text in translations:
        return translations[text]['translation'],'DICT',translations[text]['state']
    if language is None:
        return '','',''
    return mapTranslate(text, language),'ALGO',''

def getTranslationWithContextn(text,language=None):
    """
    returns translation,rootword,label from dictionary if available, else returns empty string
        return: str
    """
    #print (text.encode('utf-8'))
    if text in translations:
        return translations[text]['translation'],'DICT'
    if language is None:
        return '',''
    return mapTranslate(text, language),'ALGO'
	
def getRawTranslation(text,language=None):
    """
    returns translation from dictionary if available, else returns empty string
        return: str
    """
    if text in translations:
        return translations[text]['translation']
    if language is None:
        return '',''
    return mapTranslate(text, language)
	
def getTokenTranslation(text,forlanguage):
    """
    returns translation from dictionary if available, else returns empty string
        return: str
    """
    if text in translations:
        return translations[text]['translation'],'DICT'
    #words=text.split(' ')
    trans,_,_=translatenew(text,forlanguage)
    #trans=' '.join(getRawTranslation(word,language) for word in words)
    return trans,'ALGO'

# In[201]:
def removeRedundantTokens(uniquetokens):
    final_tokens = [token for token in uniquetokens if (token['ngram']>1 and token['freq'] >= 10)]
    return final_tokens

def doTokenTranslation(text,language,uniquetokens):
    tokens=tokenize(MTLangUtils.normalizeHindi(text))
    for token in tokens:
        token_type=token['type']
        token_word=token['token']
        token_grams=token['ngram']
        token_ref=token['ref']
        if token_type=='ALP':
            tr,kind = getTokenTranslation(token_word,language)
            """if token_word in uniquetokens:
                if uniquetokens[token_word]['freq']<5:
                    uniquetokens[token_word]['ref']=uniquetokens[token_word]['ref']+token_ref+'\r'
            """
            if token_word not in uniquetokens:
                word_token={'translation':tr,'freq':1,'ngram':token_grams,'source':kind,'ref':token_ref}
                uniquetokens[token_word] = word_token#tr
            else:
                uniquetokens[token_word]['freq']+=1
    return uniquetokens

def logthisnGram(phrase,trans,length,logforngrams,logsentencengrams):
    if (phrase==eop_phrase):
        return
    if (phrase==trans):
        return
    if logforngrams is None:
        return
    if logsentencengrams is None:
        return
    if length==0:
        return
    #print (length)
    if length>1:
        logsentencengrams['ngramsCount']+=1
        if phrase not in logforngrams['ngrams']:
           logforngrams['ngrams'][phrase]={'translation':trans}
           logforngrams['ngramsCount']+=1
        return
    if length==1:
        logsentencengrams['onegramsCount']+=1
        if phrase not in logforngrams['onegrams']:
           logforngrams['onegrams'][phrase]={'translation':trans}
           logforngrams['onegramsCount']+=1
        return
    #print ("NEW:"+str(length))
    logsentencengrams['newwordsCount']+=1
    if phrase not in logforngrams['newwords']:
           logforngrams['newwords'][phrase]={'translation':trans}
           logforngrams['newwordsCount']+=1
    return
def translatenewcontext(text, language,logforngrams=None,logsentencengrams=None) :
    """
    translate(text, language) -> str
    Translate text by spliting on spaces; search longest string from start
        text       : text to translate
        language   : target language
    """
    pstring = PhraseString(text)
    outxt = ''
    Parts = pstring.words
    partsLength = len(Parts)
    #print ("WORDS")
    #print (partsLength)
    words=partsLength
    loop = 0
    while(loop < partsLength) :
        parts = Parts[loop : partsLength]
        cc = len(parts)
        #if cc>1:
        
        ss = [''.join([st.word + st.breaker for st in parts[0:cc-i]]) for i in range(0,cc)]

        tr = ''
        for i, s in enumerate(ss) :
            #Remove last separator
            sep=parts[cc-i-1].breaker
            srcwords=cc-i
            print (srcwords)
            l=len(sep)
            if l>0:
                phrase=s[:-l]
            else:
                phrase=s
            #translate phrase get translation & attribute
            tr,_,srcngramwords = getTranslationWithContext(phrase)  #from dictionary
            #tr,_ = getTranslation(phrase)  #from dictionary
            if(tr != '') :
                if (srcwords>srcngramwords):
                    srcwords=srcngramwords
                    sep=parts[cc-srcwords-1].breaker
                tr = tr+sep
                loop += (srcwords-1)
                #loop += (cc-srcwords-1)
                #print ("SIZE")
                #if (cc<=srcwords):
                #    print (cc-srcwords)
                logthisnGram(phrase,tr,cc-srcwords,logforngrams,logsentencengrams)
                break
            elif(i == len(ss)-1) :
                """print ("SIZE*")
                print (phrase)
                print (cc-i)
				"""
                tr = mapTranslate(phrase, language)
                #if not (phrase==tr):
                    #tr=tr+'*'
                #print (tr.encode('utf-8'))
                logthisnGram(phrase,tr,-1,logforngrams,logsentencengrams)
                tr=tr+sep
        loop += 1
        outxt += tr
    final = ''.join([pstring.prefix, outxt, pstring.suffix])
    score=0.0
    if logsentencengrams is not None:
        score=logsentencengrams['Score']
    return MTLangUtils.normalizeLangText(final,language),words,score
    #return normalizeTranslation(final,language),words,score
def gettagstr(tagdict,fortag):
    if fortag not in tagdict:
        index=1
        tagdict[fortag] = {'index':index}
    else:
        index=tagdict[fortag]['index']+1
        tagdict[fortag]['index']=index
    return '<'+fortag+str(index)+'>'

indic_vowelterminating=['এ','ই','উ']
indic_vowels=['অ','আ','ই','ঈ','উ','ঊ','ঋ','ঌ','এ','ঐ','ও','ঔ']
indic_consonants=['ক','খ','গ','ঘ','ঙ','চ','ছ','জ','ঝ','ঞ','ট','ঠ','ড','ঢ','ণ','ত','থ','দ','ধ','ন','প','ফ','ব','ভ','ম','য','র','ল','শ','ষ','স','হ','ড়','ঢ়','য়','ৠ','ৡ','ৰ','ৱ']

global leng
count = 0
char = ''

#finding feature of last word or last term to apply the rules for postposition
def getWordEndFeatures(forward):
    global char
    global ctype
    lastword=''
    nsentence=' '.join(forward.split())
    for char in nsentence:
        ctype=unicodedata.category(char)
        if ctype.startswith('P') or ctype.startswith('Z'):
            if not lastword=='':
                lastword=''
        else:
            lastword=lastword+char
            
    #return char
    if   (char in indic_vowelterminating):
         return 'Er'
    elif (char in indic_vowels):
         return 'r'
    elif (char in indic_consonants):
         ctype=unicodedata.category(char)
         if(ctype == 'Mn' or ctype == 'Mc' or ctype == 'Me'):
             return 'r'
         else:
             return 'er'
    else:
         return 'Er'
         
        
def Convert(ctype):
    if(ctype == 'Mn' or ctype == 'Mc' or ctype == 'Me'):
        return 1
    else:
        return 0

ctype = ''

def LastFeature(sentence):
    global ctype
    lastword=''
    nsentence=' '.join(sentence.split())
    for char in nsentence:
        ctype=unicodedata.category(char)
        if ctype.startswith('P') or ctype.startswith('Z'):
            if not lastword=='':
                lastword=''
        else:
            lastword=lastword+char
        print(char)
    return Convert(ctype)
        
    

def translatenew(text, language,logforngrams=None,logsentencengrams=None,tagmode=False) :
    """
    translate(text, language) -> str
    Translate text by spliting on spaces; search longest string from start
        text       : text to translate
        language   : target language
    """
    global outxt,prstring,count, Start_transitions
    pstring = PhraseString(text)
    Parts = pstring.words
    partsLength = len(Parts)
    leng = partsLength
    outxt = ''
    count = count + 1
    postposition = ['में' , 'पर', 'की', 'के', 'का']
    #print(count)
    
    def Start_transitions(text):
        print ('Start_transitions')
        print (text)
        pstring = PhraseString(text)
        Parts = pstring.words
        partsLength = len(Parts)
        global outxt 
        #print ("WORDS")
        #print (partsLength)
        #words=partsLength
        loop = 0
        tags ={}
        while(loop < partsLength):
            parts = Parts[loop : partsLength]
            cc = len(parts)
            #if cc>1:
            
            ss = [''.join([st.word + st.breaker for st in parts[0:cc-i]]) for i in range(0,cc)]
            
            tr = ''
            for i, s in enumerate(ss) :
                #Remove last separator
                sep=parts[cc-i-1].breaker
                l=len(sep)
                if l>0:
                    phrase=s[:-l]
                else:
                    phrase=s
                print (phrase)
                #translate phrase get translation & attribute
                tr,_,state = getTranslation(phrase)  #from dictionary
                if(phrase not in postposition):
                    tr,_,state = getTranslation(phrase)
                    feature = getWordEndFeatures(tr)
                if(phrase == 'में' or phrase == 'पर'):
                    if(feature == 'er'):
                        feature = 1
                    else:
                        feature = 0
                    tr,_,state = getTranslation(str(feature))
                    print(feature)
                if(phrase == 'की' or phrase == 'के' or phrase == 'का'):
                    tr,_,state = getTranslation(feature)
                    print(feature)
                    #print(tr)
                        
                if(tr != '') :
                    if tagmode:
                        tr=gettagstr(tags,tr)
                    tr = tr+sep
                    loop += (cc-i-1)
                    #print ("SIZE")
                    #if (cc<=srcwords):
                    #    print (cc-srcwords)
                    logthisnGram(phrase,tr,cc-i,logforngrams,logsentencengrams)
                    break
                elif(i == len(ss)-1) :
                    """print ("SIZE*")
                    print (phrase)
                    print (cc-i)
                    """
                    tr = mapTranslate(phrase, language)
                    #if not (phrase==tr):
                        #tr=tr+'*'
                    #print (tr.encode('utf-8'))
                    logthisnGram(phrase,tr,-1,logforngrams,logsentencengrams)
                    tr=tr+sep
            loop += 1
            outxt += tr
            print(outxt)
            if(i==0):
                newState = 'End'
                Parts = Parts[i:]
                partsLength = len(Parts)
                text = ''.join([st.word + st.breaker for st in Parts[0:partsLength]])
                return (newState , text)
            if(state == 'SHai'):   #move to the next state if second form of hai can come
                newState = 'SecondHai'
                Parts = Parts[(partsLength-i):]
                partsLength = len(Parts)
                text = ''.join([st.word + st.breaker for st in Parts[0:partsLength]])
                return (newState, text)
            else:
                newState = 'Start'  #else move to the original start function
                Parts = Parts[(partsLength-i):]
                partsLength = len(Parts)
                #print('going')
                #print(partsLength)
                if(partsLength==1):
                    newState = 'End'
                    return (newState, '')
                text = ''.join([st.word + st.breaker for st in Parts[0:partsLength]])
                return (newState , text)
            
    global End_transitions
    
    def End_transitions(txt):           #end of state table
        return ('End of the state', ' ')
    
    global SecondHai_transitions
    
    def SecondHai_transitions(text):
        print (text)
        pstring = PhraseString(text)
        Parts = pstring.words
        partsLength = len(Parts)
        global outxt
        #print ("WORDS")
        #print (partsLength)
        #words=partsLength
        loop = 0
        tags ={}
        while(loop < partsLength):
            parts = Parts[loop : partsLength]
            cc = len(parts)
            #if cc>1:
            
            ss = [''.join([st.word + st.breaker for st in parts[0:cc-i]]) for i in range(0,cc)]
    
            tr = ''
            for i, s in enumerate(ss) :
                #Remove last separator
                sep=parts[cc-i-1].breaker
                l=len(sep)
                if l>0:
                    phrase=s[:-l]
                else:
                    phrase=s
                #translate phrase get translation & attribute
                if(phrase == 'है'):
                    tr = 'আছে'
                    outxt += tr 
                    newState = 'End'
                    Parts = Parts[i:]
                    partsLength = len(Parts)
                    text = ''.join([st.word + st.breaker for st in Parts[0:partsLength]])
                    return (newState, text)
                tr,_,state = getTranslation(phrase)  #from dictionary
                if(tr != '') :
                    if tagmode:
                        tr=gettagstr(tags,tr)
                    tr = tr+sep
                    loop += (cc-i-1)
                    #print ("SIZE")
                    #if (cc<=srcwords):
                    #    print (cc-srcwords)
                    logthisnGram(phrase,tr,cc-i,logforngrams,logsentencengrams)
                    break
                elif(i == len(ss)-1) :
                    """print ("SIZE*")
                    print (phrase)
                    print (cc-i)
                    """
                    tr = mapTranslate(phrase, language)
                    #if not (phrase==tr):
                        #tr=tr+'*'
                    #print (tr.encode('utf-8'))
                    logthisnGram(phrase,tr,-1,logforngrams,logsentencengrams)
                    tr=tr+sep
            loop += 1
            outxt += tr
        
    declare(text)
    final=''.join([pstring.prefix, outxt, pstring.suffix])
    #final = outxt
    print(final)
    print(count)
    score=0.0
    if logsentencengrams is not None:
        score=logsentencengrams['Score']
    return MTLangUtils.normalizeLangText(final,language),leng,score
    #return normalizeTranslation(final,language),words,score
    
def declare(text):
    m = StateMachine()  #making obect of statemachine class
    m.add_state("Start", Start_transitions)   #adding start transitions class
    m.add_state("SecondHai", SecondHai_transitions)
    m.add_state("End", None, end_state = 1)  #end function to terminate the function
    m.set_start("Start")   #initial starting point of translation 
    m.run(text)  #start the Start_transitions function


def translateNER(text, language,logforngrams=None,logsentencengrams=None,tagmode=False) :

    pstring = PhraseString(text)
    outxt = ''
    Parts = pstring.words
    partsLength = len(Parts)
    #print ("WORDS")
    #print (partsLength)
    words=partsLength
    loop = 0
    tags ={}
    while(loop < partsLength) :
        parts = Parts[loop : partsLength]
        cc = len(parts)
        #if cc>1:
        
        ss = [''.join([st.word + st.breaker for st in parts[0:cc-i]]) for i in range(0,cc)]

        tr = ''
        for i, s in enumerate(ss) :
            #Remove last separator
            sep=parts[cc-i-1].breaker
            l=len(sep)
            if l>0:
                phrase=s[:-l]
            else:
                phrase=s
            #translate phrase get translation & attribute
            tr,_ = getTranslation(phrase)  #from dictionary
            if tr!='':
                tr=phrase
            if(tr != '') :
                tr = tr+sep
                loop += (cc-i-1)
        loop += 1
        outxt += tr
    final = ''.join([pstring.prefix, outxt, pstring.suffix])
    score=0.0
    return final,words,score

def translaterev(text, language) :
    """
    translate(text, language) -> str
    Translate text by spliting on spaces; search longest string from start
        text       : text to translate
        language   : target language
    """
    pstring = PhraseString(text)
    outxt = ''
    Parts = pstring.words
    remaining = len(Parts)
    words=remaining
    loop = 0
    #print ('TRANSLATING')
    while(remaining >=1) :
        #print ('TRANSLATING'+str(loop))
        parts = Parts[0 : remaining]
        cc = len(parts)
        ss = [''.join([st.word + st.breaker for st in parts[i:cc]]) for i in range(0,cc)]
        sep=parts[cc-1].breaker
        l=len(sep)
        #print(remaining,cc,sep.encode('utf-8'))#,tr.encode('utf-8'))

        tr = ''
        #print ('LOOKING')
        for i, s in enumerate(ss) :
            if l>0:
                phrase=s[:-l]
            else:
                phrase=s
            tr,_ = getTranslation(phrase)  #from dictionary
            if(tr != '') :
                print(cc-i,tr.encode('utf-8'))
                tr = tr+sep
                remaining -= cc-i-1
                break
            elif(i == cc-1) :
                tr = mapTranslate(s, language) 
                #print(-1,s,tr)
        remaining -= 1
        outxt = tr+outxt
    final = ''.join([pstring.prefix, outxt, pstring.suffix])
    return MTLangUtils.normalizeLangText(final,language),words,score
    #return normalizeTranslation(final,language),words,score


def translate(text,language,logforngrams=None,logsentencengrams=None,tagmode=False):
    #return translate_Matrix(text,language)
    #return translaterev(text,language)
    if language=='English':
        return translateNER(text,language,logforngrams,logsentencengrams,tagmode)
    else:
        return translatenew(text,language,logforngrams,logsentencengrams,tagmode)
# In[220]:

def translateFile(file2Process, outputfile, language,logstats,tagmode=False) :
    """
    translate strings from file, and writes output to file
        file2Process : input file path to translate
        outputfile   : output file path to write output
        return       : none
    """
    output = []
    lines =  open(file2Process, encoding='utf-8').readlines()
    failures=[]
    wordCount=0
    logforbatchngrams={'newwords':{},'onegrams':{},'ngrams':{},'testfile':file2Process,'newwordsCount':0,'onegramsCount':0,'ngramsCount':0}
    oph = ''
    opl = '' 

    for index,line in enumerate(lines):
        if language=='English':
           line=line.lower()
        line = line.rstrip('\n')
        vals = line.split('\t')
        eng = ''
        expected=''
        if len(vals)>1:
           line = vals[0]
           eng=vals[1]
        if len(vals)>2:
           expected = vals[2]
        if len(vals)>3:
           corrected = vals[3]
           #if not corrected == '':
               #expected=corrected
        logforngrams={'newwordsCount':0,'onegramsCount':0,'ngramsCount':0,'Score':1}
        trans,words,score=translate(line, language,logforbatchngrams,logforngrams,tagmode)
        wordCount+=words
        Match=(expected==trans)
        if not Match:
            failures.append(index+1)
        #print (eng)
        score=MTUtils.calcMTScore(logforngrams)
        op = str(score)+'\t'+line + '\t'+eng+'\t'+ expected+'\t'+ trans+'\t'+str(words)+'\t' + str(Match)+'\n' 
        output.append(op)
        #oph = oph+line + '\n'
        #opl = opl+trans+'\n' 
    #output.append(oph+'\n\n'+opl)
    MTUtils.setBatchLogStats(wordCount,len(failures),len(lines),logforbatchngrams)
    MTUtils.printStats(logforbatchngrams)
    print (outputfile)
    MTUtils.logTranslationOutputs(outputfile,output)
    MTUtils.logStats(stats_path,logforbatchngrams,dictstats)
    
def processSingleFile(file,tododir,wipdir=None,tagmode=False):
    if wipdir is None:
        wipdir=tododir
    todofile=tododir+file
    tokenfile=wipdir+lang+'tokens'+file
    newtokenfile=wipdir+lang+'dict.txt'
    #newtokenfile=wipdir+lang+'dict'+file
    wipfile=wipdir+lang+file
    if logtrace:
        print(todofile)
        print(wipfile)
        print(language)
    translateFile(todofile,wipfile,language,True,tagmode)
    tokenizeFile(todofile,tokenfile,newtokenfile,language)

def translateBatchFile(job,file,atpath):
    wipdir=atpath+'wip/'+job
    donedir=atpath+'done/'+job
    tododir=atpath+'todo/'+job
    if not os.path.exists(wipdir):
        os.makedirs(wipdir)
    if not os.path.exists(donedir):
        os.makedirs(donedir)
    #wipfile=wipdir+lang+file
    todofile=tododir+file #atpath+'todo/'+job+file
    donefile=donedir+file
    processSingleFile(file,tododir,wipdir)
    if QAMode:
        print ('QAMODE')
        return
    move(todofile,donefile)

def translateAllFiles(job,atpath):
    jobpath=atpath+'todo/'+job+'/';
    print (jobpath)
    txtfiles=listTextFiles(jobpath)
    #print (txtfiles)
    for txtfile in txtfiles:
        #print ('processing... '+txtfile)
        translateBatchFile(job+'/',txtfile,atpath)

def translateLanguageJobs(atpath,forlanguage):
    language=forlanguage
    lang=MTLangUtils.languageToLocale(language)
    if lang=='':
        return
    if not prepareDict(lang):
        return
    langjobspath=atpath+language+'/'
    jobspath=langjobspath+'todo/'
    jobs=listJobFolders(jobspath)
    print (jobs)
    for job in jobs:
        print ('processing... '+job)
        translateAllFiles(job,langjobspath)
        
def translateText(text,forlanguage):
    language=forlanguage
    lang=MTLangUtils.languageToLocale(language)
    if lang=='':
        return
    if not prepareDict(lang):
        return
    translatenew(text,language)
    return 1        

    
def translateAllJobs(atpath=hot_folder,forlang=None):
    jobspath=atpath
    languages=forlang
    if languages is None:
        languages=listJobFolders(jobspath)
    #print (jobs)
    for language in languages:
        print ('processing... '+language)
        translateLanguageJobs(atpath,language)

def tokenizeFile(file2Process, outputfile,newtokensfile, language) :
    """
    translate strings from file, and writes output to file
        file2Process : input file path to translate
        outputfile   : output file path to write output
        return       : none
    """
    return
    if language=='English':
        return
    output = []
    ngrams={}
    print ("Tokenizing")
    lines =  open(file2Process, encoding='utf-8').readlines()
    for line in lines :
        line = line.rstrip('\n')
        vals = line.split('\t')
        eng = ''
        if len(vals)>1:
           line = vals[0]
           eng=vals[1]
        doTokenTranslation(line, language,uniquetokens)
    with open(outputfile, mode='w', encoding='utf-8',errors='ignore') as outfile,\
         open(newtokensfile, mode='a', encoding='utf-8',errors='ignore') as dictfile:
         #append to dict file
         #duplicate to be removed in excel
         outfile.write(language+'\t'+'Hindi'+'\t'+'Source'+'\t'+'Ngrams'+'\t'+'Freq'+'\n')  
         unique_onegram=0
         for k, v in uniquetokens.items():
            #ignore english words
            if k== v['translation']:
                continue
            #ignore low frequency nGrams
            if v['ngram']>1 and v['freq']<5:
                continue

            #outfile.write(k+'\t'+v['translation']+'\t'+v['source']+'\t'+str(v['ngram'])+'\t'+str(v['freq']))  
            trans,words,_=translate(str(v['ref']),language)
            if v['ngram']==1 and v['source']=='ALGO':
                dictfile.write(v['translation']+'\t'+k+'\t'+v['source']+'\t'+str(v['ngram'])+'\t'+str(v['freq'])+'\t"'+str(v['ref'])+'"'+'\t'+'"'+trans+'"')  
                dictfile.write('\n')
                unique_onegram+=1
            else:
                outfile.write(v['translation']+'\t'+k+'\t'+v['source']+'\t'+str(v['ngram'])+'\t'+str(v['freq'])+'\t"'+str(v['ref'])+'"'+'\t'+'"'+trans+'"')  
                outfile.write('\n')
         print ("Unique New words = "+str(unique_onegram))
def prepareDict(locale):
    global lang
    global language
    lang=locale
    #print(lang)
    language=MTLangUtils.localeToLanguage(locale)
    #print(language)
    if language=='':
        return False
    translationFile = exec_path+'/Test/'+'hi-'+lang+'.voc'
    #print (translationFile)
    loadTranslationFrom(translationFile)
    return True
# In[221]:
def translateservice(text,locale):
    if not prepareDict(locale):
        return text
    return translate(text,language)
    #return trans

#translate batch text jobs in Language/TODO
def batchservice(forlang=None):
    os.system('cls')
    print ('...Waiting for new batch')
    translateAllJobs(hot_folder,forlang)
def hotfolderbatchservice(forfolder,forlang=None):
    os.system('cls')
    hot_folder=forfolder
    print ('...Waiting for new batch')
    if QAMode:
        print ('QAMODE')
    translateAllJobs(hot_folder,forlang)
def localbatchservice():
    hotfolderbatchservice(local_hot_folder)
def evaluatebatchservice(forlang=None):
    hotfolderbatchservice(evaluation_hot_folder,forlang)
def batchserviceTest(hot_folder):
    os.system('cls')
    print ('...Waiting for new batch at'+hot_folder)
    translateAllJobs(hot_folder)

def fileservice(locale,txtfile):
    if not prepareDict(locale):
        return False
    processSingleFile(txtfile,test_path,None,locale=='en')
    return True


#if __name__== "__main__":
    #translatenew(text,'bn')