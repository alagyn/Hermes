cmake_minimum_required(VERSION 3.26)

project(hermes)

option(HERMES_PYTHON "Enable Hermes python bindings" OFF)
option(HERMES_TESTS "Enable Hermes Test builds" OFF)

set(HERMES_VERSION 1.1.0)

set(HERMES_ROOT ${CMAKE_CURRENT_SOURCE_DIR})
set(HERMES_GEN_ROOT ${CMAKE_CURRENT_SOURCE_DIR}/hermes_gen)
set(HERMES_CPP_ROOT ${CMAKE_CURRENT_SOURCE_DIR}/hermes_cpp)


if(HERMES_PYTHON)
    if(${MSVC})
        set(PY_COMPONENTS Interpreter Development)
    else()
        set(PY_COMPONENTS Interpreter Development.Module)
    endif()
else()
    set(PY_COMPONENTS Interpreter)
endif()

find_package(Python3 
    REQUIRED 
        COMPONENTS ${PY_COMPONENTS}
)

add_subdirectory(third-party)

set(PY_FILES
    ${HERMES_GEN_ROOT}/__main__.py
    ${HERMES_GEN_ROOT}/__init__.py
    ${HERMES_GEN_ROOT}/consts.py
    ${HERMES_GEN_ROOT}/directives.py
    ${HERMES_GEN_ROOT}/errors.py
    ${HERMES_GEN_ROOT}/grammar.py
    ${HERMES_GEN_ROOT}/hermes_logs.py
    ${HERMES_GEN_ROOT}/lalr1_automata.py
    ${HERMES_GEN_ROOT}/parseTable.py
    ${HERMES_GEN_ROOT}/counterexample/configurations.py
    ${HERMES_GEN_ROOT}/counterexample/conflict.py
    ${HERMES_GEN_ROOT}/counterexample/costs.py
    ${HERMES_GEN_ROOT}/counterexample/counterexample.py
    ${HERMES_GEN_ROOT}/counterexample/counterexampleGen.py
    ${HERMES_GEN_ROOT}/counterexample/derivation.py
    ${HERMES_GEN_ROOT}/counterexample/orderedSet.py
    ${HERMES_GEN_ROOT}/counterexample/stateItem.py
    ${HERMES_GEN_ROOT}/counterexample/utils.py
    ${HERMES_GEN_ROOT}/writers/hermesHeader.py
    ${HERMES_GEN_ROOT}/writers/loader.py
    ${HERMES_GEN_ROOT}/writers/table.py
    ${HERMES_GEN_ROOT}/writers/utils.py
    ${HERMES_GEN_ROOT}/writers/pybind.py
)

add_library(hermes)

target_include_directories(hermes
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/hermes_cpp/inc>
        $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>
)

target_sources(hermes
    PRIVATE
        ${HERMES_CPP_ROOT}/src/regex/node_strs.cpp
        ${HERMES_CPP_ROOT}/src/regex/node.cpp
        ${HERMES_CPP_ROOT}/src/regex/regex.cpp
        ${HERMES_CPP_ROOT}/src/regex/rparser.cpp
        ${HERMES_CPP_ROOT}/src/grammar.cpp
        ${HERMES_CPP_ROOT}/src/scanner.cpp
    PUBLIC
        FILE_SET HEADERS
        BASE_DIRS ${HERMES_CPP_ROOT}/inc
        FILES 
            ${HERMES_CPP_ROOT}/inc/hermes/errors.h
            ${HERMES_CPP_ROOT}/inc/hermes/parser.h
            ${HERMES_CPP_ROOT}/inc/hermes/internal/grammar.h
            ${HERMES_CPP_ROOT}/inc/hermes/internal/scanner.h
            ${HERMES_CPP_ROOT}/inc/hermes/internal/regex/regex.h
            ${HERMES_CPP_ROOT}/inc/hermes/internal/regex/match.h
)

set_target_properties(hermes
    PROPERTIES
    INTERPROCEDURAL_OPTIMIZATION ON
    VISIBILITY_INLINES_HIDDEN ON
    CXX_STANDARD 17
)

if(HERMES_PYTHON)
    add_library(hermes_pybind
        ${HERMES_CPP_ROOT}/src/bind-hermes-py.cpp
    )

    target_link_libraries(hermes_pybind
        PRIVATE
            Python3::Module
            pybind11::headers
            hermes
    )

    target_compile_definitions(hermes_pybind
        PUBLIC PYBIND11_DETAILED_ERROR_MESSAGES
    )
endif()

install(
    TARGETS
        hermes
        DESTINATION lib
    EXPORT hermesTargets
    FILE_SET
        HEADERS
        DESTINATION include
    INCLUDES DESTINATION include
)

install(
    EXPORT hermesTargets
    FILE hermesTargets.cmake
    NAMESPACE hermes::
    DESTINATION cmake
)

install(
    DIRECTORY hermes_gen
    DESTINATION .
    FILES_MATCHING PATTERN *.py
)

include(CMakePackageConfigHelpers)
configure_package_config_file(
    cmake/hermesConfig.cmake.in
    "${CMAKE_CURRENT_BINARY_DIR}/hermesConfig.cmake"
    INSTALL_DESTINATION cmake
)

write_basic_package_version_file(
    ${CMAKE_CURRENT_BINARY_DIR}/cmake/hermesConfigVersion.cmake
    VERSION ${HERMES_VERSION}
    COMPATIBILITY AnyNewerVersion
)

install(
    FILES 
    "${CMAKE_CURRENT_BINARY_DIR}/hermesConfig.cmake" 
    "${CMAKE_CURRENT_BINARY_DIR}/cmake/hermesConfigVersion.cmake"
    "${CMAKE_SOURCE_DIR}/cmake/add_hermes_grammar.cmake"
    DESTINATION cmake
)

if(HERMES_TESTS)
    add_subdirectory(tests)
endif()