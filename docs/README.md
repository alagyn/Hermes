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
Tokens are defined via *regular expression* (a.k.a regex). Hermes uses a regex syntax that is a subset of the Perl regex specification. See [the regex docs](regex.md) for more info. Another important thing to note, is that the Hermes scanner (like most scanners) operates under the *maximal-munch principle* which essentially means that it will always produce the longest token it can, in the case of a tie. This is the difference between turning `interior` into `int erior` or `interior`, if you have tokens that matches `int` and `interior`.

__Parser__:
The parser takes in a stream of tokens, and performs a number of actions as defined by a *Deterministic Finite Automata*. This automata is created from your input grammar. In particular, Hermes consumes a *Context Free Grammar* (CFG) and produces an LALR(1) Automata (More automata flavors may come later).  
`LALR(1) => Look-Ahead Left-To-Right with 1 token look ahead.`  
What this exactly means is mostly unimportant, but know that it means that there are some CFGs that cannot be parsed by Hermes. Sometimes this can be solved with a bit of grammar massaging, but hopefully you aren't creating monster grammars that will cause parse table conflicts.

## [Grammer File Documentation](grammar-files.md)

## CMake Stuff

Variables:
- Set `HERMES_DEBUG` to `ON` to enable a lot of parser debug output. May or may not be useful if you don't know the parse algorithm
- Set `HERMES_DESC_FILE` to a file path to have Hermes generate a detailed description of the automata's rules and states.