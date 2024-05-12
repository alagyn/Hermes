#include <regex_test_utils.h>

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
