# Unit tests
add_executable(tests
    cpp_tests/regex_test_utils.cpp
    cpp_tests/test_main.cpp
    cpp_tests/test_re_alternation.cpp
    cpp_tests/test_re_bad_re.cpp
    cpp_tests/test_re_char_class.cpp
    cpp_tests/test_re_escapes.cpp
    cpp_tests/test_re_lookahead.cpp
    cpp_tests/test_re_rep_bracket.cpp
    cpp_tests/test_re_rep_plus.cpp
    cpp_tests/test_re_rep_question.cpp
    cpp_tests/test_re_rep_star.cpp
    cpp_tests/test_re_tricky.cpp
    cpp_tests/test_regex.cpp
)
target_link_libraries(tests
    PRIVATE
    Catch2::Catch2
    hermes
)

target_include_directories(tests
    PRIVATE
    cpp_tests
)

add_executable(calculator test_execs/calculator.cpp)

add_hermes_grammer(
    TARGET calc
    GRAMMAR grammars/calculator.hm
)

target_link_libraries(calculator
    PRIVATE calc
)

add_executable(regex-debug test_execs/regex-debug.cpp)

target_link_libraries(regex-debug PRIVATE hermes)