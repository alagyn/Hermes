#pragma once

#include <catch2/catch_test_macros.hpp>
#include <hermes/internal/regex/regex.h>

void check(
    const hermes::Regex& r,
    const char* str,
    bool fullmatch = true,
    bool partial = false
);

void singleCheck(
    const char* re,
    const char* str,
    bool fullmatch = true,
    bool partial = false
);