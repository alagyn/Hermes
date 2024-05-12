#include <regex_test_utils.h>

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

    hermes::Regex r3("a*");

    check(r3, "a");
    check(r3, "aa");
    check(r3, "aaa");
    check(r3, "aaaaaaaaaaaaaaaaaaa");
    check(r3, "b", false);
}
