cmake_minimum_required(VERSION 3.26)

project(hermes)

find_package(Python3 
    REQUIRED 
        COMPONENTS Interpreter
)

find_package(Boost 1.82.0 
    REQUIRED
        COMPONENTS regex
)

# This will let users specify their grammar and then add_subdiretory to this
set(GRAMMAR ${GRAMMAR} CACHE FILEPATH "The input grammar file")

set(HERMES_TEST OFF CACHE BOOL "Build tests")

if(NOT EXISTS "${GRAMMAR}")
    message(FATAL_ERROR "Grammar file: \"${GRAMMAR}\" not found")
endif()

set(PARSE_TABLE_FILE ${CMAKE_CURRENT_BINARY_DIR}/src/parseTable.cpp)
set(TOKEN_FILE ${CMAKE_CURRENT_BINARY_DIR}/inc/token.h)

set(HERMES_GEN_ROOT hermes_gen)
set(HERMES_CPP_ROOT hermes_cpp)

set(PY_FILES
    ${HERMES_GEN_ROOT}/consts.py
    ${HERMES_GEN_ROOT}/ebnf_grammer.py
    ${HERMES_GEN_ROOT}/errors.py
    ${HERMES_GEN_ROOT}/first_and_follow.py
    ${HERMES_GEN_ROOT}/lalr1_automata.py
    ${HERMES_GEN_ROOT}/main.py
    ${HERMES_GEN_ROOT}/preprocessing.py
)

set(CPP_FILES
    ${HERMES_CPP_ROOT}/src/parser.cpp
    ${HERMES_CPP_ROOT}/src/scanner.cpp
    ${PARSE_TABLE_FILE}
)

# Custom command to generate the header
add_custom_command(
    OUTPUT ${PARSE_TABLE_FILE}
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    COMMAND
        ${Python3_EXECUTABLE} -m hermes_gen.main --code ${PARSE_TABLE_FILE} --token ${TOKEN_FILE} ${GRAMMAR}
    DEPENDS ${GRAMMAR} ${PY_FILES}
)

# Add target to generate parse table
add_custom_target(parse_table
    DEPENDS ${PARSE_TABLE_FILE} ${GRAMMAR} ${PY_FILES}
)

# Add library
add_library(${CMAKE_PROJECT_NAME} SHARED
    ${CPP_FILES}
)

# Add dependency on parse_table
add_dependencies(${CMAKE_PROJECT_NAME} parse_table)

target_include_directories(${CMAKE_PROJECT_NAME}
    PUBLIC
        hermes_cpp/inc
)

target_link_libraries(${CMAKE_PROJECT_NAME}
    PRIVATE
        Boost::regex
)

if(${HERMES_TEST})
    add_subdirectory(tets)
endif()
