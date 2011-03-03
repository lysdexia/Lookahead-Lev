#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cherrypy, yaml, json
__author__ = "kphretiq@gmail.com"
"""
Simple "look-ahead" word completion service using Levenshtein distance algorithm
to find closest matches. Meant to be used in conjunction with AJAX call in text
box.

example lookup for "engine shroud" by typing "shroud"

http://localhost:8080/motorbike_parts/?word=s
["back rest", "foot peg", "handle bar", "seat", "spokes", "spring"]
http://localhost:8080/motorbike_parts/?word=sh
["leg shroud", "hub", "wind shield", "foot peg", "engine shroud", "back rest"]
http://localhost:8080/motorbike_parts/?word=shr
["wheel rim", "leg shroud", "engine shroud", "handle bar", "hub"]
http://localhost:8080/motorbike_parts/?word=shro
["engine shroud", "leg shroud", "hub", "back rest"]

It handles mispellings pretty well
http://localhost:8080/animals/?word=shrrew
["shrew", "ferret", "hare"]

Great fun to play with, and not particularly slow!
"""

# upper limit of values returned
# 3 will return a max of 6 and works pretty well.

(LIMIT)=3

class Lev(object):
    def __init__(self, file_path):
        self.words = [str(i).lower() for i in yaml.load(open(file_path))]
    
    def levDist(self, firstWord, secondWord):
        """Find smallest number of changes to change one string to another.
        http://en.wikipedia.org/wiki/Levenshtein_distance."""

        # if we have a 0 length element for our secondWord word, 
        # return length of firstWord, avoiding calculation on empties 
        if len(secondWord) == 0:
            return len(firstWord)

        if len(firstWord) == 0:
            return len(secondWord)

        # always start out with longest, to avoid bollixing your
        # visualizaton. :-)
        if len(firstWord) > len(secondWord):
            firstWord, secondWord = secondWord, firstWord

        # build our matrix
        firstWord_length = len(firstWord) + 1
        secondWord_length = len(secondWord) + 1
        matrix = [range(secondWord_length) for i in range(firstWord_length)]
    
        # March through and count the changes needed to make firstWord ==
		# secondWord
        for i in range(1, firstWord_length):
            for j in range(1, secondWord_length):
                deletion = matrix[i - 1][j] + 1
                insertion = matrix[i][j - 1] + 1
                # count the substitutions
                substitution = matrix[i - 1][j - 1]
                # increment substitution if no match
                if firstWord[i - 1] != secondWord[j - 1]:
                    substitution += 1
                # replace
                matrix[i][j] = min(insertion, deletion, substitution)
    
        # return the sum in the lower right corner.
        return matrix[firstWord_length - 1][secondWord_length - 1] 

    # sometimes splitting the string up will return a better value than
    # considering the entire string as a whole. Works best on shorter stuff
    def split_string(self, word):
        multi = []
        for row in self.words:
            pos = [(self.levDist(word, i), i)[0] for i in row.split(" ")]
            multi.append((min(pos), row))
        multi.sort()
        return multi[0:LIMIT]

    # longer word values work better here.
    def complete(self, word):
        pos = [(self.levDist(word, i), i) for i in self.words]
        # experiment with limiting results. Doesn't seem to help
        # until you have a mother-huge list
        #pos = [i for i in pos if i[0] <= int(len(word) /.3)]
        pos.sort()

        close = [i for i in pos if word in i[1]]
        notso = [i for i in pos if not i in close]
        return [i for i in close + notso][0: LIMIT]

    # lookup happens here
    @cherrypy.expose
    def index(self, word=False):
        if not word:
            return json.dumps(word)
        l = self.complete(word) + self.split_string(word)
        l.sort()
        final = []
        # maintain word order
        for word in l:
            if not word[1] in final:
                final.append(word[1])
        return json.dumps(final)

class Finder(object):
    # just add more paths here
    # ie. if you have a list of muffin tops in a file called muffins.yaml
    # muffin_tops = Lev("muffins.yaml")
    # call with localhost:8080/muffin_tops?word=choco chip
    # or whatever turns you on.
    motorbike_parts = Lev("motorbike_parts.yaml")
    animals = Lev("animals.yaml")
    
    # nothing set for root ... 
    @cherrypy.expose
    def index(self, *args, **kwargs):
        return self.err(args, kwargs)

    # ... or default. Just echo back with an error message.
    @cherrypy.expose
    def default(self, *args, **kwargs):
        return self.err(args, kwargs)

    # default error dump. 
    def err(self, *args, **kwargs):
        return json.dumps({"error": "lookup path not found", "args": args, "kwargs": kwargs})
# You will most likely want to handle this a bit better should you decide
# to use this! :-)
root = Finder()
cherrypy.quickstart(Finder())
