#include <pybind11/pybind11.h>

#include <fstream>
#include <vector>

#include <hermes/parser.h>

namespace py = pybind11;
using namespace pybind11::literals;

namespace hermes {

static py::module_ _this_module;

constexpr size_t BUFF_SIZE = 1024;

class ByteStream : public std::streambuf
{
public:
    py::iterable stream;
    py::iterator iter;
    size_t readSize;
    char* buffer;

    ByteStream(py::iterable stream)
        : stream(stream)
        , iter(stream.begin())
        , readSize(0)
        , buffer(new char[BUFF_SIZE + 1])
    {
        buffer[BUFF_SIZE] = 0;
        setg(buffer, buffer, buffer);
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
            for(readSize = 0; readSize < BUFF_SIZE; ++readSize, ++iter)
            {
                if(iter == py::iterator::sentinel())
                {
                    break;
                }
                auto temp = *iter;
                // Doesn't like to cast to char for some reason?
                buffer[readSize] = static_cast<char>(iter->cast<int>());
            }
            this->setg(buffer, buffer, buffer + readSize);
        }

        return this->gptr() == this->egptr()
                   ? std::char_traits<char>::eof()
                   : std::char_traits<char>::to_int_type(*this->gptr());
    }
};

class FileStream : public std::streambuf
{
public:
    py::iterable stream;
    py::iterator iter;
    size_t readSize;
    std::vector<char> buffer;

    FileStream(py::iterable stream)
        : stream(stream)
        , iter(stream.begin())
        , readSize(0)
        , buffer(BUFF_SIZE, 0)
    {
        buffer[BUFF_SIZE] = 0;
        setg(buffer.data(), buffer.data(), buffer.data());
    }

    int underflow() override
    {
        // If we are at the end of the buffer
        if(this->gptr() == this->egptr())
        {
            // read more data from python
            for(readSize = 0; readSize < BUFF_SIZE; ++iter)
            {
                if(iter == py::iterator::sentinel())
                {
                    break;
                }
                // File IO returns bytes, can be more than one char
                auto temp = *iter;
                int len = temp.attr("__len__")().cast<int>();

                // resize if we need to
                // Buffer should still remain close to the original size
                if(readSize + len > buffer.size())
                {
                    buffer.resize(readSize + len, 0);
                }

                auto bIter = temp.begin();
                for(; bIter != temp.end(); ++bIter, ++readSize)
                {
                    // Doesn't like to cast to char for some reason?
                    buffer[readSize] = static_cast<char>(bIter->cast<int>());
                }
            }
            this->setg(buffer.data(), buffer.data(), buffer.data() + readSize);
        }

        return this->gptr() == this->egptr()
                   ? std::char_traits<char>::eof()
                   : std::char_traits<char>::to_int_type(*this->gptr());
    }
};

template<typename HermesReturn>
class PyParser
{
private:
    std::shared_ptr<Parser<HermesReturn>> parser;

public:
    PyParser(std::shared_ptr<Parser<HermesReturn>> parser)
        : parser(parser)
    {
    }

    py::tuple parse(py::iterable stream)
    {
        std::streambuf* buff;
        auto byteArrayType = py::globals()["__builtins__"].attr("bytearray");
        auto fileReaderType = _this_module.attr("_BufferedReader");

        if(py::isinstance<py::bytes>(stream)
           || py::isinstance(stream, byteArrayType))
        {
            buff = new ByteStream(stream);
        }
        else if(py::isinstance(stream, fileReaderType))
        {
            buff = new FileStream(stream);
        }
        else
        {
            throw std::runtime_error(
                "Invalid type, expectes bytes, bytearray, or file handle"
            );
        }

        auto input = std::make_shared<std::istream>(buff);

        bool error = false;

        HermesReturn out = parser->parse(input, error);
        return py::make_tuple(out, error);
    }
};

template<typename HermesReturn>
void init_hermes(py::module_& m)
{
    py::class_<PyParser<HermesReturn>>(m, "Parser")
        .def("parse", &PyParser<HermesReturn>::parse, "stream"_a);

    auto package = pybind11::module::import("io");
    auto bufferedreader = package.attr("BufferedReader");
    m.add_object("_BufferedReader", bufferedreader);

    /*
        store a reference to the module to get at it later
        Not sure of a better way to do this, but it doesn't seem
        to cause any issues, and this func only executes once per interpeter...

        Specifically need to get access to the above type for use in the parse
        func so we don't have to reimport it every time
    */
    m.inc_ref();
    _this_module = m;
}

} //namespace hermes