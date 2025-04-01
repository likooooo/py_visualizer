#include "py_helper.hpp"
#include <cstdlib>

void test_frame_update()
{
    int nx = 100, ny = 100;
    std::vector<float> vec(nx * ny);
    auto callback = py_plot::create_callback_simulation_fram_done(py::object(overload_click));
    for(size_t i = 0; i < 10; i++) callback(create_ndarray_from_vector(vec, { nx, ny }));
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
    constexpr bool test_deprecated= false;
    catch_py_error(py_engine::init());
    add_path_to_sys_path("core_plugins");
    auto workspace = py_plugin::exec({"./core_plugins/gauge_io.py",
        "/home/like/model_data/X_File/LG40_poly_File/LG40_PC_CDU_7.ss",
        "/home/like/model_data/X_File/LG40_poly_File/LG40_PC_CDU_Contour_Mask_L300.oas",
        "JDV_M", "300", "--shape", "8, 8", "--verbose", "3"
    });
    auto cutlines = convert_to<np::array2d>(workspace["cutlines_in_um"]);
    std::cout << cutlines.shape(0) <<","<<cutlines.shape(1) << std::endl;

    py_plugin::call<void>("image_io", "test");
    catch_py_error(test_plot_curve());

    //== deprecated
    if(test_deprecated)
    {
        py_plugin::call<void>("gds_io", "plot_gds", "/home/like/doc/Documents/YuWei/gds/gds/case11.gds");
        catch_py_error(test_frame_update());
    }
    py_engine::dispose();
}