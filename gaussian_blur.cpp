#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <limits>
#include <new>
#include <stdexcept>
#include <vector>

namespace {

unsigned char round_byte(double value) {
    value = std::max(0.0, std::min(255.0, value));
    double lower = std::floor(value);
    double fraction = value - lower;
    int result = static_cast<int>(lower);
    if (fraction > 0.5 || (fraction == 0.5 && result % 2 != 0)) {
        ++result;
    }
    return static_cast<unsigned char>(result);
}

Py_ssize_t clamped_index(Py_ssize_t position, Py_ssize_t extent,
                         Py_ssize_t kernel_index, Py_ssize_t radius) {
    if (kernel_index < radius) {
        Py_ssize_t distance = radius - kernel_index;
        return distance > position ? 0 : position - distance;
    }
    Py_ssize_t distance = kernel_index - radius;
    return distance >= extent - position ? extent - 1 : position + distance;
}

PyObject* gaussian_blur(PyObject*, PyObject* args, PyObject* kwargs) {
    PyObject* input;
    Py_ssize_t width, height;
    double sigma;
    static const char* names[] = {"rgb", "width", "height", "sigma", nullptr};
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "Onnd:gaussian_blur",
                                     const_cast<char**>(names), &input, &width, &height, &sigma)) {
        return nullptr;
    }
    if (!PyBytes_Check(input)) {
        PyErr_SetString(PyExc_TypeError, "rgb must be bytes");
        return nullptr;
    }
    if (width <= 0 || height <= 0) {
        PyErr_SetString(PyExc_ValueError, "width and height must be positive");
        return nullptr;
    }
    if (!std::isfinite(sigma) || sigma <= 0.0) {
        PyErr_SetString(PyExc_ValueError, "sigma must be a positive finite number");
        return nullptr;
    }
    const Py_ssize_t limit = PY_SSIZE_T_MAX;
    if (width > limit / 3 || height > limit / (width * 3)) {
        PyErr_SetString(PyExc_OverflowError, "image dimensions are too large");
        return nullptr;
    }
    Py_ssize_t size = width * height * 3;
    if (PyBytes_GET_SIZE(input) != size) {
        PyErr_SetString(PyExc_ValueError, "rgb length must equal width * height * 3");
        return nullptr;
    }
    double radius_value = std::ceil(3.0 * sigma);
    if (!std::isfinite(radius_value) || radius_value >= static_cast<double>(limit / 2)) {
        PyErr_SetString(PyExc_OverflowError, "sigma produces an excessively large kernel");
        return nullptr;
    }
    Py_ssize_t radius = std::max<Py_ssize_t>(1, static_cast<Py_ssize_t>(radius_value));
    Py_ssize_t kernel_size = radius * 2 + 1;

    try {
        std::vector<double> kernel(static_cast<size_t>(kernel_size));
        double total = 0.0;
        double denominator = 2.0 * (sigma * sigma);
        for (Py_ssize_t k = 0; k < kernel_size; ++k) {
            double offset = static_cast<double>(k - radius);
            double weight = denominator == 0.0 ? (offset == 0.0 ? 1.0 : 0.0)
                                               : std::exp(-(offset * offset) / denominator);
            kernel[static_cast<size_t>(k)] = weight;
            total += weight;
        }
        for (double& weight : kernel) {
            weight /= total;
        }
        std::vector<unsigned char> horizontal(static_cast<size_t>(size));
        PyObject* output = PyBytes_FromStringAndSize(nullptr, size);
        if (!output) {
            return nullptr;
        }
        const auto* source = reinterpret_cast<const unsigned char*>(PyBytes_AS_STRING(input));
        auto* destination = reinterpret_cast<unsigned char*>(PyBytes_AS_STRING(output));
        for (int pass = 0; pass < 2; ++pass) {
            const unsigned char* src = pass == 0 ? source : horizontal.data();
            unsigned char* dst = pass == 0 ? horizontal.data() : destination;
            for (Py_ssize_t y = 0; y < height; ++y) {
                for (Py_ssize_t x = 0; x < width; ++x) {
                    double sums[3] = {0.0, 0.0, 0.0};
                    for (Py_ssize_t k = 0; k < kernel_size; ++k) {
                        Py_ssize_t px = pass == 0 ? clamped_index(x, width, k, radius) : x;
                        Py_ssize_t py = pass == 1 ? clamped_index(y, height, k, radius) : y;
                        Py_ssize_t index = (py * width + px) * 3;
                        for (int c = 0; c < 3; ++c) {
                            volatile double product = src[index + c] * kernel[static_cast<size_t>(k)];
                            sums[c] += product;
                        }
                    }
                    Py_ssize_t index = (y * width + x) * 3;
                    for (int c = 0; c < 3; ++c) {
                        dst[index + c] = round_byte(sums[c]);
                    }
                }
            }
        }
        return output;
    } catch (const std::bad_alloc&) {
        return PyErr_NoMemory();
    } catch (const std::length_error&) {
        PyErr_SetString(PyExc_OverflowError, "image or kernel is too large");
        return nullptr;
    } catch (...) {
        PyErr_SetString(PyExc_RuntimeError, "Gaussian blur failed");
        return nullptr;
    }
}

PyMethodDef methods[] = {
    {"gaussian_blur", reinterpret_cast<PyCFunction>(gaussian_blur), METH_VARARGS | METH_KEYWORDS,
     "Blur packed RGB bytes using a separable Gaussian kernel."},
    {nullptr, nullptr, 0, nullptr}
};

PyModuleDef module = {PyModuleDef_HEAD_INIT, "gaussian_blur_cpp", nullptr, -1, methods};

}  // namespace

PyMODINIT_FUNC PyInit_gaussian_blur_cpp() {
    return PyModule_Create(&module);
}