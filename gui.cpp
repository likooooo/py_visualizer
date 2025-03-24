#include "py_helper.hpp"

void test_frame_update()
{
    int nx = 100, ny = 100;
    std::vector<float> vec(nx * ny);
    auto callback = py_plot::create_callback_simulation_fram_done(py::object(overload_click));
    while (callback(create_ndarray_from_vector(vec, { nx, ny })));
}
void test_plot_curve()
{
    std::vector<std::vector<float>> curves{
        std::vector<float>{1, 4, 7, 10},
        std::vector<float>{2, 5, 8},
        std::vector<float>{3, 6, 9, 12, 15}
    };
    for(float sample_rate : {0.5f, 1.0f})
        plot_curves(curves,{0, 1, 2}, {0.5, 1, 1.5}, {"Curve 1", "Curve 2", "Curve 3"}, {"--o", "--", ":*"}, sample_rate);
}

int main() 
{
    py_loader::init();
    // test_frame_update();
    test_plot_curve();
}