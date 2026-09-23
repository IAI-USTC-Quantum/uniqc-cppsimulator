#include "threading_control.h"

#include <algorithm>
#include <atomic>
#include <thread>

#include "errors.h"

namespace uniqc {

    namespace
    {
        std::atomic<bool> g_parallel_enabled{ false };
        std::atomic<size_t> g_num_threads{ 1 };

        size_t hardware_concurrency_clamped()
        {
            const unsigned int hw = std::thread::hardware_concurrency();
            return hw == 0 ? 1 : static_cast<size_t>(hw);
        }
    }

    void set_parallel_enabled(bool enabled)
    {
        g_parallel_enabled.store(enabled, std::memory_order_relaxed);
    }

    bool is_parallel_enabled()
    {
        return g_parallel_enabled.load(std::memory_order_relaxed);
    }

    void set_num_threads(size_t n)
    {
        if (n == 0)
            ThrowInvalidArgument("Thread count must be >= 1.");

        n = std::min(n, hardware_concurrency_clamped());
        g_num_threads.store(n, std::memory_order_relaxed);
    }

    size_t get_num_threads()
    {
        return g_num_threads.load(std::memory_order_relaxed);
    }

    size_t parallel_worker_count(size_t len)
    {
        return parallel_worker_count(len, 1);
    }

    size_t parallel_worker_count(size_t len, size_t work_per_iter)
    {
        if (!is_parallel_enabled() || len == 0)
            return 1;

        const size_t total_work = len * work_per_iter;
        if (total_work < MIN_PARALLEL_WORK)
            return 1;

        const size_t by_work =
            (total_work + MIN_PARALLEL_WORK / 2 - 1) / (MIN_PARALLEL_WORK / 2);
        return std::min(std::min(get_num_threads(), by_work), len);
    }
}
