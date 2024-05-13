cmake_minimum_required(VERSION 3.26)

project(hermes)

find_package(Python3 
    REQUIRED 
        COMPONENTS Interpreter
)

set(HERMES_ROOT ${CMAKE_CURRENT_SOURCE_DIR})
set(HERMES_GEN_ROOT ${HERMES_ROOT}/hermes_gen)
set(HERMES_CPP_ROOT ${HERMES_ROOT}/hermes_cpp)

set(PY_FILES
    ${HERMES_GEN_ROOT}/consts.py
    ${HERMES_GEN_ROOT}/grammar.py
    ${HERMES_GEN_ROOT}/errors.py
    ${HERMES_GEN_ROOT}/lalr1_automata.py
    ${HERMES_GEN_ROOT}/main.py
    ${HERMES_GEN_ROOT}/writers/hermesHeader.py
    ${HERMES_GEN_ROOT}/writers/loader.py
    ${HERMES_GEN_ROOT}/writers/parseTable.py
)

add_library(hermes
    ${HERMES_CPP_ROOT}/src/regex/node_strs.cpp
    ${HERMES_CPP_ROOT}/src/regex/node.cpp
    ${HERMES_CPP_ROOT}/src/regex/regex.cpp
    ${HERMES_CPP_ROOT}/src/regex/rparser.cpp
    ${HERMES_CPP_ROOT}/src/grammar.cpp
    ${HERMES_CPP_ROOT}/src/scanner.cpp
)

target_include_directories(hermes
    PUBLIC
        hermes_cpp/inc
)

option(HERMES_TESTS "Enable Hermes Test builds" OFF)

list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake")

if(${HERMES_TESTS})
    add_subdirectory(third-party)
    add_subdirectory(tests)
endif()