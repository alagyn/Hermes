#include <regex_test_utils.h>

void check(const hermes::Regex& r, const char* str, bool fullmatch, bool partial)
{
    INFO("Regex: " << r.toStr());
    INFO("Input: '" << str << "'");
    INFO("Expected: full=" << fullmatch << " partial=" << partial);
    INFO(r.annotate());

    hermes::Match m = r.match(str);

    INFO("\nActual:    full=" << m.match << " partial=" << m.partial);

    CHECK((fullmatch == m.match && partial == m.partial));
}

void singleCheck(const char* re, const char* str, bool fullmatch, bool partial)
{
    hermes::Regex r(re);
    check(r, str, fullmatch, partial);
}