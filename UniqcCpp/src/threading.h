#pragma once

#include <algorithm>
#include <cstddef>
#include <thread>
#include <vector>

#include "threading_control.h"

namespace uniqc {

    /* Chunked parallel execution over [begin, end).
     *
     * f(chunk_idx, chunk_begin, chunk_end) is called once per contiguous
     * chunk covering the range. chunk_idx < parallel_worker_count(len) and
     * identifies the slot for per-chunk partial results (reductions).
     * f must not throw (no kernel loop body throws).
     *
     * Chunks are contiguous (not strided) so amplitude pairs stay inside
     * one chunk and cache lines are not shared between threads. */
    template <class F>
    void parallel_chunks(size_t begin, size_t end, size_t work_per_iter, F&& f)
    {
        if (begin >= end)
            return;

        const size_t len = end - begin;
        const size_t nchunks = parallel_worker_count(len, work_per_iter);
        if (nchunks <= 1)
        {
            f(0, begin, end);
            return;
        }

        const size_t chunk = (len + nchunks - 1) / nchunks;
        std::vector<std::thread> workers;
        workers.reserve(nchunks - 1);
        for (size_t t = 1; t < nchunks; ++t)
        {
            const size_t b = begin + t * chunk;
            if (b >= end)
                break;
            const size_t e = std::min(b + chunk, end);
            workers.emplace_back([&f, t, b, e]() { f(t, b, e); });
        }
        f(0, begin, std::min(begin + chunk, end));
        for (auto& w : workers)
            w.join();
    }

    /* Elementwise variant: f(chunk_begin, chunk_end) over the union of the
     * chunks (chunk index dropped). */
    template <class F>
    void parallel_for(size_t begin, size_t end, F&& f)
    {
        parallel_chunks(begin, end, size_t(1),
            [&f](size_t, size_t b, size_t e) { f(b, e); });
    }

    /* Same, with a per-iteration work hint for loops whose iterations are
     * heavy (see parallel_worker_count(len, work_per_iter)). */
    template <class F>
    void parallel_for(size_t begin, size_t end, size_t work_per_iter, F&& f)
    {
        parallel_chunks(begin, end, work_per_iter,
            [&f](size_t, size_t b, size_t e) { f(b, e); });
    }

    /* Chunked variant without a work hint (one work unit per iteration). */
    template <class F>
    void parallel_chunks(size_t begin, size_t end, F&& f)
    {
        parallel_chunks(begin, end, size_t(1), f);
    }

} // namespace uniqc
