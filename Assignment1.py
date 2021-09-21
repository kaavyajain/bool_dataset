#dataset: few paragraphs from short stories by Russian author Anton Chekhov
import nltk, time, re
import numpy as np
import pandas as pd
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.stem.porter import PorterStemmer
from flask import Flask, render_template, request
from collections import defaultdict
from nltk.stem import PorterStemmer
from nltk.corpus import stopwords

#declaring variables 
porter = PorterStemmer()
lemma = WordNetLemmatizer()
stem = PorterStemmer()
swords = set(stopwords.words("english"))
punct = "?:!""''[]|.,&;*(-)—"
swordsq = set(stopwords.words("english"))
swordsq.remove("and")
swordsq.remove("or")
swordsq.remove("not")

def soundexterm(term):
    term = term.upper()
    soundex = ""
    soundex += term[0]
    mapping = {"AEIOUHWY" : ".", "BFPV" : "1", "CGJKQSXZ" : "2", "DT" : "3", "L" : "4", "MN" : "5", "R" : "6"}
    for char in term[1:]:
        for key in mapping.keys():
            if char in key:
                code = mapping[key]
                if code != soundex[-1]:
                    soundex += code
    soundex = soundex.replace(".","")
    soundex = soundex[:4].ljust(4,"0")
    return soundex

invertdict ={} 
documents = {} 
posdict ={} 
tmp_dict ={} 
bidict ={}
soundexdict ={} 
paired_list = {}
postfix = []
postfix2 = []

def tokenize(s):
    token = word_tokenize(s)
    return token

for i in range(1, 41):
    doc_no = i
    with open("C:/Users/kaavk/OneDrive/Desktop/ACode/IR/A1/dataset/ShortStories/doc_"+str(doc_no)+".txt",'r',errors = 'ignore') as doc:
        #iterating through the documents and storing lines
        next(doc, None)
        f=doc.read()
        s=f.replace('\n',' ')
        key= 'doc_' + str(doc_no) 
        #initialising the dictionary for the current key with an empty list
        documents.setdefault(key, [])
        #adding the comments of the file to the lsit for the current key in the dictionary
        documents[key].append(s)
        #tokenizing the file contents and storing it in tokenized_word
        tokens = tokenize(s)
        removal_words = []
        #filtering the content by removing stop words like articles 'all', 'the', etc
        for w in tokens:
            if w not in swords:
                removal_words.append(w)
        #stemming the filtered words by using stemmed_words (removing the suffix)
        stem =[]
        for w in removal_words:
            stem.append(porter.stem(w))
        #lemmatizng the stemmed words (to change it into the base word)
        lem = []
        for w in stem:
            lem.append(lemma.lemmatize(w,"v"))
        #removing the punctuations and storing the final pre-processed words into lemmatised words
        for word in lem:
           if word in punct:
              lem.remove(word)        
        #iterating through the final tokens to define the dictionary
        for x in lem:
            key = x
            invertdict.setdefault(key,[])
            #adding the current doc to the list corresponding the key
            invertdict[key].append(doc_no)
            #removing the duplicate doc number from the key

    invertdict = {a:list(set(b)) for a, b in invertdict.items()}
    #making a list of words of biword index
    list_length = len(lem)
    list_pairs = []
    for l in range(0,list_length-1):
        list_pairs.append([lem[l] + " " + lem[l+1]])
    #iterating through the list of paired tokens to define the dictionary for the biword index
    for x in list_pairs:
        s2 = ""
        for y in x:
            s2+=y
        key = y
        bidict.setdefault(key,[])
        #condition to prevent duplicates
        if doc_no not in bidict[key]:
            bidict[key].append(doc_no)

    #POSITIONAL INDEX
    #storing pre-processed words without removing stop wrds to get accurate count
    stemmed_tokens=[]
    for w in tokens:
        stemmed_tokens.append(porter.stem(w))

    lemmed_tokens=[]
    for w in stemmed_tokens:
        lemmed_tokens.append(lemma.lemmatize(w,"v"))

    for word in lemmed_tokens:
        if word in punct:
            lemmed_tokens.remove(word)

    #initializing word count of documents
    a=0  #to keep track of the position 
    tmp_dict.clear()
    #temp_dict used to store a list of positions of words in current file
    for x in lemmed_tokens:
        key = x.lower()
        tmp_dict.setdefault(key,[])
        tmp_dict[key].append(a)
        a=a+1  #incrementing the position every time in the temp dictionary
    for x in tmp_dict:
        if invertdict.get(x):
            temp={}
            temp[doc_no]=tmp_dict.get(x)
            posdict.setdefault(x,[])
            posdict[x].append(temp)
    #finding soundex for tokenized words
    for w in lem:
        soundex_w = soundexterm(w)
        soundex_number = soundex_w
        soundexdict[soundex_number]=w

