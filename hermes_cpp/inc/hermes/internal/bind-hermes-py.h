#include <pybind11/pybind11.h>

#include <fstream>
#include <hermes/parser.h>

namespace py = pybind11;
using namespace pybind11::literals;

namespace hermes {

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
        py::print(stream);
        py::print(stream.get_type());
        ByteStream bs(stream);
        py::print("Making IS");
        auto input = std::make_shared<std::istream>(&bs);

        bool error = false;
        py::print("Parsing");
        HermesReturn out = parser->parse(input, error);
        return py::make_tuple(out, error);
    }
};

void streamDestructor(void* ptr)
{
    auto data = (std::shared_ptr<std::istream>*)ptr;
    delete data;
}

py::capsule loadInputFile(const std::string& filename)
{
    std::shared_ptr<std::ifstream>* out = new std::shared_ptr<std::ifstream>();
    *out = std::make_shared<std::ifstream>(filename);
    if(!(*out)->good())
    {
        delete out;
        throw std::runtime_error("Unable to open input file");
    }
    return py::capsule(out, streamDestructor);
}

py::capsule loadInputBytes(char* data)
{
    std::shared_ptr<std::stringstream>* out =
        new std::shared_ptr<std::stringstream>();
    *out = std::make_shared<std::stringstream>(data);
    return py::capsule(out, streamDestructor);
}

template<typename HermesReturn>
void init_hermes(py::module_& m)
{
    py::class_<PyParser<HermesReturn>>(m, "Parser")
        .def("parse", &PyParser<HermesReturn>::parse, "stream"_a);

    m.def("load_input_file", loadInputFile, "filename"_a);
    m.def("load_input_bytes", loadInputBytes, "data"_a);
}

} //namespace hermes