Subset of Perl regex.

Grouping: `(asdf)`
Repetition: `a+ b* c? d{1, 4} e{2,} f{4}`
Alternation: `(abc)|(def)`
Character classes: `[ab][a-z][0-9][^xyz]`
- Digits: `\d`
- Uppercase: `\u`
- Lowercase: `\l`
Lookahead: 
- Positive: `(?=abc)`
- Negative: `(?!abc)`

There is not concept of the start or end of line anchors: `^ $` since they
do not make much sense in the context of Hermes since we consume a stream
of characters.

