#include <regex_test_utils.h>

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
