#pragma once
#include "py_plugin.h"
#include <type_traist_notebook/type_traist.hpp>

//== for convert.hpp
template<class TTo>
struct convert<py::object, TTo>{
    constexpr TTo operator()(py::object from){
        return py::extract<TTo>(from);
    }
};
template<class TTo>
struct convert<py::api::proxy<boost::python::api::item_policies>, TTo>{
    constexpr TTo operator()(py::api::proxy<boost::python::api::item_policies> from){
        return py::extract<TTo>(from);
    }
};
template<class T> inline 
std::ostream& py_list_to_string (std::ostream& strean, const py::list& py_list,const char* separator = "\n") {
    int list_count = len(py_list);
    auto print = [&](int offset, int size) {
        for (int i = 0; i < size; ++i) {
            py::object temp = py_list[offset + i];
            T& n = py::extract<T>(temp);
            strean << n << separator;
        }
    };
    if (list_count > 10) {
        print(0, 5);
        strean << "..." << separator;
        print(list_count - 6, 5);
    }
    else{
        print(0, list_count);
    }
    return strean;
}
template <typename, typename = void>struct has_resize : std::false_type {};
template <typename T> struct has_resize<T, std::void_t<decltype(std::declval<T>().resize(std::declval<typename T::size_type>()))>> : std::true_type {};
template <typename T> constexpr bool has_resize_v = has_resize<T>::value;

template<class TContainer> struct stl_container_converter {
    static PyObject* convert(const TContainer& vec) {
        py::list list;
        for (const auto& elem : vec) list.append(elem);
        return py::incref(list.ptr());
    }
    static void* convert_from_python(PyObject* obj) {
        void* p = std::malloc(sizeof(TContainer));
        TContainer& vec = *(new (p)TContainer());
        if (PyList_Check(obj) || PyTuple_Check(obj)) {
            py::handle<> handle(py::borrowed(obj));
            py::list list(handle);
            int n = len(list);
            if constexpr(has_resize_v<TContainer>){
                vec.resize(n);
            }else{
                if(n > vec.size()){
                    throw std::out_of_range(std::string(__PRETTY_FUNCTION__) + " (require size, acturay size)=" + to_string(std::make_tuple(n, vec.size())));
                }
            }
            for (int i = 0; i < n; i++) vec[i] = py::extract<typename TContainer::value_type>(list[i]);
        }
        return p;
    }
    static void register_converter() {
        py::to_python_converter<TContainer, stl_container_converter<TContainer>>();
        py::converter::registry::insert(
            &convert_from_python,
            py::type_id<TContainer>()
        );
    }
};
template<class T, class ...TRest> inline
void init_stl_converters() {
    stl_container_converter<T>::register_converter();
    if constexpr (sizeof...(TRest)) {
        init_stl_converters<TRest...>();
    }
}


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
    static_assert(std::is_standard_layout_v<TPixel>);
    try{
        auto dtype = arr.get_dtype();
        if(np::dtype::get_builtin<typename TPixel::value_type>() != dtype) 
            throw std::runtime_error("dtype error " + to_string(std::make_tuple(
                std::string(py::extract<std::string>(dtype.attr("str"))), TypeReflection<TPixel>()
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

template<class T> inline void plot_curves(const std::vector<std::vector<T>>& rowdata, 
    const std::vector<float>& start_x,
    const std::vector<float>& step_x,
    const std::vector<std::string>& legends,
    const std::vector<std::string>& plot_dot_types,
    const float sample_rate = 1.0
){
    catch_py_error(py_plot().visulizer["plot_curves"](
        py::list(rowdata),
        py::list(start_x),
        py::list(step_x),
        py::list(legends),
        py::list(plot_dot_types),
        sample_rate
    ));
}
