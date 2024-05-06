#include <catch2/catch_test_macros.hpp>

#include <hermes/regex/regex.h>

#include <iostream>
#include <vector>

TEST_CASE("Regex +", "[regex]")
{
    {
        hermes::Regex r("ab+");

        INFO(r.toStr());

        CHECK(r.match("ab"));
        CHECK_FALSE(r.match("b"));
        CHECK(r.match("abb"));
        CHECK_FALSE(r.match("aab"));
    }

    {
        hermes::Regex r("a(ab)+");
        INFO(r.toStr());

        CHECK(r.match("aab"));
        CHECK(r.match("aabab"));
        CHECK(r.match("aababab"));
        CHECK_FALSE(r.match("aa"));
        CHECK_FALSE(r.match("aaba"));
        CHECK_FALSE(r.match("aabb"));
    }
}

TEST_CASE("Regex *", "[regex]")
{
    hermes::Regex r1("a[ba]*");

    CHECK_FALSE(r1.match(""));
    CHECK(r1.match("a"));
    CHECK(r1.match("aa"));
    CHECK(r1.match("ab"));
    CHECK(r1.match("abba"));
    CHECK(r1.match("aaaab"));
    CHECK(r1.match("ababab"));
    CHECK_FALSE(r1.match("abc"));
    CHECK_FALSE(r1.match("ac"));
    CHECK_FALSE(r1.match("aaaaaac"));
    CHECK_FALSE(r1.match("aabaacbab"));
    CHECK_FALSE(r1.match("acaaba"));

    hermes::Regex r2("a(ba)*");

    CHECK_FALSE(r2.match(""));
    CHECK_FALSE(r2.match("aab"));
    CHECK(r2.match("a"));
    CHECK(r2.match("aba"));
    CHECK(r2.match("ababa"));
    CHECK_FALSE(r2.match("abaa"));
    CHECK_FALSE(r2.match("ababb"));
}

TEST_CASE("Regex ?", "[regex]")
{
    {
        hermes::Regex r("ab?");
        INFO(r.toStr());
        CHECK(r.match("a"));
        CHECK(r.match("ab"));
        CHECK_FALSE(r.match("abb"));
        CHECK_FALSE(r.match("ac"));
    }

    {
        hermes::Regex r("a(ab)?");
        INFO(r.toStr());
        CHECK(r.match("a"));
        CHECK(r.match("aab"));
        CHECK_FALSE(r.match("ab"));
        CHECK_FALSE(r.match("aa"));
        CHECK_FALSE(r.match("aaba"));
        CHECK_FALSE(r.match("aac"));
    }
}

TEST_CASE("Regex CC Number", "[regex]")
{
    hermes::Regex r1("\\d{3, 4}[- ]?[0-9]{4}[ -]?[0-56-9]{ 4 ,4}[ -]?\\d{4,4}");

    std::string x = r1.toStr();
    const char* xx = x.c_str();

    INFO("Regex->toStr(): " << xx);

    REQUIRE(r1.match("0000111122223333"));
    REQUIRE(r1.match("0000 1111 2222 3333"));
    REQUIRE(r1.match("0000-1111-2222-3333"));
    REQUIRE(r1.match("000-1111-2222-3333"));
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
        CHECK(r.match("["));
        CHECK(r.match("]"));
    }

    {
        hermes::Regex r("\\[]");
        CHECK(r.match("[]"));
    }

    {
        hermes::Regex r("[asdf]+");
        CHECK(r.match("asdf"));
        CHECK(r.match("aaaa"));
        CHECK(r.match("afff"));
        CHECK(r.match("afda"));
        CHECK_FALSE(r.match("b"));
        CHECK_FALSE(r.match("basdf"));
        CHECK_FALSE(r.match("asdfb"));
        CHECK_FALSE(r.match("asdb"));
    }

    {
        hermes::Regex r("[-]");
        CHECK(r.match("-"));
    }

    {
        hermes::Regex r("[0-]");
        CHECK(r.match("0"));
        CHECK(r.match("-"));
    }

    {
        hermes::Regex r("[0-a]");
        CHECK(r.match("0"));
        CHECK(r.match("-"));
        CHECK(r.match("a"));
    }

    {
        hermes::Regex r("[0-9]");
        CHECK(r.match("0"));
        CHECK(r.match("1"));
        CHECK(r.match("2"));
        CHECK(r.match("8"));
        CHECK(r.match("9"));
    }
}

TEST_CASE("Partial Matches", "[regex]")
{
    hermes::Regex r("ab{4}");

    bool partial = false;

    CHECK(r.match("abbbb", partial));
    CHECK(partial);

    CHECK_FALSE(r.match("abbb", partial));
    CHECK(partial);

    CHECK_FALSE(r.match("abb", partial));
    CHECK(partial);

    CHECK_FALSE(r.match("ab", partial));
    CHECK(partial);

    CHECK_FALSE(r.match("a", partial));
    CHECK(partial);

    CHECK_FALSE(r.match("b", partial));
    CHECK_FALSE(partial);
}

TEST_CASE("Lookahead", "[regex]")
{
    {
        hermes::Regex r("ab((?!ba)[abcd])*");

        INFO(r.toStr());

        CHECK(r.match("ab"));
        CHECK(r.match("abcd"));
        CHECK_FALSE(r.match("abcba"));
        CHECK_FALSE(r.match("abcdba"));
        CHECK_FALSE(r.match("abbacc"));
    }

    {
        hermes::Regex r("/\\*((?!\\*/)(.|\n))*?\\*/");

        INFO(r.toStr());

        CHECK(r.match("/* asdf */"));
        CHECK(r.match("/*a*s\nd/f*/"));
        CHECK_FALSE(r.match("/*asdf/"));
    }
}