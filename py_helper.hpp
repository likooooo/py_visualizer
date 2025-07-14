#pragma once
#include "py_plugin.h"
#include <type_traist_notebook/type_traist.hpp>

//== for convert.hpp
template<class TTo>
struct convert<py::object, TTo>{
    TTo operator()(py::object from){
        catch_py_error(return py::extract<TTo>(from));
    }
};
template<class TTo>
struct convert<pyobject_wrapper, TTo>{
    TTo operator()(pyobject_wrapper from){
        catch_py_error(return py::extract<TTo>(from));
    }
};
template<class TTo>
struct convert<py::api::proxy<boost::python::api::item_policies>, TTo>{
    TTo operator()(py::api::proxy<boost::python::api::item_policies> from){
        catch_py_error(return py::extract<TTo>(from));
    }
};
template<class TTo>
struct convert<py::api::proxy<boost::python::api::const_item_policies>, TTo>{
    TTo operator()(py::api::proxy<boost::python::api::const_item_policies> from){
        catch_py_error(return py::extract<TTo>(from));
    }
};

template<>struct convert<py::object, std::string>{
    std::string operator()(py::object from){
        catch_py_error(return py::extract<std::string>(from));
    }
};
template<>struct convert<pyobject_wrapper, std::string>{
    std::string operator()(pyobject_wrapper from){
        catch_py_error(return py::extract<std::string>(from));
    }
};
template<>struct convert<py::api::proxy<boost::python::api::item_policies>, std::string>{
    std::string operator()(py::api::proxy<boost::python::api::item_policies> from){
        catch_py_error(return py::extract<std::string>(from));
    }
};
template<> struct convert<py::api::proxy<boost::python::api::const_item_policies>, std::string>{
    std::string operator()(py::api::proxy<boost::python::api::const_item_policies> from){
        catch_py_error(return py::extract<std::string>(from));
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

template<class TContainer> class stl_container_converter 
{
    using value_type = typename TContainer::value_type;

    struct stl_to_python
    // #if defined BOOST_PYTHON_SUPPORTS_PY_SIGNATURES
    //     : converter::to_python_target_type<py::list>
    // #endif
    {
        static PyObject* convert(const TContainer& vec) 
        {
            py::list list;
            for (const auto& elem : vec) list.append(elem);
            return py::incref(list.ptr());
        }
    };
    struct stl_from_python
    {
        stl_from_python()
        {
            boost::python::converter::registry::push_back(
                &convertible, 
                &construct, 
                py::type_id< TContainer >()
        // #if defined BOOST_PYTHON_SUPPORTS_PY_SIGNATURES 
        //         , &converter::expected_from_python_type<py::list>::get_pytype
        // #endif
            );
        }
        static void* convert_from_python(PyObject* obj) 
        {
            void* p = std::malloc(sizeof(TContainer));
            TContainer& vec = *(new (p)TContainer());
            if (PyList_Check(obj) || PyTuple_Check(obj)) 
            {
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
        static void* convertible(PyObject* obj_ptr) 
        {
            return obj_ptr;//PyList_Check(obj_ptr) ? obj_ptr : convert_from_python(obj_ptr);
        }
        static void construct(PyObject* obj_ptr, py::converter::rvalue_from_python_stage1_data* data) 
        {
            int length = PyList_Size(obj_ptr);
            if (length < 0) py::throw_error_already_set();

            void* storage = ((py::converter::rvalue_from_python_storage<TContainer>*)data)->storage.bytes;
            
            if constexpr(is_vector_v<TContainer>){
                new (storage) TContainer(length);
            }else{ // std::array
                new (storage) TContainer();
            }
            TContainer& vec = *reinterpret_cast<TContainer*>(storage);
            for (int i = 0; i < length; ++i) {
                PyObject* item = PyList_GetItem(obj_ptr, i);
                vec.at(i) =py::extract<value_type>(item);
            }
            data->convertible = storage;
        }
    };
public:
    static py::list to_list(const TContainer& c)
    {
        return py::list(c);
    }
    static void register_converter() 
    {
        const py::converter::registration* regVectorValue = py::converter::registry::query(py::type_id<TContainer>());
        if (!(nullptr == regVectorValue || nullptr == (*regVectorValue).m_to_python)) {
            // std::cerr << TypeReflection<TContainer>() << "'s to python converter has alreadly registed before." << std::endl;
            return;
        }

        if constexpr(is_vector_v<TContainer>){
            if constexpr(is_vec_or_array_v<value_type>) stl_container_converter<value_type>::register_converter();
            py::class_<TContainer>(TypeReflection<TContainer>().c_str()).def(py::vector_indexing_suite<TContainer>())
                .def("__repr__", (std::string (*)(const TContainer&))&to_string<TContainer>)
                .def("clear", &TContainer::clear)
            ;
        }
        else if constexpr(std::is_array_v<TContainer>){
            if constexpr(is_vec_or_array_v<value_type>) stl_container_converter<value_type>::register_converter();
            stl_from_python();
            auto a = py::class_<TContainer>(TypeReflection<TContainer>().c_str()).def(py::init<>())
                .def("__iter__", py::iterator<TContainer>())
                .def("__repr__", (std::string (*)(const TContainer&))&to_string<TContainer>)
            ;
        }
        else{
            std::cerr << TypeReflection<TContainer>() << "'s to python converter is NOT registed." << std::endl;
        }
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
    std::string t = "";
    if constexpr(std::is_same_v<T, int>) t= "n";
    else if constexpr(std::is_same_v<T, float>) t= "f";
    else if constexpr(std::is_same_v<T, double>) t= "d";
    else if constexpr(std::is_same_v<T, complex_t<float>>) t= "c";
    else if constexpr(std::is_same_v<T, complex_t<double>>) t= "z";
    else unreachable_constexpr_if<T>{};
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

