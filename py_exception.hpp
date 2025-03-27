#pragma once
#include "py_helper.hpp"
#include <exception>
#include <type_traist_notebook/type_traist.hpp>
inline PyObject* createPyExceptionClass(const char* name, PyObject* baseTypeObj = PyExc_RuntimeError)
{
    const std::string scopeName = py::extract<std::string>(py::scope().attr("__name__"));
    const std::string qualifiedName0 = scopeName + "." + name;
    PyObject* typeObj = PyErr_NewException(qualifiedName0.c_str(), baseTypeObj, nullptr);
    py::scope().attr(name) = py::handle<>(py::borrowed(typeObj));
    return typeObj;
}

template <class E, class... Policies,class... Args> inline  py::class_<E, Policies...> exception_converters(const char* name, Args&&... args) 
{
    py::class_<E, Policies...> cls(name, std::forward<Args>(args)...);
    static PyObject* pythonExceptionType = createPyExceptionClass(name);
    py::register_exception_translator<E>([ptr=pythonExceptionType](E const& e){
        py::object exc_t(py::handle<>(py::borrowed(ptr)));
        exc_t.attr("cause") = py::object(e); 
        exc_t.attr("what") = py::object(e.what());
        PyErr_SetString(ptr, e.what());
        PyErr_SetObject(ptr, py::object(e).ptr());
    });

    cls.def("__str__", &E::what);
    return cls;
}
template<class T, class ...TRest> inline void init_exception_converters() 
{
    std::string name = TypeReflection<T>();
    exception_converters<T>(name.c_str(), py::init<std::string>());
    if constexpr (sizeof...(TRest)) {
        init_exception_converters<TRest...>();
    }
}
