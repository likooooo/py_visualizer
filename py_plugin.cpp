#include "py_plugin.h"
#include "py_helper.hpp"

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
    init_stl_converters<
        std::vector<int>, std::vector<size_t>, 
        std::vector<float>, std::vector<double>,
        std::vector<std::string>,
        std::vector<std::vector<float>>,
        std::vector<std::vector<double>>
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