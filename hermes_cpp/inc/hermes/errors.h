#pragma once

#include <exception>
#include <string>

class HermesError : public std::exception
{
public:
    std::string msg;

    HermesError(std::string msg)
        : msg(msg)
    {
    }

    const char* what() const noexcept override
    {
        return msg.c_str();
    }
};