# CLOB

## Description
Implementation of a Central Limit Order Book with support for two types of orders: Regular Limit Orders and [Iceberg Orders](https://www.investopedia.com/terms/i/icebergorder.asp)
The Order Books are modelled with Heaps, and matches are evaluated as the orders arrive.

This program receives order info from standard input, and assumes the input will be correct and coherent.

## Installation
Only Python is required, as there are no external libraries used. This was developed using python 3.8.10.

## Usage
After cloning the repo, and using one of the example files, an example run would be:

`python clob_main.py < test2.txt`

