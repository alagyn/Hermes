#include <regex_test_utils.h>

TEST_CASE("Char Class", "[regex]")
{
    {
        hermes::Regex r("[[\\]]");
        check(r, "[");
        check(r, "]");
    }

    {
        hermes::Regex r("\\[]");
        check(r, "[]");
    }

    {
        hermes::Regex r("[asdf]+");
        check(r, "asdf");
        check(r, "aaaa");
        check(r, "afff");
        check(r, "afda");
        check(r, "b", false, false);
        check(r, "basdf", false, false);
        check(r, "asdfb", false, false);
        check(r, "asdb", false, false);
    }

    {
        hermes::Regex r("[-]");
        check(r, "-");
    }

    {
        hermes::Regex r("[0-]");
        check(r, "0");
        check(r, "-");
    }

    {
        hermes::Regex r("[0-a]");
        check(r, "0");
        check(r, "-");
        check(r, "a");
    }

    {
        hermes::Regex r("[0-9]");
        check(r, "0");
        check(r, "1");
        check(r, "2");
        check(r, "8");
        check(r, "9");
    }

    {
        hermes::Regex r("[abc]");

        check(r, "a");
        check(r, "b");
        check(r, "c");
        check(r, "d", false);
    }

    {
        hermes::Regex r("[^bcd]");

        check(r, "a");
        check(r, "b", false);
        check(r, "d", false);
        check(r, "e");
    }

    singleCheck("a[b]c", "abc");
    singleCheck("a[b]c", "abc");
    singleCheck("a[ab]c", "abc");
    singleCheck("a[a^b]*c", "aba^c");
    singleCheck("a[^ab]c", "adc");
    singleCheck("a[[b]c", "a[c");
    singleCheck("a[-b]c", "a-c");
    singleCheck("a[^-b]c", "adc");
    singleCheck("a[b-]c", "a-c");
    singleCheck("a[a-z-]c", "a-c");
    singleCheck("a[a-z-]+c", "aaz-c");
    singleCheck("a[a-z-]+c", "aaz-cccc");

    //partial because d is consumed by the class
    singleCheck("a[a-z-]+c", "aaz-cd", false, true);

    singleCheck("a[a-z-]+c", "aaz-c1", false);

    singleCheck("//[^\\n]*\\n?", "// asdf this is line ");
    singleCheck("//[^\\n]*\\n?", "// asdf this is line\n");
}
