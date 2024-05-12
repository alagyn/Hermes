#include <regex_test_utils.h>

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
