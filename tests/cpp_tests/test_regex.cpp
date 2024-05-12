#include <catch2/catch_test_macros.hpp>

#include <hermes/internal/regex/regex.h>

#include <iostream>
#include <vector>

void check(
    const hermes::Regex& r,
    const char* str,
    bool fullmatch = true,
    bool partial = false
)
{
    INFO("Regex: " << r.toStr());
    INFO("Input: '" << str << "'");
    INFO("Expected: full=" << fullmatch << " partial=" << partial);

    hermes::Match m = r.match(str);

    INFO(
        "Actual:    full=" << m.match << " partial=" << m.partial
                           << " pos=" << m.pos.top()
    );

    INFO(r.annotate());

    CHECK((fullmatch == m.match && partial == m.partial));
}

void singleCheck(
    const char* re,
    const char* str,
    bool fullmatch = true,
    bool partial = false
)
{
    hermes::Regex r(re);
    check(r, str, fullmatch, partial);
}

TEST_CASE("Repetition +", "[regex]")
{
    {
        hermes::Regex r("ab+");

        check(r, "ab");
        check(r, "b", false, false);
        check(r, "abb");
        check(r, "aab", false, false);

        CHECK_THROWS(r.match(""));
    }

    {
        hermes::Regex r("a(ab)+");

        check(r, "aab");
        check(r, "aabab");
        check(r, "aababab");
        check(r, "aa", false, true);
        check(r, "aaba", false, true);
        check(r, "aabb", false, false);
    }
    {
        hermes::Regex r("[0-9]+");
        check(r, "2");
        check(r, "2 ", false, false);
    }
}

TEST_CASE("Repetition *", "[regex]")
{
    hermes::Regex r1("a[ba]*");

    check(r1, "a");
    check(r1, "aa");
    check(r1, "ab");
    check(r1, "abba");
    check(r1, "aaaab");
    check(r1, "ababab");
    check(r1, "abc", false, false);
    check(r1, "ac", false, false);
    check(r1, "aaaaaac", false, false);
    check(r1, "aabaacbab", false, false);
    check(r1, "acaaba", false, false);

    hermes::Regex r2("a(ba)*");

    check(r2, "aab", false);
    check(r2, "a");
    check(r2, "aba");
    check(r2, "ababa");
    check(r2, "abaa", false);
    check(r2, "ababb", false);
}

TEST_CASE("Repetition ?", "[regex]")
{
    {
        hermes::Regex r("ab?");
        check(r, "a");
        check(r, "ab");
        check(r, "abb", false);
        check(r, "ac", false);
    }

    {
        hermes::Regex r("a(ab)?");
        check(r, "a");
        check(r, "aab");
        check(r, "ab", false);
        check(r, "aa", false, true);
        check(r, "aaba", false);
        check(r, "aac", false);
    }
}

TEST_CASE("Regex CC Number", "[regex]")
{
    hermes::Regex r1("\\d{3, 4}[- ]?[0-9]{4}[ -]?[0-56-9]{ 4 ,4}[ -]?\\d{4,4}");

    std::string x = r1.toStr();
    const char* xx = x.c_str();

    INFO("Regex->toStr(): " << xx);

    check(r1, "0000111122223333");
    check(r1, "0000 1111 2222 3333");
    check(r1, "0000-1111-2222-3333");
    check(r1, "000-1111-2222-3333");
}

void tryConstr(const char* str)
{
    try
    {
        hermes::Regex r(str);
        INFO(r.toStr());
        FAIL("Did not error with input \"" << str << "\"");
    }
    catch(const std::exception& err)
    {
        SUCCEED("Error thrown " << err.what());
    }
}

TEST_CASE("Bad Regex", "[regex]")
{
    // Empty str is invalid
    tryConstr("");
    // unclosed group
    tryConstr("(");
    // empty group
    tryConstr("()");
    // unclosed class
    tryConstr("[");
    tryConstr("[a");
    tryConstr("a[a");
    // empty class
    tryConstr("a[]");
    tryConstr("a[^]");
    // various bad bracket reps
    tryConstr("a{");
    tryConstr("a{a}");
    tryConstr("a{2");
    tryConstr("a{,");
    tryConstr("a{,a");
    tryConstr("a{,2");
    tryConstr("a{,}");
    tryConstr("a{,2}");
    tryConstr("a{}");

    // Repetitions are not allowed at the start of the string
    tryConstr("+a");
    tryConstr("*a");
    tryConstr("?a");
    tryConstr("{2}a");
    tryConstr("{2,3}a");

    // bad alternations
    tryConstr("|a");
    tryConstr("a|");
    tryConstr("(|)");
}

