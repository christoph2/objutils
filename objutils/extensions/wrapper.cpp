
#include <pybind11/functional.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "difflib.h"

namespace py = pybind11;
using namespace difflib;


PYBIND11_MODULE(hexfiles_ext, m) {
	py::class_<SequenceMatcher<std::string>>(m, "SequenceMatcher")
		.def(py::init<const std::string &, const std::string &, SequenceMatcher<std::string>::junk_function_type, bool>(), py::arg("a"), py::arg("b"), py::arg("is_junk")=nullptr, py::arg("auto_junk")=true)
		.def("ratio", &SequenceMatcher<std::string>::ratio)
		.def("get_opcodes", &SequenceMatcher<std::string>::get_opcodes)
	;
}
