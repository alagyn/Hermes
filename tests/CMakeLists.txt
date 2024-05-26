# Unit tests
add_executable(tests
    cpp_tests/regex_test_utils.cpp
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
    Catch2::Catch2WithMain
    hermes
)

target_include_directories(tests
    PRIVATE
    cpp_tests
)

option(HERMES_PYTHON_TESTS "Enable Python Unit Tests in CTEST" ON)

include(CTest)
include(Catch)
catch_discover_tests(tests)

# python tests
function(pythonTest)
    set(options)
    set(single_args TEST)
    set(multivalue_args)

    cmake_parse_arguments(ARGS "${options}" "${single_args}" "${multivalue_args}" ${ARGN})

    if(NOT EXISTS ${HERMES_ROOT}/tests/py_tests/${ARGS_TEST}.py)
        message(FATAL_ERROR "Could not find python test file: ${ARGS_TEST}.py")
    endif()

    add_test(
        NAME py_${ARGS_TEST}
        WORKING_DIRECTORY ${HERMES_ROOT}
        COMMAND ${Python3_EXECUTABLE} -m unittest discover -t ${HERMES_ROOT} -s tests/py_tests -p ${ARGS_TEST}.py
    )

endfunction()

if(${HERMES_PYTHON_TESTS})
    pythonTest(TEST test_1_buildGrammar)
    pythonTest(TEST test_2_FandF)
    pythonTest(TEST test_3_LR1Closure)
    pythonTest(TEST test_4_parseTable)
endif()

# Calculator test app
add_executable(calculator test_execs/calculator.cpp)

list(APPEND CMAKE_MODULE_PATH ${PROJECT_SOURCE_DIR}/cmake)
include(add_hermes_grammar)

add_hermes_grammar(
    TARGET calc
    GRAMMAR grammars/calculator.hm
)

target_link_libraries(calculator
    PRIVATE calc
)


# regex debugger app
add_executable(regex-debug test_execs/regex-debug.cpp)

target_link_libraries(regex-debug PRIVATE hermes)