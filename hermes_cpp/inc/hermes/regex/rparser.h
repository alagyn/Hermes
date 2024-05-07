#pragma once

#include <stdexcept>

#include <hermes/regex/node.h>

namespace hermes {

NodePtr parseRegexPattern(const char* str);

} //namespace hermes