#pragma once

#include <cstddef>

namespace uniqc {

    /* Global multithreading control for the simulator kernels.
     *
     * The switch defaults to OFF and the thread count to 1, so a fresh
     * process behaves exactly like the historical serial implementation.
     * Both settings are process-wide: they affect every simulator instance
     * and are read at the start of each parallel_for decision. */

    void set_parallel_enabled(bool enabled);
    bool is_parallel_enabled();

    /* Throws InvalidArgument for n == 0; values above the hardware
     * concurrency are clamped. get_num_threads() returns the effective
     * count. */
    void set_num_threads(size_t n);
    size_t get_num_threads();

    /* Minimum loop length before parallel_for considers spawning threads
     * (16384 elements = 128 KiB of complex<double>). */
    constexpr size_t MIN_PARALLEL_WORK = size_t(1) << 14;

    /* Effective worker count for a loop of `len` iterations: the configured
     * thread count when parallelism is enabled and the loop is large
     * enough, otherwise 1. */
    size_t parallel_worker_count(size_t len);

    /* Same, for loops whose iterations each do `work_per_iter` units of
     * work (e.g. a density-matrix row loop carries an O(N) inner loop, so
     * its len alone underestimates the work). The thread count is also
     * capped at `len` so every worker gets at least one iteration. */
    size_t parallel_worker_count(size_t len, size_t work_per_iter);
}
