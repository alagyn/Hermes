
#include <regex_test_utils.h>

TEST_CASE("Escapes", "[regex]")
{
    singleCheck("a\\|", "a|");
    singleCheck("a\\(", "a(");
    singleCheck("a\\[", "a[");
    singleCheck("a\\{", "a{");
    singleCheck("a\\n", "a\n");
    singleCheck("a\\d", "a3");
    singleCheck("a\\d", "a1");
    singleCheck("a\\d", "a9");
    singleCheck("a\\d", "a0");
    singleCheck("a\\l", "aa");
    singleCheck("a\\l", "az");
    singleCheck("a\\l", "ag");
    singleCheck("a\\l", "aA", false);
    singleCheck("a\\u", "aA");
    singleCheck("a\\s", "a ");
}