def ANDquery(word1, word2):
    if((word1) and (word2)):
        return set(word1).intersection(word2)
    else:
        return "[]"

def ORquery(word1, word2):
    return set(word1).union(word2)

def NOTquery(a):
    notq_docs = list(range(1,41))
    return set(notq_docs).symmetric_difference(a)

class Conversion:
    def __init__(self,capacity):
        self.array = []
        self.output = []
        self.top = -1
        self.capacity = capacity
        self.precedence = {'or':1, 'and':2, 'not':3}
    
    def isOperand(self, ch):
        return (ch=="and" or ch=="not" or ch=="or" or ch=='(' or ch==')')
    def notGreater(self, i):
        try:
            a = self.precedence[i]
            b = self.precedence[self.peek()]
            return True if a <= b else False
        except KeyError:
            return False

    def isEmpty(self):
        return True if self.top == -1 else False

    def peek(self):
        return self.array[-1]
    
    def pop(self):
        if not self.isEmpty():
            self.top -= 1
            return self.array.pop()
        else:
            return "$"
    
    def push(self, op):
        self.top += 1
        self.array.append(op)
    
    def inToPost(self, exp):
        tokens2 = tokenize(exp)
        for i in tokens2:
            if self.isOperand(i)==False:
                self.output.append(i)
            elif i ==')':
                while((not self.isEmpty()) and self.peek() !='('):
                    a = self.pop()
                    self.output.append(a)
                if (not self.isEmpty() and self.peek() != '('):
                    return -1
                else:
                    self.pop()
            elif i == '(':
                self.push(i)
            else:
                while(not self.isEmpty() and self.notGreater(i)):
                    self.output.append(self.pop())
                self.push(i)
        while not self.isEmpty():
            self.output.append(self.pop())
        postfix.extend(self.output)
        
    def inToPostlist(self, qList):
        for i in qList:
            if self.isOperand(i)==False:
                self.output.append(i)
            elif i == ')':
                while((not self.isEmpty()) and self.peek()!='('):
                    a = self.pop()
                    self.output.append(a)
                if (not self.isEmpty() and self.peek() != '('):
                    return 1
                else:
                    self.pop()
            elif i == '(':
                self.push(i)  
            else:
                while(not self.isEmpty() and self.notGreater(i)):
                    self.output.append(self.pop())
                self.push(i)
        while not self.isEmpty():
            self.output.append(self.pop())
        postfix2.extend(self.output)

