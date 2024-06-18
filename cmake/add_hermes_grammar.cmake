
function(add_hermes_grammar)
    set(options DEBUG STRICT LOCAL_LINK)
    set(single_args TARGET GRAMMAR DESC_FILE GRAMMAR_DIR)
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

    if(DEFINED ARGS_GRAMMAR_DIR)
        if(NOT IS_ABSOLUTE ${ARGS_GRAMMAR_DIR})
            cmake_path(ABSOLUTE_PATH ARGS_GRAMMAR_DIR
                BASE_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
                NORMALIZE
                OUTPUT_VARIABLE GRAMMAR_DIR
            )
        else()
            set(GRAMMAR_DIR ${ARGS_GRAMMAR})
        endif()

        file(GLOB_RECURSE GRAMMAR_FILES ${GRAMMAR_DIR}/*.hm)
    endif()

    set(STRICT_MODE "")

    if(${ARGS_STRICT})
        set(STRICT_MODE "--strict")
    endif()

    set(HERMES_TARGET "hermes::hermes")
    if(${ARGS_LOCAL_LINK})
        set(HERMES_TARGET "hermes")
    endif()


    # Private generated include files
    set(PRIVATE_INC ${CMAKE_CURRENT_BINARY_DIR}/hidden)
    # Public generated include files
    set(PUBLIC_INC ${CMAKE_CURRENT_BINARY_DIR}/inc)

    set(GRAMMAR_FILE ${PRIVATE_INC}/hermes/${ARGS_TARGET}_grammar.h)
    set(LOADER_HEADER_FILE ${PUBLIC_INC}/hermes/${ARGS_TARGET}_loader.h)
    set(LOADER_IMPL_FILE ${PRIVATE_INC}/hermes/${ARGS_TARGET}_loader.cpp)

    set(OUTPUTS ${GRAMMAR_FILE} ${LOADER_HEADER_FILE} ${LOADER_IMPL_FILE})

    # Custom command to generate the header
    add_custom_command(
        OUTPUT ${OUTPUTS}
        WORKING_DIRECTORY ${HERMES_ROOT}
        COMMENT "Generating parser for ${TARGET}"
        COMMAND
            ${Python3_EXECUTABLE} -m hermes_gen
                --name ${ARGS_TARGET}
                --table ${GRAMMAR_FILE}
                --loader ${LOADER_HEADER_FILE}
                --impl ${LOADER_IMPL_FILE}
                --automata "${DESC_FILE}"
                ${GRAMMAR}
        VERBATIM
        DEPENDS ${GRAMMAR} ${PY_FILES} ${GRAMMAR_FILES}
    )

    # Add target to generate parse table
    add_custom_target(${ARGS_TARGET}_grammar
        DEPENDS ${OUTPUTS} ${GRAMMAR} ${PY_FILES}
    )

    # Add library
    add_library(${ARGS_TARGET}
        ${LOADER_IMPL_FILE}
    )

    # Add dependency on parse_table
    add_dependencies(${ARGS_TARGET} ${ARGS_TARGET}_grammar)

    target_include_directories(${ARGS_TARGET}
        PUBLIC
            ${PUBLIC_INC}
        PRIVATE
            ${PRIVATE_INC}
    )
    
    target_link_libraries(${ARGS_TARGET}
        PUBLIC
            ${HERMES_TARGET}
    )
    
    if(${ARGS_DEBUG})
        target_compile_definitions(${ARGS_TARGET}
            PRIVATE
                HERMES_PARSE_DEBUG
        )
        message("Added Hermes target ${ARGS_TARGET} for grammar ${ARGS_GRAMMAR} in ${CMAKE_CURRENT_SOURCE_DIR}")
    endif()

endfunction()