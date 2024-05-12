#include <regex_test_utils.h>

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