#include <regex_test_utils.h>

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

    // bad alternations
    tryConstr("|a");
    tryConstr("a|");
    tryConstr("(|)");
}