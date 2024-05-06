

add_executable(calculator test_execs/calculator.cpp)
target_link_libraries(calculator hermes)

add_executable(tests
    cpp_tests/test_main.cpp
    cpp_tests/test_regex.cpp
)
target_link_libraries(tests
    PRIVATE
    Catch2::Catch2
    hermes_regex
)
