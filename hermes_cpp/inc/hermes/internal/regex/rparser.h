#pragma once

#include <stdexcept>

#include <hermes/internal/regex/node.h>

namespace hermes {

NodePtr parseRegexPattern(const char* str);

} //namespace hermes