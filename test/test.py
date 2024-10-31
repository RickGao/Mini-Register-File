# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles




async def write_register(dut, reg_addr, write_data):
    """Writes a value to a specific register."""
    we = 1  # Write enable
    dut.ui_in.value = 0b00000000  # Clearing ui_in for write operation
    dut.uio_in.value = (we << 7) | (reg_addr << 4) | write_data  # Setting we, reg_addr, and write_data

    dut._log.info(f"Writing to register {reg_addr}: write_enable={we}, write_data={write_data}")
    dut._log.info(f"Signals: ui_in={dut.ui_in.value}, uio_in={dut.uio_in.value}")
    await ClockCycles(dut.clk, 1)


async def read_register(dut, reg_addr1, expected_data1, reg_addr2, expected_data2):
    """Reads values from two registers and compares them to the expected data."""
    dut.ui_in.value = (reg_addr2 << 4) | reg_addr1  # Set read_reg1 to reg_addr1 and read_reg2 to reg_addr2
    dut.uio_in.value = 0b00000000  # Set uio_in to 0 for read operation

    dut._log.info(f"Reading from registers {reg_addr1} and {reg_addr2}")
    dut._log.info(f"Signals: ui_in={dut.ui_in.value}, uio_in={dut.uio_in.value}")

    await ClockCycles(dut.clk, 1)

    # Extract read values from output
    read_data1 = dut.uo_out.value.integer & 0xF
    read_data2 = (dut.uo_out.value.integer >> 4) & 0xF

    dut._log.info(f"Output after read from register {reg_addr1}: Expected {expected_data1}, Got {read_data1}")
    dut._log.info(f"Output after read from register {reg_addr2}: Expected {expected_data2}, Got {read_data2}")

    assert read_data1 == expected_data1, f"Expected register {reg_addr1} to contain {expected_data1}, got {read_data1}"
    assert read_data2 == expected_data2, f"Expected register {reg_addr2} to contain {expected_data2}, got {read_data2}"


@cocotb.test()
async def test_register_file(dut):
    dut._log.info("Start register file test")

    # Set the clock period to 1000 us (1 KHz)
    clock = Clock(dut.clk, 1000, units="us")
    cocotb.start_soon(clock.start())

    # Reset the design
    dut._log.info("Resetting the design")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)  # Ensure enough cycles during reset
    dut.rst_n.value = 1  # Release reset
    await ClockCycles(dut.clk, 10)

    # Test case: Write value 2 to register 1 and read it back
    await write_register(dut, reg_addr=0b001, write_data=0b0010)
    await read_register(dut, reg_addr=0b001, expected_data=0b0010, read_port=1)

    # Test case: Write value 5 to register 2 and read it back
    await write_register(dut, reg_addr=0b010, write_data=0b0101)
    await read_register(dut, reg_addr=0b010, expected_data=0b0101, read_port=2)

    # Test case: Write to register 0 and confirm it remains zero (RISC-V convention)
    await write_register(dut, reg_addr=0b000, write_data=0b0011)
    await read_register(dut, reg_addr=0b000, expected_data=0b0000, read_port=1)

    dut._log.info("Register file test completed successfully!")