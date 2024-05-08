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
    ${HERMES_CPP_ROOT}/src/scanner.cpp
    ${HERMES_CPP_ROOT}/src/parseTable.cpp
    ${HERMES_CPP_ROOT}/src/regex/node.cpp
    ${HERMES_CPP_ROOT}/src/regex/regex.cpp
    ${HERMES_CPP_ROOT}/src/regex/rparser.cpp
)

target_include_directories(hermes
    PUBLIC
        hermes_cpp/inc
)

option(HERMES_TESTS "Enable Hermes Test builds" OFF)


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

    # Private generated include files
    set(PRIVATE_INC ${CMAKE_CURRENT_BINARY_DIR}/hidden)
    # Public generated include files
    set(PUBLIC_INC ${CMAKE_CURRENT_BINARY_DIR}/inc)


    set(PARSE_TABLE_FILE ${PRIVATE_INC}/hermes/${ARGS_TARGET}_parseTable.h)
    set(LOADER_HEADER_FILE ${PUBLIC_INC}/hermes/${ARGS_TARGET}_parser.h)
    set(LOADER_IMPL_FILE ${PRIVATE_INC}/hermes/${ARGS_TARGET}_parser.cpp)

    set(OUTPUTS ${PARSE_TABLE_FILE} ${LOADER_HEADER_FILE} ${LOADER_IMPL_FILE})

    # Custom command to generate the header
    add_custom_command(
        OUTPUT ${OUTPUTS}
        WORKING_DIRECTORY ${HERMES_ROOT}
        COMMAND
            ${Python3_EXECUTABLE} -m hermes_gen.main
                --name ${ARGS_TARGET}
                --table ${PARSE_TABLE_FILE}
                --loader ${LOADER_HEADER_FILE}
                --impl ${LOADER_IMPL_FILE}
                --automata "${DESC_FILE}"
                ${GRAMMAR}
        VERBATIM
        DEPENDS ${GRAMMAR} ${PY_FILES}
    )

    # Add target to generate parse table
    add_custom_target(${ARGS_TARGET}_parse_table
        DEPENDS ${OUTPUTS} ${GRAMMAR} ${PY_FILES}
    )

    # Add library
    add_library(${ARGS_TARGET}
        ${LOADER_IMPL_FILE}
    )

    # Add dependency on parse_table
    add_dependencies(${ARGS_TARGET} ${ARGS_TARGET}_parse_table)

    target_include_directories(${ARGS_TARGET}
        PUBLIC
            ${HERMES_ROOT}/hermes_cpp/inc
            ${PUBLIC_INC}
        PRIVATE
            ${PRIVATE_INC}
    )
    
    target_link_libraries(${ARGS_TARGET}
        PRIVATE
            hermes
    )
    
    if(${ARGS_DEBUG})
        target_compile_definitions(${ARGS_TARGET}
            PRIVATE
                HERMES_PARSE_DEBUG
        )
        message("Added Hermes target ${ARGS_TARGET} for grammar ${ARGS_GRAMMAR} in ${CMAKE_CURRENT_SOURCE_DIR}")
    endif()

endfunction()

if(${HERMES_TESTS})
    add_subdirectory(third-party)
    add_subdirectory(tests)
endif()