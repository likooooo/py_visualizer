#include "py_plugin.h"
#include "py_helper.hpp"
#include "py_exception.hpp"
#include <ios>          // std::ios_base::failure

std::vector<std::function<void()>> regist_callback_list;
bool py_engine::regist_py_custom(std::function<void()> callback)
{
    regist_callback_list.push_back(callback);
    return true;
}

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
        vector<string>,
        vector<vector<int>>, vector<vector<size_t>>, vector<vector<float>>, vector<vector<double>>, 
        vector<vector<complex<float>>>, vector<vector<complex<double>>>, 
        
        vector<array<int, 2>>, vector<array<size_t, 2>>,  vector<array<float, 2>>, vector<array<double, 2>>, 
        vector<array<complex<float>, 2>>, vector<array<complex<double>, 2>>,

        vector<array<int, 3>>, vector<array<size_t, 3>>,  vector<array<float, 3>>, vector<array<double, 3>>, 
        vector<array<complex<float>, 3>>, vector<array<complex<double>, 3>>
    >();
    for(const auto& f : regist_callback_list) f();
}
void py_engine::init_exception_for_pycall()
{
    using namespace std;
    // reference : https://en.cppreference.com/w/cpp/error/exception
    init_exception_converters<
        logic_error,   invalid_argument, domain_error,   length_error, out_of_range,
        runtime_error, range_error,      overflow_error, underflow_error,
        ios_base::failure
    >();
}
void py_engine::dispose(){
    py_plugin::ref() = py_loader();
    get_py_inter() = py_engine(false);
}


std::vector<std::string> py_plugin::paths{"core_plugins"};
py_loader& py_plugin::ref()
{
    static std::vector<std::string> paths;
    static py_loader plugin;
    if(paths != py_plugin::paths && 0 < py_plugin::paths.size() )
    {
        paths = py_plugin::paths;
        plugin = py_loader(paths.at(0));
        for(size_t i = 1; i < paths.size(); i++) plugin.append_import_to_current(paths.at(i));
    }
    return plugin;
}