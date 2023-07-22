# Hermes Docs

## Overview
Hermes is a combination scanner+parser generator, essentially Flex + Bison rolled into one. If you don't know what that means, here is the rundown:  

__Scanner__:
The scanner takes in a stream of input text, and produces an output stream of discrete *tokens* (Scanners are also sometimes also referred to as Tokenizers). Tokens are defined as non-overlapping, discrete substrings of the input text.  
For example, this snippet of C++:  
```c++
int foobar = 25;
```
could be turned into the following tokens:
```
TYPE_INT NAME OPERATOR_EQUALS LITERAL_INT SEMICOLON
```
Tokens are defined via *regular expression* (a.k.a regex), in particular they must conform to the [default boost regex syntax](https://www.boost.org/doc/libs/1_82_0/libs/regex/doc/html/boost_regex/syntax/perl_syntax.html). Another importnant thing to note, is that the Hermes scanner (like most scanners) operates under the *maximal-munch principle* which essentially means that it will always produce the longest token it can, in the case of a tie. This is the difference between turning `interior` into `int erior` or `interior`, if you have tokens that matches `int` and `interior`.

__Parser__:
The parser takes in a stream of tokens, and performs a number of actions as defined by a *Deterministic Finite Automata*. This automata is created from your input grammar. In particular, Hermes consumes a *Context Free Grammar* (CFG) and produces an LALR(1) Automata (More automata flavors may come later).  
`LALR(1) => Look-Ahead Left-To-Right with 1 token look ahead.`  
What this exactly means is mostly unimportant, but know that it means that there are some CFGs that cannot be parsed by Hermes. Sometimes this can be solved with a bit of grammar massaging, but hopefully you aren't creating monster grammars that will cause parse table conflicts.