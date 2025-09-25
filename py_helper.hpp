#pragma once
#include "py_plugin.h"
#include <type_traist_notebook/type_traist.hpp>
#include "py_convert.hpp"

namespace details
{
    template<class TTuple, size_t N = 0> inline void _Update(TTuple& values, 
        const std::vector<std::string>& keys, const py::dict& dict)
    {
        using T = typename std::tuple_element<N, TTuple>::type;
        
        std::get<N>(values) = dict.has_key(keys.at(N)) ? T(py::extract<T>(dict[keys.at(N)])) : T{};
        if constexpr(N + 1 < std::tuple_size<TTuple>::value){
            _Update<TTuple, N + 1>(values, keys, dict);
        }
    }
}
template<class TTuple> inline void get_dict_values(TTuple& values, 
    const std::vector<std::string>& keys, const py::object& obj){
    py::dict dict = py::extract<py::dict>(obj);    
    details::_Update<TTuple>(values, keys, dict);
} 
template<class TTuple> inline TTuple get_dict_values(const std::vector<std::string>& keys, const py::object& obj){
    TTuple values{};
    py::dict dict = py::extract<py::dict>(obj);    
    details::_Update<TTuple>(values, keys, dict);
    return values;
} 
template<class T, class TAlloc> inline 
np::ndarray create_ndarray_from_vector(const std::vector<T, TAlloc>& data, std::vector<int> shape) {
    std::reverse(shape.begin(), shape.end());
    std::vector<int> strides(shape.size());
    strides.back() = sizeof(T);
    for (int i = shape.size() - 2; i >= 0; --i) {
        strides[i] = strides[i + 1] * shape[i + 1];
    }
    np::dtype dtype = np::dtype::get_builtin<T>();
    catch_py_error(np::ndarray ndarray = np::from_data(
        reinterpret_cast<const void*>(data.data()), dtype,
        py::tuple(py::list(shape)),
        py::tuple(py::list(strides)),
        py::object()
    );
    return ndarray;
        );
}

inline size_t sizeof_element_ndarray(np::ndarray arr) {
    return py::extract<size_t>(arr.get_dtype().attr("itemsize"));
}
inline size_t get_ndarray_size(np::ndarray arr) {
    size_t size = 1;
    for (size_t i = 0; i < arr.get_nd(); ++i) {
        size *= arr.shape(i);
    }
    return size;
}
template <class TPixel> inline  std::pair<TPixel*, size_t> ndarray_ref_no_padding(np::ndarray arr) 
{
    // using T = TPixel;//std::conditional_t<is_real_or_complex_v<TPixel>,TPixel , typename TPixel::value_type>;
    using T = typename TPixel::value_type;
    static_assert(std::is_standard_layout_v<TPixel>);
    try{
        auto dtype = arr.get_dtype();
        if(np::dtype::get_builtin<T>() != dtype) 
            throw std::runtime_error("dtype error " + to_string(std::make_tuple(
                std::string(py::extract<std::string>(dtype.attr("str"))), 
                std::string(py::extract<std::string>(
                    np::dtype::get_builtin<T>().attr("str"))),
                TypeReflection<TPixel>()
            )));
        size_t bytes = sizeof_element_ndarray(arr) * get_ndarray_size(arr); 
        return {reinterpret_cast<TPixel*>(arr.get_data()), bytes/sizeof(TPixel)};
    }
    catch (py::error_already_set) {
        PyErr_Print();exit(1);
    };
}



[[deprecated("use py_plugin instead")]]  struct py_plot {
    static std::filesystem::path& get_default_visualizer_dir()
    {
        static std::filesystem::path path = "/usr/local/bin";
        return path;
    }
    py_loader loader;
    pyobject_wrapper visulizer;
    bool event_init = false;
    py_plot(std::filesystem::path path = get_default_visualizer_dir()) : loader(path) {
        // std::cout <<"path=" << path<<std::endl;
        visulizer = loader["visualizer"];
    }
    static bool& get_cancel_token() {
        static  bool cancel = false;
        return cancel;
    }
    static bool on_plot_close(py::object event) {
        // printf("gui closing...\n");
        get_cancel_token() = true;
        return false;
    }
    static auto create_callback_simulation_fram_done(
        py::object callback_click = py::object(),
        py::object callback_motion = py::object()
    ) {
        auto callback_fram_display = [plot = py_plot(), callback_click, callback_motion](np::ndarray data) mutable {
            if (get_cancel_token()) return false;
            catch_py_error(plot.visulizer["update"](data));
            if (!plot.event_init) {
                catch_py_error(plot.visulizer["regist_on_close"](py_plot::on_plot_close));
                catch_py_error(auto func = plot.visulizer["regist_click_and_motion"](callback_click, callback_motion));
                plot.event_init = true;
            }
            return !get_cancel_token();
        };
        return callback_fram_display;
    }
};

using pycallback_update_frame = decltype(py_plot::create_callback_simulation_fram_done(py::object()));

inline void overload_click(int type, int flag, float dx, float dy) {
    const std::array<const char*, 4> btn_type{ "", "left", "mid", "right" };
    printf("%s  %s button at (%f, %f)\n", 0 == flag ? "press" : "release", btn_type.at(type), dx, dy);
}

template<class TVec> inline void imshow(const TVec& rowdata, const std::vector<size_t>& dim){
    std::vector<int> d(dim.size());
    std::transform(dim.begin(), dim.end(), d.begin(), [](size_t n){return int(n);});
    catch_py_error(py_plot().visulizer["display_image"](create_ndarray_from_vector(rowdata, d)));
}
template<class T> inline std::tuple<std::vector<T>, vec2<size_t>> load_image(const std::string& path, const std::vector<size_t> shape = {}){
    constexpr const char* str = get_numerical_type_str_suffix<T>();
    static_assert("" != str);
    std::string t = str;
    py::object obj;
    catch_py_error(obj = py_plot().visulizer["load_binary_image_file"](path, convert_to<std::vector<std::string>>(shape), t));
    np::ndarray array = convert_to<np::ndarray>(obj);
    auto [p, size] = ndarray_ref_no_padding<vec<T, 1>>(array);
    size_t y = array.shape(0);
    size_t x = size / y;
    return std::tuple<std::vector<T>, vec2<size_t>>(std::vector<T>((T*)p, (T*)p + size), vec2<size_t>{y, x});
}

template<class T> inline void plot_curves(const std::vector<std::vector<T>>& rowdata, 
    const std::vector<float>& start_x,
    const std::vector<float>& step_x,
    const std::vector<std::string>& legends,
    const std::vector<std::string>& plot_dot_types,
    const float sample_rate = 1.0
){
    py_plugin::call<void>("plot_curves", "plot_curves",
        py::list(rowdata),
        py::list(start_x),
        py::list(step_x),
        py::list(legends),
        py::list(plot_dot_types),
        sample_rate
    );
}

template<class rT> inline void plot_field(
    const std::vector<vec2<rT>>& pos,
    const std::vector<rT>& dir,
    const std::vector<rT>& intensity,
    const std::vector<rT>& ellipticity,
    const std::vector<std::string>& color,
    const std::string& title = ""
){
    py_plugin::call<void>("plot_source", "plot_source_field", 
        py::list(pos), 
        py::list(dir),
        py::list(intensity),
        py::list(ellipticity),
        py::list(color),
        title
    );
}

