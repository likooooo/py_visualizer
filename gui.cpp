#include "py_helper.hpp"
int main() {
    py_loader::init();
    int nx = 100, ny = 100;
    std::vector<float> vec(nx * ny);
    auto callback = py_plot::create_callback_simulation_fram_done(py::object(overload_click));
    while (callback(create_ndarray_from_vector(vec, { nx, ny })));
}