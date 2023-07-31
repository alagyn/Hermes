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
set(HERMES_GRAMMAR ${HERMES_GRAMMAR} CACHE FILEPATH "The input grammar file")

set(HERMES_TEST OFF CACHE BOOL "Build tests")
set(HERMES_DEBUG OFF CACHE BOOL "Enable Parser debug statements")

if(NOT EXISTS "${HERMES_GRAMMAR}")
    message(FATAL_ERROR "Grammar file: \"${HERMES_GRAMMAR}\" not found")
endif()

# Hidden generated include files
set(HERMES_HIDDEN_INC ${CMAKE_CURRENT_BINARY_DIR}/hidden)
# Public generated include files
set(HERMES_PUBLIC_INC ${CMAKE_CURRENT_BINARY_DIR}/inc)

set(HERMES_PARSE_TABLE_FILE ${HERMES_HIDDEN_INC}/hermes/_parseTable.h)
set(HERMES_SYMBOL_FILE ${HERMES_PUBLIC_INC}/hermes/symbol.h)

set(HERMES_GEN_ROOT hermes_gen)
set(HERMES_CPP_ROOT hermes_cpp)



set(PY_FILES
    ${HERMES_GEN_ROOT}/consts.py
    ${HERMES_GEN_ROOT}/grammar.py
    ${HERMES_GEN_ROOT}/errors.py
    ${HERMES_GEN_ROOT}/lalr1_automata.py
    ${HERMES_GEN_ROOT}/main.py
)

set(CPP_FILES
    ${HERMES_CPP_ROOT}/src/parser.cpp
    ${HERMES_CPP_ROOT}/src/scanner.cpp
    ${HERMES_CPP_ROOT}/src/parseTableImpl.cpp
)

# Custom command to generate the header
add_custom_command(
    OUTPUT ${HERMES_PARSE_TABLE_FILE}
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    COMMAND
        ${Python3_EXECUTABLE} -m hermes_gen.main --table ${HERMES_PARSE_TABLE_FILE} --symbol ${HERMES_SYMBOL_FILE} ${HERMES_GRAMMAR}
    DEPENDS ${HERMES_GRAMMAR} ${PY_FILES}
)

# Add target to generate parse table
add_custom_target(parse_table
    DEPENDS ${HERMES_PARSE_TABLE_FILE} ${HERMES_GRAMMAR} ${PY_FILES}
)

# Add library
add_library(${PROJECT_NAME} SHARED
    ${CPP_FILES}
)

# Add dependency on parse_table
add_dependencies(${PROJECT_NAME} parse_table)

target_include_directories(${PROJECT_NAME}
    PUBLIC
        hermes_cpp/inc
        ${HERMES_PUBLIC_INC}
    PRIVATE
        ${HERMES_HIDDEN_INC}
        ${HERMES_ADDITIONAL_INCLUDES}
)

target_link_libraries(${PROJECT_NAME}
    PRIVATE
        Boost::regex
)

if(${HERMES_DEBUG})
target_compile_definitions(${PROJECT_NAME}
    PRIVATE
        HERMES_PARSE_DEBUG
)
endif()

if(${HERMES_TEST})
    add_subdirectory(tests)
endif()