def boolquery():
    #general query processing using inverted index
    #taking input for the query and converting it to postfix
    postfix.clear()
    query = input("Enter boolean query: ")
    obj = Conversion(len(query))
    obj.inToPost(query.lower())
    print("The postfix list of words is: ", postfix)
    #filtering the content by removing any stopwords occuring
    remove2 = []
    for w in postfix:
        if w not in swordsq:
            remove2.append(w)
    #stemming the filtered words
    stem2=[]
    for w in remove2:
        stem2.append(porter.stem(w))
    #lemmatizing the stemmed words
    lem2=[]
    for w in stem2:
        lem2.append(lemma.lemmatize(w,"v"))
    #removing the punctuations and storing the final pre-processed words into lemmatised words
    #punct = "?:!""''[]|.,&;*(-)—"
    for word in lem2:
        if word in punct:
            lem2.remove(word)

    #general query processing using inverted index
    result2 = []
    #iterating through the pre-processed queries and processing the queries to return the list of docs
    for i in lem2:  
        #if i is not equal to "and", "or" and "not", we look for its inverted index
        if (i != "and" and i!="or" and i!="not"):
            i=invertdict.get(i)
            if i==None:
                result2.append([])
            else:
                result2.append(i)
        if result2:
            if (i=="and"):
                w1 = result2.pop()
                w2 = result2.pop()
                result2.append(ANDquery(w1,w2))
            elif(i=="or"):
                w1 = result2.pop()
                w2 = result2.pop()
                result2.append(ORquery(w1,w2))
            elif(i=="not"):
                w1 = result2.pop()
                result2.append(NOTquery(w1))
    if result2:
        print("List of documents is: ",result2.pop())


def phrasequery():
    #list to store query in biword form
    qList = []
    #taking input for the query 
    biquery = input("Enter biword query: ")
    #tokenizing the query
    tokens3 = tokenize(biquery)
    #filtering the content by removing stop words
    remove3 = []
    for w in tokens3:
        if w not in swordsq:
            remove3.append(w)
    # stemming the filtered words using porter stemmer
    stem3=[]
    for w in remove3:
        stem3.append(porter.stem(w))
    #lemmatizing the stemmed words
    lem3=[]
    for w in stem3:
        lem3.append(lemma.lemmatize(w,"v"))
    #remove punctuations  
    for word in lem3:
        if word in punct:
            lem3.remove(word)
    h=0
    #empty string to store the query
    cStr=""
    k = len(lem3)
    while h<k:
        while h<k and (lem3[h]!="and" and lem3[h]!="or" and lem3[h]!="not"):
            cStr = cStr+" "+lem3[h]
            h=h+1
        #adding current phrase to query list
        if cStr[1:] not in qList:
            qList.append(cStr[1:])
            cStr=""  
        #adding and, or, not to our query list
        if h<k and (lem3[h]=="and" or lem3[h]=="or" or lem3[h]=="not"):
            qList.append(lem3[h])
        h=h+1
    print("Processsed biword query is: ",qList)
    #converting input query to postfix form
    postfix2.clear()
    obj = Conversion(len(qList))
    obj.inToPostlist(qList)
    print("The postfix list of biwords is: ",postfix2)
    #query processing for biword index
    result3 = []
    #iterating through pre-processed queries and processing the queries to return the list of docs
    for i in postfix2:
        if (i!='and' and i!='or' and i!='not'):
            i= bidict.get(i)
            if i==None:
                result3.append([])
            else:
                result3.append(i)
        if result3:
            if (i=="and"):
                w1 = result3.pop()
                w2 = result3.pop()
                result3.append(ANDquery(w1,w2))
            elif(i=="or"):
                w1 = result3.pop()
                w2 = result3.pop()
                result3.append(ORquery(w1,w2))
            elif(i=="not"):
                w1 = result3.pop()
                result3.append(NOTquery(w1))
    if result3:
        print("List of documents is: ",result3.pop())

