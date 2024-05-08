# Unit tests
add_executable(tests
    cpp_tests/test_main.cpp
    cpp_tests/test_regex.cpp
)
target_link_libraries(tests
    PRIVATE
    Catch2::Catch2
    hermes_regex
)

add_executable(calculator test_execs/calculator.cpp)

add_hermes_grammer(
    TARGET calc
    GRAMMAR grammars/calculator.hm
)

target_link_libraries(calculator
    PRIVATE calc
)
