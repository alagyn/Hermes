#include <regex_test_utils.h>

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
