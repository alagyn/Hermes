#include <regex_test_utils.h>

TEST_CASE("Lookahead", "[regex]")
{
    {
        // must start with ab
        // and can contain any combination of [abcd] that is not ba
        hermes::Regex r("ab((?!ba)[abcd])*");

        check(r, "ab");
        check(r, "abcd");
        check(r, "abcba", false, false);
        check(r, "abcdba", false, false);
        check(r, "abbacc", false, false);
        check(r, "abcbac", false, false);
    }

    {
        // typical c-style multiline comment
        hermes::Regex r("/\\*((?!\\*/)(.|\n))*\\*/");

        check(r, "/* asdf */");
        check(r, "/*a*s\nd/f*/");
        check(r, "/*asdf/", false, true);
    }

    {
        // requires string to contain at least 1 number and 1 uppercase letter
        hermes::Regex r("(?=.*[0-9])(?=.*[A-Z]).*");

        // none of these are partial, because they never make it to
        // the ".*", they fail in one of the lookaheads first
        check(r, "asdf", false);
        check(r, "asdfA", false);
        check(r, "as1df", false);

        check(r, "Aasdf1");
    }
}