TEST_CASE("Char Class", "[regex]")
{
    {
        hermes::Regex r("[[\\]]");
        check(r, "[");
        check(r, "]");
    }

    {
        hermes::Regex r("\\[]");
        check(r, "[]");
    }

    {
        hermes::Regex r("[asdf]+");
        check(r, "asdf");
        check(r, "aaaa");
        check(r, "afff");
        check(r, "afda");
        check(r, "b", false, false);
        check(r, "basdf", false, false);
        check(r, "asdfb", false, false);
        check(r, "asdb", false, false);
    }

    {
        hermes::Regex r("[-]");
        check(r, "-");
    }

    {
        hermes::Regex r("[0-]");
        check(r, "0");
        check(r, "-");
    }

    {
        hermes::Regex r("[0-a]");
        check(r, "0");
        check(r, "-");
        check(r, "a");
    }

    {
        hermes::Regex r("[0-9]");
        check(r, "0");
        check(r, "1");
        check(r, "2");
        check(r, "8");
        check(r, "9");
    }

    {
        hermes::Regex r("[abc]");

        check(r, "a");
        check(r, "b");
        check(r, "c");
        check(r, "d", false);
    }

    {
        hermes::Regex r("[^bcd]");

        check(r, "a");
        check(r, "b", false);
        check(r, "d", false);
        check(r, "e");
    }

    singleCheck("a[b]c", "abc");
    singleCheck("a[b]c", "abc");
    singleCheck("a[ab]c", "abc");
    singleCheck("a[a^b]*c", "aba^c");
    singleCheck("a[^ab]c", "adc");
    singleCheck("a[[b]c", "a[c");
    singleCheck("a[-b]c", "a-c");
    singleCheck("a[^-b]c", "adc");
    singleCheck("a[b-]c", "a-c");
    singleCheck("a[a-z-]c", "a-c");
    singleCheck("a[a-z-]+c", "aaz-c");
    singleCheck("a[a-z-]+c", "aaz-cccc");

    //partial because d is consumed by the class
    singleCheck("a[a-z-]+c", "aaz-cd", false, true);

    singleCheck("a[a-z-]+c", "aaz-c1", false);

    singleCheck("//[^\\n]*\\n?", "// asdf this is line ");
    singleCheck("//[^\\n]*\\n?", "// asdf this is line\n");
}

TEST_CASE("Repetition {}", "[regex]")
{
    {
        hermes::Regex r("ab{0,2}bb");

        check(r, "ab", false, true);
        check(r, "abb");
        check(r, "abbb");
        check(r, "abbbb");
        check(r, "abbbbb", false);
    }

    {
        hermes::Regex r("ab{4}c");

        check(r, "ab", false, true);
        check(r, "abbbb", false, true);
        check(r, "abbbbc");
        check(r, "abbbc", false);
    }

    {
        hermes::Regex r("ab{3,}c");
        check(r, "abc", false);
        check(r, "abbb", false, true);
        check(r, "abbc", false);
        check(r, "abbbc");
        check(r, "abbbbbbbbbbbbbbbc");
    }

    {
        hermes::Regex r("ab{2,}b{5,}c");
        check(r, "abc", false);
        /*
            this tests to make sure the backtracking doesn't
            go below the minimum reps
        */
        check(r, "abbbbbbc", false);
    }

    {
        hermes::Regex r("ab{2,4}c");
        check(r, "abc", false);
        check(r, "abbc");
        check(r, "abbbc");
        check(r, "abbbbc");
        check(r, "abbbbbc", false);
    }
}

