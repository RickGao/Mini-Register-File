# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles
from cocotb.triggers import Timer





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

    # await ClockCycles(dut.clk, 1)
    await Timer(10, units="us")

    # Extract read values from output
    read_data1 = dut.uo_out.value.integer & 0xF
    read_data2 = (dut.uo_out.value.integer >> 4) & 0xF

    dut._log.info(f"Output after read from register {reg_addr1}: Expected {expected_data1}, Got {read_data1}")
    dut._log.info(f"Output after read from register {reg_addr2}: Expected {expected_data2}, Got {read_data2}\n")

    assert read_data1 == expected_data1, f"Expected register {reg_addr1} to contain {expected_data1}, got {read_data1}"
    assert read_data2 == expected_data2, f"Expected register {reg_addr2} to contain {expected_data2}, got {read_data2}"

    # await ClockCycles(dut.clk, 1)


@cocotb.test()
async def test_register_file(dut):
    # Set up clock
    clock = Clock(dut.clk, 100, units="us")  # 10 KHz clock
    cocotb.start_soon(clock.start())

    # Reset the design
    dut._log.info("Resetting the design\n")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1


    dut._log.info("Test case 1: Write value 2 to register 1 and value 5 to register 2, then read both back\n")

    await write_register(dut, reg_addr=0b001, write_data=0b0010)
    await write_register(dut, reg_addr=0b010, write_data=0b0101)
    await read_register(dut, reg_addr1=0b001, expected_data1=0b0010, reg_addr2=0b010, expected_data2=0b0101)


    dut._log.info("Write to register 0 and confirm it remains zero (RISC-V convention), and check register 1 still has 2\n")

    await write_register(dut, reg_addr=0b000, write_data=0b0011)
    await read_register(dut, reg_addr1=0b000, expected_data1=0b0000, reg_addr2=0b001, expected_data2=0b0010)


    dut._log.info("Test Case 3: Write and read all registers to check boundary values\n")

    for reg_addr in range(8):
        await write_register(dut, reg_addr=reg_addr, write_data=reg_addr)
    for reg_addr in range(0, 8, 2):  # Read two registers at a time
        await read_register(
            dut,
            reg_addr1=reg_addr,
            expected_data1=reg_addr,
            reg_addr2=reg_addr + 1,
            expected_data2=reg_addr + 1
        )


    dut._log.info("Test case 4: Overwrite a register and check the last write persists\n")

    await write_register(dut, reg_addr=0b010, write_data=0b0111)  # Write 7 to register 2
    await write_register(dut, reg_addr=0b011, write_data=0b1001)  # Write 9 to register 3
    await write_register(dut, reg_addr=0b011, write_data=0b0100)  # Overwrite with 4
    await read_register(dut, reg_addr1=0b011, expected_data1=0b0100, reg_addr2=0b010, expected_data2=0b0111)

    dut._log.info("Test case 5: Write to multiple registers, reset, and verify all registers are cleared\n")
    
    await write_register(dut, reg_addr=0b001, write_data=0b1111)  # Write 15 to register 1
    await write_register(dut, reg_addr=0b010, write_data=0b1110)  # Write 14 to register 2
    dut.rst_n.value = 0  # Apply reset
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1  # Release reset
    await read_register(dut, reg_addr1=0b001, expected_data1=0b0000, reg_addr2=0b010, expected_data2=0b0000)

    dut._log.info("All test passed!")