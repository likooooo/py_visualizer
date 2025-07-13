#include "py_helper.hpp"
#include <cstdlib>
#include <filesystem>
std::filesystem::path get_golden_dir()
{
    char* p = std::getenv("GOLDEN_DIR");
    return nullptr == p ? "./" : p;
}
constexpr bool test_deprecated= false;
void test_frame_update()
{
    if constexpr(test_deprecated){
        int nx = 100, ny = 100;
        std::vector<float> vec(nx * ny);
        auto callback = py_plot::create_callback_simulation_fram_done(py::object(overload_click));
        for(size_t i = 0; i < 10; i++) callback(create_ndarray_from_vector(vec, { nx, ny }));
    }
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

void test_plot_source()
{
    size_t xsize = 5;
    size_t ysize = xsize;
    using rT = float;
    rT step = 2.0 / (xsize - 1);
    vec2<rT> center{rT(xsize /2), rT(ysize/ 2)};
    std::vector<vec2<rT>> pos;
    std::vector<rT> dir;
    std::vector<rT> intensity;
    std::vector<rT> ellipticity;
    std::vector<std::string> color;
    pos.reserve(xsize * ysize);
    dir.reserve(xsize * ysize);
    intensity.reserve(xsize * ysize);
    ellipticity.reserve(xsize * ysize);
    color.reserve(xsize * ysize);
    rT scalar = 0.2;
    for(rT e : {0.0f, 0.5f, -1.0f})
    {
        pos.clear();
        dir.clear();
        intensity.clear();
        ellipticity.clear();
        color.clear();
        for(size_t y = 0; y < ysize; y++)
        {
            for(size_t x= 0; x < xsize; x++)
            {
                vec2<rT> temp{rT(x), rT(y)};
                temp -= center;
                temp *= step;
                pos.push_back(temp);
                dir.push_back(0.1_PI);
                intensity.push_back(step * scalar);
                ellipticity.push_back(e);
                color.push_back(vec2<std::string>{"red", "blue"}[int(ellipticity.back() < 0)]);
            }
        }
        plot_field<rT>(pos, dir, intensity, ellipticity, color, "source field (sigma XY)");
    }
}

void test_imshow()
{
    auto [im, shape] = load_image<std::complex<float>>(get_golden_dir() / "pupil_TE_y.bin");
    std::cout << "shape is " << shape << std::endl;
    auto [real_part, imag_part] = decompose_from<std::complex<float>, float, float>(im);
    imshow(real_part, std::vector<size_t>(shape.rbegin(), shape.rend()));
}

int main() 
{
    catch_py_error(
        py_engine::init();
        add_path_to_sys_path("core_plugins");
        test_imshow();
        test_plot_source();
        auto workspace = py_plugin::exec({"./core_plugins/gauge_io.py",
            "/home/like/model_data/X_File/LG40_poly_File/LG40_PC_CDU_7.ss",
            "/home/like/model_data/X_File/LG40_poly_File/LG40_PC_CDU_Contour_Mask_L300.oas",
            "JDV_M", "300", "--shape", "8, 8", "--verbose", "3"
        });
        py_plugin::call<void>("image_io", "test");
        catch_py_error(test_plot_curve());
        //== deprecated
        if(test_deprecated)
        {
            py_plugin::call<void>("gds_io", "plot_gds", "/home/like/doc/Documents/YuWei/gds/gds/case11.gds");
            catch_py_error(test_frame_update());
        }
        py_engine::dispose();
    );
}