def proxquery():
    proquery = input("Enter proximity query: ")
    #tokenizing the query
    tokens4 = tokenize(proquery)
    remove4 = []
    #filtering the content by removing any stopwords
    for w in tokens4:
        if w not in swordsq:
            remove4.append(w)
    #stemming
    stem4 = []
    for w in remove4:
        stem4.append(porter.stem(w))
    #lemmatizing the filtered words
    lem4=[]
    for w in stem4:
        lem4.append(lemma.lemmatize(w,"v"))
    #removing the punctuations
    for word in lem4:
        if word in punct:
            lem4.remove(word)
    #finding distance between words
    word1 = lem4[0]
    word2 = lem4[2]
    dist = int(lem4[1][1:])
    #list1 is used to store the list of documents and the respective positions where word1 occurs
    list1 = []
    #list2 is used to store the list of documents and the respective positions where word2 occurs
    list2 = []
    #common dictionary is used to store the documents and positions where the reqd condn is satisfied
    common_dict={}
    if word1 in posdict:
        for w in posdict[word1]:
            list1.append(w)
    else:
        list1.append([])
    #if word2 exists, we store the respective list in list2, else we store an empty list in list2
    if word2 in posdict:
        for w in posdict[word2]:
            list2.append(w)
    else:
        list2.append([])
    for i in list1:
        for y in i:
            for j in list2:
                for k in j:
                    if y==k:
                        common_list = []
                        for w1 in i[y]:
                            for w2 in j[k]:
                                if w1-w2<=dist and w1-w2>=(dist*-1):
                                    common_list.append((w1,w2))
                                    common_dict[y]=common_list
    print("List of documents: ",common_dict)

def soundexquery():
    postfix2.clear()
    #taking input for the query
    squery=input("Enter soundex query: ")
    #tokenizing the query
    tokens5 = tokenize(squery)
    #converting the tokenized query in postfix form
    obj = Conversion(len(tokens5))
    obj.inToPostlist(tokens5)
    #qsoundex stores the query in sounex form
    qsoundex=[]
    #filtering the content by removing the stopwords
    remove5 = []
    for w in tokens5:
        if w not in swordsq:
            remove5.append(w)
    #stemming the filtered words
    stem5 = []
    for w in remove5:
        stem5.append(porter.stem(w))
    lem5=[]
    for w in stem5:
        lem5.append(lemma.lemmatize(w,"v"))
    for word in lem5:
        if word in punct:
            lem5.remove(word)

    postfix2.clear()
    obj = Conversion(len(lem5))
    obj.inToPostlist(lem5)
    print("The postfix list of words is: ", postfix2)
    #converting words in the query of soundex, when they're not and, or, not.
    #(AND, OR and NOT are used for query pre-processing)
    for w in postfix2:
        if w!="and" and w!="or" and w!="not":
            w=soundexterm(w)
        qsoundex.append(w)
    print("Processed soudex query is: ",qsoundex)

    #query processing for mis-spelled words (SOUNDEX)
    result5 = []
    #iterating through the soundex queries
    for i in qsoundex:
        if(i!='and' and i!='or' and i!='not'):
            if i in soundexdict:
                if soundexdict[i] in invertdict:
                    result5.append(invertdict[soundexdict[i]])
                else:
                    result5.append([])
        if result5:
            if(i=='and'):
                w1= result5.pop()
                if len(result5)==0:
                    w2 = []
                else: 
                    w2=result5.pop()
                result5.append(ANDquery(w1,w2))
            elif(i=='or'):
                print(result5)
                w1=result5.pop()
                if len(result5)==0:
                    w2=[]
                else:
                    w2=result5.pop()
                result5.append(ORquery(w1,w2))
            elif (i=='not'):
                w1=result5.pop()
                result5.append(NOTquery(w1))
    if result5:
        print("List of documents: ",result5.pop())

if __name__ == "__main__":
    d = input("""
    Inverted, Positional, Biword and Soundex dictionaries have been made. 
    Enter 1 to see: 
    """)
    if d=="1":
        print("""INVERTED DICTIONARY: 
        """,invertdict)
        print("""POSITIONAL DICTIONARY: 
        """,posdict)
        print("""BIWORD DICTIONARY: 
        """,bidict)
        print("""SOUNDEX DICTIONARY: 
        """,soundexdict)

    print("""
    MENU:
    1.General Boolean Query
    2.Biword Phrase Query
    3.Proximity Search Query
    4.Soundex Query
    (Press enter key to exit anytime)
    """)
    ans =True
    while ans:
        print("Choice: ")
        ans = input()
        if ans=="1":
            boolquery()
        elif ans=="2":
            phrasequery()
        elif ans=="3":
            proxquery()
        elif ans=="4":
            soundexquery()
        