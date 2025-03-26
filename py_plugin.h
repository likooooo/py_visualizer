#pragma once
#include <boost/python.hpp>
#include <boost/python/numpy.hpp>
#include <filesystem>
#include <cassert>
#include <iostream>
#include <map>
#include <algorithm>
#include <cstring>

#define catch_py_error(code) do{try{code;}catch (py::error_already_set) {PyErr_Print();exit(1);}}while(0)

namespace py = boost::python;
namespace np = boost::python::numpy;

struct py_engine{
    bool is_py_running;
    py_engine(bool init = false);
    ~py_engine();
    void operator = (py_engine&& py);

    static void init();
    static void dispose();
private:
    static py_engine& get_py_inter();
};

struct py_plugin
{
    static py_plugin& ref();
};