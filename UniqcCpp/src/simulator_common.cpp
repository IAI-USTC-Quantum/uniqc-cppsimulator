#include "simulator_common.h"

namespace uniqc {
    std::map<size_t, size_t> preprocess_measure_list(const std::vector<size_t>& measure_list, size_t total_qubit)
    {
        if (measure_list.size() > total_qubit)
        {
            auto errstr = fmt::format("Exceed total (total_qubit = {}, measure_list size = {})", total_qubit, measure_list.size());
            ThrowInvalidArgument(errstr);
        }

        std::map<size_t, size_t> qbit_cbit_map;
        for (size_t i = 0; i < measure_list.size(); ++i)
        {
            size_t qn = measure_list[i];
            if (qn >= total_qubit)
            {
                auto errstr = fmt::format("Exceed total (total_qubit = {}, measure_qubit = {})", total_qubit, qn);
                ThrowInvalidArgument(errstr);
            }
            if (qbit_cbit_map.find(qn) != qbit_cbit_map.end())
            {
                auto errstr = fmt::format("Duplicate measure qubit ({})", qn);
                ThrowInvalidArgument(errstr);
            }
            qbit_cbit_map.insert({ qn,i });
        }
        return qbit_cbit_map;
    }

    size_t get_state_with_qubit(size_t i, const std::map<size_t, size_t>& measure_map)
    {
        size_t ret = 0;
        for (auto&& [qidx, cidx] : measure_map)
        {
            ret += (((i >> qidx) & 1) << cidx);
        }
        return ret;
    }

    size_t make_controller_mask(const std::vector<size_t>& global_controller, size_t total_qubit)
    {
        size_t mask = 0;
        for (size_t qn : global_controller)
        {
            if (qn >= total_qubit)
            {
                auto errstr = fmt::format(
                    "Exceed total (total_qubit = {}, control_qubit = {})",
                    total_qubit, qn);
                ThrowInvalidArgument(errstr);
            }
            mask |= (1ull << qn);
        }
        return mask;
    }

    void check_qram_data_validity(
        size_t addr_size,
        size_t data_size,
        const std::vector<size_t>& data_array)
    {
        constexpr size_t size_t_bits = sizeof(size_t) * 8;
        if (addr_size >= size_t_bits || data_size > size_t_bits)
        {
            auto errstr = fmt::format(
                "QRAM address/data sizes ({}/{}) exceed the native size_t representation ({} bits).",
                addr_size, data_size, size_t_bits);
            ThrowInvalidArgument(errstr);
        }

        const size_t expected_size = size_t{ 1 } << addr_size;
        if (data_array.size() != expected_size)
        {
            auto errstr = fmt::format(
                "QRAM data array size ({}) does not match 2^addr_size ({}).",
                data_array.size(), expected_size);
            ThrowInvalidArgument(errstr);
        }

        if (data_size == size_t_bits)
            return;
        const size_t value_limit = size_t{ 1 } << data_size;
        for (size_t i = 0; i < data_array.size(); ++i)
        {
            if (data_array[i] >= value_limit)
            {
                auto errstr = fmt::format(
                    "QRAM data value ({}) at index {} does not fit data_size = {}.",
                    data_array[i], i, data_size);
                ThrowInvalidArgument(errstr);
            }
        }
    }

    void check_qram_qubit_validity(
        const std::vector<size_t>& addr_qubits,
        const std::vector<size_t>& data_qubits,
        const std::vector<size_t>& control_qubits)
    {
        std::set<size_t> addr_set;
        for (size_t qn : addr_qubits)
        {
            if (!addr_set.insert(qn).second)
            {
                auto errstr = fmt::format(
                    "QRAM address qubit ({}) is duplicated in the address qubit list.", qn);
                ThrowInvalidArgument(errstr);
            }
        }

        std::set<size_t> data_set;
        for (size_t qn : data_qubits)
        {
            if (!data_set.insert(qn).second)
            {
                auto errstr = fmt::format(
                    "QRAM data qubit ({}) is duplicated in the data qubit list.", qn);
                ThrowInvalidArgument(errstr);
            }
            if (addr_set.count(qn))
            {
                auto errstr = fmt::format(
                    "QRAM data qubit ({}) overlaps with an address qubit; "
                    "address and data qubits must be disjoint.",
                    qn);
                ThrowInvalidArgument(errstr);
            }
        }

        if (control_qubits.empty())
            return;

        std::set<size_t> target_qubits = addr_set;
        target_qubits.insert(data_set.begin(), data_set.end());

        std::set<size_t> control_set;
        for (size_t qn : control_qubits)
        {
            if (target_qubits.count(qn))
            {
                auto errstr = fmt::format(
                    "QRAM control qubit ({}) overlaps with an address/data qubit; "
                    "control qubits must be disjoint from the QRAM's addr/data qubits.",
                    qn);
                ThrowInvalidArgument(errstr);
            }
            if (!control_set.insert(qn).second)
            {
                auto errstr = fmt::format(
                    "QRAM control qubit ({}) is duplicated in the control qubit list.", qn);
                ThrowInvalidArgument(errstr);
            }
        }
    }
} // namespace uniqc
