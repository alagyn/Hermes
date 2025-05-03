#include <pybind11/pybind11.h>

#include <fstream>
#include <hermes/parser.h>

namespace py = pybind11;
using namespace pybind11::literals;

namespace hermes {

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

    py::tuple parse(py::capsule input)
    {
        auto stream = (std::shared_ptr<std::istream>*)input.get_pointer();

        bool error = false;
        HermesReturn out = parser->parse(*stream, error);
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
        .def("parse", &PyParser<HermesReturn>::parse, "input_stream"_a);

    m.def("load_input_file", loadInputFile, "filename"_a);
    m.def("load_input_bytes", loadInputBytes, "data"_a);
}

} //namespace hermes