# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


@cocotb.test()
async def test_register_file(dut):
    dut._log.info("Start register file test")

    # Set the clock period to 1000 us (1 KHz)
    clock = Clock(dut.clk, 1000, units="us")
    cocotb.start_soon(clock.start())

    # Reset the design
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)  # Ensure enough cycles during reset
    dut.rst_n.value = 1  # Release reset
    await ClockCycles(dut.clk, 10)

    # Test write and read operations
    dut._log.info("Testing write and read operations")

    # Write value to register 1
    dut.uio_in.value = 0b10000010  # IO[7]=1 (we=1), IO[6:4]=001 (write to reg 1), IO[3:0]=0b0010 (data=2)
    await ClockCycles(dut.clk, 1)  # Apply write

    # Wait additional cycles to ensure write completes
    await ClockCycles(dut.clk, 2)

    # Read back value from register 1
    dut.ui_in.value = 0b00000001  # Input[2:0]=001 (read reg 1)
    await ClockCycles(dut.clk, 2)  # Ensure read
    assert dut.uo_out.value.integer & 0xF == 2, f"Expected register 1 to contain 2, got {dut.uo_out.value.integer & 0xF}"

    # Write value to register 2
    dut.uio_in.value = 0b10000101  # IO[7]=1 (we=1), IO[6:4]=010 (write to reg 2), IO[3:0]=0b0101 (data=5)
    await ClockCycles(dut.clk, 2)  # Apply write
    await ClockCycles(dut.clk, 2)  # Wait additional cycles for write to take effect

    # Read back value from register 2
    dut.ui_in.value = 0b00000100  # Input[6:4]=010 (read reg 2)
    # await ClockCycles(dut.clk, 0)  # Ensure read
    assert (dut.uo_out.value.integer >> 4) & 0xF == 5, f"Expected register 2 to contain 5, got {(dut.uo_out.value.integer >> 4) & 0xF}"

    # Write and read to ensure register 0 remains 0 (RISC-V convention)
    dut.uio_in.value = 0b10000011  # IO[7]=1 (we=1), IO[6:4]=000 (write to reg 0), IO[3:0]=0b0011 (attempt to write 3)
    await ClockCycles(dut.clk, 1)
    await ClockCycles(dut.clk, 2)  # Wait for write to complete

    # Check that register 0 is still zero
    dut.ui_in.value = 0b00000000  # Input[2:0]=000 (read reg 0)
    # await ClockCycles(dut.clk, 0)
    assert dut.uo_out.value.integer & 0xF == 0, f"Expected register 0 to remain 0, got {dut.uo_out.value.integer & 0xF}"

    dut._log.info("Register file test completed successfully")