TEST_CASE("Partial Matches", "[regex]")
{
    {
        hermes::Regex r("ab{4}");

        bool partial = false;

        check(r, "abbbbb", false, false);
        check(r, "abbbb");
        check(r, "abbb", false, true);
        check(r, "abb", false, true);
        check(r, "ab", false, true);
        check(r, "a", false, true);
        check(r, "b", false, false);
    }
}

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
        hermes::Regex r("/\\*((?!\\*/)(.|\n))*?\\*/");

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

TEST_CASE("Escapes", "[regex]")
{
    singleCheck("a\\|", "a|");
    singleCheck("a\\(", "a(");
    singleCheck("a\\[", "a[");
    singleCheck("a\\{", "a{");
    singleCheck("a\\n", "a\n");
    singleCheck("a\\d", "a3");
    singleCheck("a\\d", "a1");
    singleCheck("a\\d", "a9");
    singleCheck("a\\d", "a0");
    singleCheck("a\\l", "aa");
    singleCheck("a\\l", "az");
    singleCheck("a\\l", "ag");
    singleCheck("a\\l", "aA", false);
    singleCheck("a\\u", "aA");
    singleCheck("a\\s", "a ");
}

TEST_CASE("Alternation", "[regex]")
{
    singleCheck("a|b", "a");
    singleCheck("a|b", "b");
    singleCheck("a|b|c", "c");
    singleCheck("a|(b)|.", "b");
    singleCheck("(a)|b|.", "a");
    singleCheck("a(b|c)", "ab");
    singleCheck("a(b|c)", "ac");
    singleCheck("a(b|c)", "ad", false);
    singleCheck("(a|b|c)", "c");
    singleCheck("(a|b|c)", "a");
    singleCheck("(a|b|c)", "b");
    singleCheck("(a|(b)|.)", "b");
}

TEST_CASE("Tricky Stuff", "[regex]")
{
    singleCheck("a(((b)))c", "abc");
    singleCheck("a(b|(c))d", "abd");
    singleCheck("a(b|(c))d", "acd");
    singleCheck("a(b*|c)d", "abbd");
    singleCheck("a(b*|c)d", "ad");
    singleCheck("a(b*|c)d", "acd");
    singleCheck("a[ab]{20}", "aaaaabaaaabaaaabaaaab");
    singleCheck(
        "a[ab][ab][ab][ab][ab][ab][ab][ab][ab][ab][ab][ab][ab][ab][ab][ab][ab]["
        "ab][ab][ab]",
        "aaaaabaaaabaaaabaaaab"
    );
    singleCheck(
        "a[ab][ab][ab][ab][ab][ab][ab][ab][ab][ab][ab][ab][ab][ab][ab][ab][ab]["
        "ab][ab][ab](wee|week)(knights|night)",
        "aaaaabaaaabaaaabaaaabweeknights"
    );
    singleCheck(
        "123456789012345678901234567890123456789012345678901234567890123456789"
        "0",
        "a123456789012345678901234567890123456789012345678901234567890123456789"
        "0b",
        false
    );

    singleCheck("a(b?c)+d", "accd");
    singleCheck("(wee|week)(knights|night)", "weeknights");
    singleCheck(".*", "abc");

    {
        hermes::Regex r("a(b|(c))d");

        check(r, "abd");
        check(r, "acd");
    }

    {
        hermes::Regex r("a(b*|c|e)d");

        check(r, "abbd");
        check(r, "acd");
        check(r, "ad");
    }

    {
        hermes::Regex r("a(b?)c");

        check(r, "abc");
        check(r, "ac");
    }

    {
        hermes::Regex r("a(b+)c");

        check(r, "abc");
        check(r, "abbbc");
    }

    singleCheck("a(b*)c", "ac");
    singleCheck("(a|ab)(bc([de]+)f|cde)", "abcdef");

    {
        hermes::Regex r("a([bc]?)c");

        check(r, "abc");
        check(r, "ac");
    }

    {
        hermes::Regex r("a([bc]+)c");

        check(r, "abc");
        check(r, "abcc");
        check(r, "abcbc");
    };

    {
        hermes::Regex r("a(bbb+|bb+|b)b");

        check(r, "abb");
        check(r, "abbb");
    }

    singleCheck("a(bbb+|bb+|b)bb", "abbb");
    singleCheck("a(bb+|b)b", "abb");
    singleCheck("(.*).*", "abcdef");
    singleCheck("(a*)*", "bc", false);
}