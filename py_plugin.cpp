#include "py_plugin.h"
#include "py_helper.hpp"
#include "py_exception.hpp"
#include <ios>          // std::ios_base::failure

py_engine::py_engine(bool init) : is_py_running(init){
    if(!init) return;
    Py_Initialize();
    np::initialize();
}
py_engine::~py_engine(){
    if(!is_py_running) return;
    Py_Finalize();
}
void py_engine::operator = (py_engine&& py) {
    std::swap(is_py_running, py.is_py_running);
}
py_engine& py_engine::get_py_inter(){
    static py_engine py(false); 
    return py;
};
void py_engine::init(){
    if(get_py_inter().is_py_running) return;
    get_py_inter() = py_engine(true);
    using namespace std;
    init_stl_converters<
        vector<int>, vector<size_t>, vector<float>, vector<double>, vector<complex<float>>, vector<complex<double>>,vector<string>,
        vector<vector<float>>, vector<vector<double>>,

        array<int, 2>, array<size_t, 2>,  array<float, 2>, array<double, 2>, array<complex<float>, 2>, array<complex<double>, 2>,
        array<int, 3>, array<size_t, 3>,  array<float, 3>, array<double, 3>, array<complex<float>, 3>, array<complex<double>, 3>,
        array<array<float, 2>, 2>, array<array<double, 2>, 2>
    >();

    // reference : https://en.cppreference.com/w/cpp/error/exception
    init_exception_converters<
        logic_error,   invalid_argument, domain_error,   length_error, out_of_range,
        runtime_error, range_error,      overflow_error, underflow_error,
        ios_base::failure
    >();
}
void py_engine::dispose(){
    get_py_inter() = py_engine(false);
}
py_plugin& py_plugin::ref()
{
    static py_plugin plugin;
    return plugin;
}
