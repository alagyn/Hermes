#include <regex_test_utils.h>

TEST_CASE("Alternation", "[regex]")
{
    {
        hermes::Regex r("a|b");

        check(r, "a");
        check(r, "b");
        check(r, "c", false);
    }

    singleCheck("a|b|c", "c");
    singleCheck("a|(b)|.", "b");
    singleCheck("(a)|b|.", "a");

    {
        hermes::Regex r("a(b|c)");

        check(r, "ab");
        check(r, "ac");
        check(r, "ad", false);
    }

    {
        hermes::Regex r("(a|b|c)");

        check(r, "c");
        check(r, "a");
        check(r, "b");
    }

    singleCheck("(a|(b)|.)", "b");
}
