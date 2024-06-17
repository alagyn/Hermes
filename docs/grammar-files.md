
## Grammar Files
Hermes grammar files are based on the "Extended Backus-Naur Form" and look rather similar to Bison grammars.  
They have three main components:
- Tokens
- Grammar Rules
- Directives

All three of these can be defined in an arbitrary order and interleaving, but the key thing to note is that __tokens have precedence based upon the order they are defined in.__ I.E. in case of a tie, the token that is defined first will win.

__Hermes grammars can contain line comments starting with # anywhere except code blocks. Pounds are safe to use within regex.__

### Tokens
Tokens are defined as name+regex tuple. By convention, tokens are usually named with full uppercase, but they can be any combination of letters and underscores.
``` 
NAME = "[a-zA-Z_]+";
SEMICOLON = ';';
STRING = "\"[^\"]+\"";
```
Regex strings can be wrapped in either single or double quotes to the same effect, and inner quotes can be escaped with backslashes. Otherwise, regex follow the specification [described here](regex.md). You cannot have more than one token with the same name, and you cannot have an empty regex string.

### Rules
Rules describe your Context-Free-Grammar. They are composed of Tokens (a.k.a Terminals) and Nonterminals. Nonterminals are best described as intermediate steps, where terminals are your base building blocks. New nonterminals are created simply by creating a rule with a new name on the left hand side. The right hand side is composed of any number of "symbols" (Terminals and Nonterminals), then a code block enclosed in curly brackets (more on that later) and ends with a semicolon. By convention, nonterminals are all lowercase, but again they can be any combination of letters and underscores.
```
expression = expression PLUS term {};
```
Symbols referenced on the right hand side do not need to be defined prior to this rule. A single nonterminal can have multiple rules with different symbols. Creating a duplicate rule with the same LHS and RHS will produce undetermined errors. 
```
expression = expression PLUS term {};
expression = expression MINUS term {};
```
Because this is a common operation, we have a shorthand:
```
expression = expression PLUS term {}
    | expression MINUS term {};
```
Note the location of the semicolon. Whitespace anywhere in the rule's definition is ignored, so go crazy with your formatting. I prefer this style:
```
expression
    = expression PLUS term { /* short code */ }
    | expression MINUS term 
    {
        // long code
    }
    ;
```
There is a single special rule that you can define.
```
expression 
    = EMPTY {}
    | expression PLUS term {}
    ;
```
The `EMPTY` keyword can only be defined in a rule by itself, and it declares that this nonterminal can be the "empty string" i.e. it can be reduced to nothing. For instance, a 
c++ function can be defined as 
```
func = type name OPEN_PAREN arg_list CLOSE_PAREN {};
arg_list
    = arg COMMA arg_list {}
    | arg {}
    | EMPTY {}
    ;
```
This means a functions arguments can be a list, a single argument, or nothing.

#### Starting rule
**The first rule/nonterminal you define is special**. This defines your *starting rule and symbol* as well as what is considered a valid input. When your starting rule is matched, the input is considered valid and the parse is done. **It is best practice to only have a single rule for your start symbol.** You can just have an intermediate nonterminal if you need to have alternatives. This is also done automatically if you do define more than one rule for your starting symbol.
```
output = expr {};

# Avoid having these alternatives on "output"
expr
    = expr PLUS term {}
    | expr MINUS term {}
    ;
```

### Directives
Directives are special statements that define extra data for the generated c++ code. All directives start with a `%` immediately followed by the directive name. Multiline directives values start and end with `%%` (see `%header`)

Available directives:

`%return`: **This directive is required for every grammar**, and can only be defined once. It declares the c++ datatype that is returned by the rule code blocks.
```
%return int
# Or something else
%return MyClass*
```

`%header`: This directive allows you to add arbitrary code to the top of the generated parser. This is primarily useful for adding `#include` directives or namespace declarations. This directive can be defined as many times as needed (but usually only once)
```c++
%header %%
#include <string>
#include <memory>
#include <map>

using namespace std;

// ... etc

%%
```

`%ignore`: This directive creates a hidden token type that is parsed and ignored by the scanner. This is primarily useful for creating comments in your language.
```
# C style line comments
%ignore "//[^\n]*\n?"
# C style block comments
%ignore "/\*((?!\*/)(.|\n))*?\*/"
```

`%import`: this directive allows you to import the definitions of another gramar file into the current grammar. Imported files are defined globally, you do not need to import the same file into multiple subfiles. Paths are relative to the current file. Can be specified multiple times. Files are processed as a queue, and imported files are not processed until after the current file finishes. This is not typically an issue, but **be wary of defining terminals in multiple files as import order can change precedence.**
```
%import terminals.hm
%import folder/otherGrammar.hm
```

### Code blocks
A code block can be defined for every rule. This code block contains a c++ function that is executed whenever its rule is matched. This function's return type is defined by the `%return` directive and is the same for every function. In your code, you can access the data for each of the symbols in the rule. They can accessed in one of two ways: via the index of the symbol `$0`, or the symbol name `$name`. However, you can only reference them by name if the symbol does not appear more than once in the rule. When you reference a terminal, you are given a `std::string`, if you reference a nonterminal, you are given evaluated value of the nonterminal determined by your `%return` type.
```c++
%return int

expr = expr PLUS INT
{
    // INT is a terminal, therefore we need to parse it, here we reference it by name
    int val = std::stoi( $INT );
    // This expression evaluates as whatever the LHS is plus the new int
    // This value is what will be used whenever this expr is evaluated later
    // Reference expr by index
    return $0 + val;
};
```

**If you do not define a code block for your rule,** a default one will be generated of the form
```c++
{
    return $0;
}
```
This is useful for simple pass-through nonterminals

```c++
x = a b
  {
    // do some processing...
    return $a;
  }
  | a // simply return a
  ;
```


See `calculator.hm` for a more complete example.