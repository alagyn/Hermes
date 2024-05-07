cmake_minimum_required(VERSION 3.26)

project(hermes)

find_package(Python3 
    REQUIRED 
        COMPONENTS Interpreter
)

set(HERMES_ROOT ${CMAKE_CURRENT_SOURCE_DIR})
set(HERMES_GEN_ROOT ${HERMES_ROOT}/hermes_gen)
set(HERMES_CPP_ROOT ${HERMES_ROOT}/hermes_cpp)

## Regex Lib
add_library(hermes_regex SHARED
    ${HERMES_CPP_ROOT}/src/regex/node.cpp
    ${HERMES_CPP_ROOT}/src/regex/regex.cpp
    ${HERMES_CPP_ROOT}/src/regex/rparser.cpp
)

target_include_directories(hermes_regex
    PUBLIC
        hermes_cpp/inc
)


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


function(add_hermes_grammer)
    set(options DEBUG)
    set(single_args TARGET GRAMMAR DESC_FILE)
    set(multivalue_args)

    cmake_parse_arguments(ARGS "${options}" "${single_args}" "${multivalue_args}" ${ARGN})

    if(NOT ${ARGS_GRAMMAR} STREQUAL "")
        # Make the desc file relative to the source root
        if(NOT IS_ABSOLUTE ${ARGS_GRAMMAR})
            cmake_path(ABSOLUTE_PATH ARGS_GRAMMAR
                BASE_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
                NORMALIZE
                OUTPUT_VARIABLE GRAMMAR 
            )
        else()
            set(GRAMMAR ${ARGS_GRAMMAR})
        endif()
    endif()

    if(NOT EXISTS "${GRAMMAR}")
        message(FATAL_ERROR "Grammar file: \"${GRAMMAR}\" not found")
    endif()

    if(NOT ${ARGS_DESC_FILE} STREQUAL "")
        # Make the desc file relative to the source root
        if(NOT IS_ABSOLUTE ${ARGS_DESC_FILE})
            cmake_path(ABSOLUTE_PATH ARGS_DESC_FILE
                BASE_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
                NORMALIZE
                OUTPUT_VARIABLE DESC_FILE 
            )
        else()
            set(DESC_FILE ${ARGS_DESC_FILE})
        endif()
    endif()

    # Hidden generated include files
    set(HIDDEN_INC ${CMAKE_CURRENT_BINARY_DIR}/hidden)
    # Public generated include files
    set(PUBLIC_INC ${CMAKE_CURRENT_BINARY_DIR}/inc)

    set(PARSE_TABLE_FILE ${HIDDEN_INC}/hermes/${ARGS_TARGET}_parseTable.h)
    set(SYMBOL_FILE ${PUBLIC_INC}/hermes/${ARGS_TARGET}_symbol.h)

    # Custom command to generate the header
    add_custom_command(
        OUTPUT ${PARSE_TABLE_FILE}
        WORKING_DIRECTORY ${HERMES_ROOT}
        COMMAND
            ${Python3_EXECUTABLE} -m hermes_gen.main
                --table ${PARSE_TABLE_FILE}
                --symbol ${SYMBOL_FILE}
                --automata "${DESC_FILE}"
                ${GRAMMAR}
        VERBATIM
        DEPENDS ${GRAMMAR} ${PY_FILES}
    )

    # Add target to generate parse table
    add_custom_target(${ARGS_TARGET}_parse_table
        DEPENDS ${PARSE_TABLE_FILE} ${GRAMMAR} ${PY_FILES}
    )

    # Add library
    add_library(${ARGS_TARGET} SHARED
        ${CPP_FILES}
    )

    # Add dependency on parse_table
    add_dependencies(${ARGS_TARGET} ${ARGS_TARGET}_parse_table)

    target_include_directories(${ARGS_TARGET}
        PUBLIC
            ${HERMES_ROOT}/hermes_cpp/inc
            ${PUBLIC_INC}
        PRIVATE
            ${HIDDEN_INC}
    )
    
    target_link_libraries(${ARGS_TARGET}
        PRIVATE
    )
    
    if(${ARGS_DEBUG})
        target_compile_definitions(${ARGS_TARGET}
            PRIVATE
                HERMES_PARSE_DEBUG
        )
        message("Added Hermes target ${ARGS_TARGET} for grammar ${ARGS_GRAMMAR} in ${CMAKE_CURRENT_SOURCE_DIR}")
    endif()

endfunction()

option(HERMES_TESTS "Enable Hermes Test builds" OFF)

if(${HERMES_TESTS})
    add_subdirectory(third-party)
    add_subdirectory(tests)
endif()