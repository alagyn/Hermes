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

TEST_CASE("Regex + #1", "[regex]")
{
    hermes::Regex r("ab+");

    check(r, "ab");
    check(r, "b", false, false);
    check(r, "abb");
    check(r, "aab", false, false);

    CHECK_THROWS(r.match(""));
}

TEST_CASE("Regex + #2", "[regex]")
{
    hermes::Regex r("a(ab)+");

    check(r, "aab");
    check(r, "aabab");
    check(r, "aababab");
    check(r, "aa", false, true);
    check(r, "aaba", false, true);
    check(r, "aabb", false, false);
}

TEST_CASE("Regex + #3")
{
    hermes::Regex r("[0-9]+");
    check(r, "2");
    check(r, "2 ", false, false);
}

TEST_CASE("Regex *", "[regex]")
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

TEST_CASE("Regex ?", "[regex]")
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
}

TEST_CASE("Repetition", "[regex]")
{
    {
        hermes::Regex r("ab{0,2}bb");

        check(r, "ab", false, true);
        check(r, "abb");
        check(r, "abbb");
        check(r, "abbbb");
        check(r, "abbbbb", false);
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