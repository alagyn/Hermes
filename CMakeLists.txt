cmake_minimum_required(VERSION 3.26)

project(hermes)

find_package(Python3 
    REQUIRED 
        COMPONENTS Interpreter
)

set(HERMES_VERSION 1.0.0)

set(HERMES_ROOT ${CMAKE_CURRENT_SOURCE_DIR})
set(HERMES_GEN_ROOT ${CMAKE_CURRENT_SOURCE_DIR}/hermes_gen)
set(HERMES_CPP_ROOT ${CMAKE_CURRENT_SOURCE_DIR}/hermes_cpp)

set(PY_FILES
    ${HERMES_GEN_ROOT}/consts.py
    ${HERMES_GEN_ROOT}/directives.py
    ${HERMES_GEN_ROOT}/errors.py
    ${HERMES_GEN_ROOT}/grammar.py
    ${HERMES_GEN_ROOT}/lalr1_automata.py
    ${HERMES_GEN_ROOT}/main.py
    ${HERMES_GEN_ROOT}/writers/hermesHeader.py
    ${HERMES_GEN_ROOT}/writers/loader.py
    ${HERMES_GEN_ROOT}/writers/parseTable.py
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

option(HERMES_TESTS "Enable Hermes Test builds" OFF)

install(
    TARGETS
        hermes
        DESTINATION lib
    EXPORT hermesTargets
    FILE_SET
        HEADERS
        DESTINATION hermes_cpp/inc
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
    "${CMAKE_CURRENT_SOURCE_DIR}/cmake/add_hermes_grammar.cmake"
    DESTINATION cmake
)


if(${HERMES_TESTS})
    add_subdirectory(third-party)
    add_subdirectory(tests)
endif()