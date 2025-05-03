#include <hermes/internal/bind-hermes-py.h>

#include <istream>

#include <hermes/parser.h>

using namespace hermes;

constexpr size_t BUFF_SIZE = 1024;

class ByteStream : public std::streambuf
{
public:
    py::iterable stream;
    py::typing::Iterator<pybind11::iterator::reference> iter;
    size_t readSize;
    char* buffer;

    ByteStream(py::iterable stream)
        : stream(stream)
        , iter(py::make_iterator(stream))
        , readSize(0)
        , buffer(new char[BUFF_SIZE])
    {
    }

    ~ByteStream()
    {
        delete buffer;
    }

    int underflow() override
    {
        // If we are at the end of the buffer
        if(this->gptr() == this->egptr())
        {
            // read more data from python
            readSize = 0;
        }
    }
};
