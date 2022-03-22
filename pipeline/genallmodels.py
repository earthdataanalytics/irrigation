#!/usr/bin/env python
# coding: utf-8


import argparse
import sys
import os
import glob

# custom libraries
import ET_Driver as driver

def run():

    files = glob.glob('../../runs/')

    for file in files:
        print(file)



if __name__ == "__main__":
    run()
