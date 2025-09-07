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


template <typename, typename = void> struct has_resize : std::false_type {};
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
            debug_unclassified::out(TypeReflection<TContainer>(), "'s to python converter has alreadly registed before." );
            return;
        }

        if constexpr(is_vector_v<TContainer>){
            if constexpr(is_vec_or_array_v<value_type>) stl_container_converter<value_type>::register_converter();
            py::class_<TContainer>(TypeReflection<TContainer>().c_str()).def(py::vector_indexing_suite<TContainer>())
                .def("__repr__", (std::string (*)(const TContainer&))&to_string<TContainer>)
                .def("clear", &TContainer::clear)
                .def("reserve", &TContainer::reserve)
                .def("resize", (void (TContainer::*)(size_t))&TContainer::resize)
            ;
            stl_from_python();
        }
        else if constexpr(std::is_array_v<TContainer>){
            if constexpr(is_vec_or_array_v<value_type>) stl_container_converter<value_type>::register_converter();
            stl_from_python();
            auto a = py::class_<TContainer>(TypeReflection<TContainer>().c_str()).def(py::init<>())
                .def("__iter__", py::iterator<TContainer>())
                .def("__repr__", (std::string (*)(const TContainer&))&to_string<TContainer>)
                .def("__len__", &TContainer::size)
            ;
            if constexpr(!is_real_or_complex_v<value_type>){
                a.def("__getitem__", (value_type& (TContainer::*)(size_t))&TContainer::at, py::return_value_policy<py::reference_existing_object>());
            }
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

//== tuple register
template<class ... Args> struct tuple_unpacker 
{
    static py::tuple unpack( const std::tuple<Args...>& cpp_tuple) {
        return std::apply([](const auto&... args) {
            return py::make_tuple(args...);
        }, cpp_tuple);
    }
};
template<size_t Index, class... Args> struct tuple_packer 
{
    static void pack(std::tuple<Args...>& cpp_tuple, const py::tuple& py_tuple) {
        if constexpr (Index < sizeof...(Args)) {
            using ElementType = typename std::tuple_element<Index, std::tuple<Args...>>::type;
            std::get<Index>(cpp_tuple) = py::extract<ElementType>(py_tuple[Index]);
            tuple_packer<Index + 1, Args...>::pack(cpp_tuple, py_tuple);
        }
    }
};
template<class... Args> struct tuple_converter 
{
    static constexpr bool is_registrable() {
        return true;
    }

    // C++ -> Python
    static PyObject* convert(const std::tuple<Args...>& cpp_tuple) {
        py::tuple py_tuple = tuple_unpacker<Args...>::unpack(cpp_tuple);
        return py::incref(py_tuple.ptr());
    }

    // Python -> C++ 转换
    static void* convertible(PyObject* obj) {
        if (!PyTuple_Check(obj)) return nullptr;
        
        py::tuple py_tuple(py::handle<>(py::borrowed(obj)));
        if (len(py_tuple) != sizeof...(Args)) return nullptr;
        
        return obj;
    }

    static void construct(PyObject* obj, py::converter::rvalue_from_python_stage1_data* data) {
        void* storage = ((py::converter::rvalue_from_python_storage<std::tuple<Args...>>*)data)->storage.bytes;
        py::tuple py_tuple(py::handle<>(py::borrowed(obj)));
        
        new (storage) std::tuple<Args...>();
        std::tuple<Args...>* cpp_tuple = static_cast<std::tuple<Args...>*>(storage);
        tuple_packer<0, Args...>::pack(*cpp_tuple, py_tuple);
        
        data->convertible = storage;
    }
};
template<class... Args> inline void register_tuple_converter() 
{
    using TContainer = std::tuple<Args...>;
    const py::converter::registration* regVectorValue = py::converter::registry::query(py::type_id<TContainer>());
    if (!(nullptr == regVectorValue || nullptr == (*regVectorValue).m_to_python)) {
        error_unclassified::out(TypeReflection<TContainer>(), "'s to python converter has alreadly registed before." );
        return;
    }
    boost::python::to_python_converter<TContainer, tuple_converter<Args...>>();
    py::converter::registry::push_back(
        &tuple_converter<Args...>::convertible,
        &tuple_converter<Args...>::construct,
        py::type_id<TContainer>()
    );
}
