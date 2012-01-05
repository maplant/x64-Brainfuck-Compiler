#!/usr/bin/env python
"""
bf.py
A very simple, slightly optimized brainfuck compiler for x64.
Reads from standard input and writes to standard output.

By default, the stack size is set to 60000, which is twice the
size used by the original implementation. This is because, unlike
in the original implementation, the data pointer starts in the
middle, rather than the beginning.

Data is stored in the stack and initialized to 0 at runtime.

Register assignments:
%rdi          - the data pointer.
%rsp and %rbp - stack and base pointers respectively, as per usual.

Commands for assembling and linking output (may vary):
as --64 -o prog.o prog.s
ld -o prog prog.o

Issues:
I suck at assembler of all kinds, so this is all terrible. Joy!

(C) 2011 Matthew Plant
"""

import sys

stack_size = 60000
header = (
    """\
.equ SYS_READ, 0
.equ SYS_WRITE, 1
.equ SYS_EXIT, 60
.equ STDIN, 0
.equ STDOUT, 1
.equ STDERR, 2

.section .text
.globl _start
_start:
        movq    %%rsp, %%rax
        subq    $%d, %%rsp        
_init_stack:
        movb    $0, (%%rax)
        decq    %%rax
        cmpq    %%rax, %%rsp
        jge     _init_stack
        movq    %%rsp, %%rdi
        addq    $%d, %%rdi
_begin_compilation:\
""" % (stack_size, int (stack_size / 2) - 1))
footer = (
    """\
        movq    $SYS_EXIT, %rax
        syscall
""")


# Get the input up to the EOF. 
input_str = ''
while True:
    try:
        input_str += raw_input ()
    except:
        break

if input_str == '':
    sys.stderr.write ('Error: no input to compile, exiting')
    quit ()
    
# Compile the code.
output = []
lbls = {}
bc = 0
pmov = 0
pch = 0
code_slice = ''

for c in input_str:
    if pmov != 0 and c != '>' and c != '<':
        output.append ("# " + code_slice)
        code_slice = ''
        if pmov > 0:
            output.append ("        addq    $%d, %%rdi" % pmov)
        else:
            output.append ("        subq    $%d, %%rdi" % abs (pmov))
        pmov = 0
    elif pch != 0 and c != '+' and c != '-':
        output.append ("# " + code_slice)
        code_slice = ''
        if pch > 0:
            output.append ("        addb    $%d, (%%rdi)" % pch)
        else:
            output.append ("        subb    $%d, (%%rdi)" % abs (pch))
        pch = 0
    
    if c == '>':
        code_slice += '>'
        pmov += 1
    elif c == '<':
        code_slice += '<'
        pmov -= 1
    elif c == '+':
        code_slice += '+'
        pch += 1
    elif c == '-':
        code_slice += '-'
        pch -= 1
    elif c == '.':
        output.append ("# .")
        output.append ("        pushq   %rdi")
        output.append ("        movq    %rdi, %rsi")
        output.append ("        movq    $1, %rdx")
        output.append ("        movq    $STDOUT, %rdi")  
        output.append ("        movq    $SYS_WRITE, %rax")
        output.append ("        syscall")
        output.append ("        popq    %rdi")
    elif c == ',':
        output.append ("# ,")
        output.append ("        pushq   %rdi")
        output.append ("        movq    %rdi, %rsi")
        output.append ("        movq    $1, %rdx")
        output.append ("        movq    $STDIN, %rdi")
        output.append ("        movq    $SYS_READ, %rax")
        output.append ("        syscall")
        output.append ("        popq    %rdi")
    elif c == '[':
        code_slice = ' ';
        lbl = 'loop'
        if not bc in lbls:
            lbls[bc] = 0
        else:
            lbls[bc] += 1
        for i in range (bc + 1):
            code_slice += ' '
            lbl += "_%d" % lbls[i]
        output.append ("#%s[" % code_slice)
        output.append ("        movb    (%rdi), %al")
        output.append ("        cmpb    $0, %al")
        output.append ("        je      %s_end" % lbl)
        output.append ("%s_start:" % lbl)
        bc += 1
    elif c == ']':
        code_slice = ' ';
        bc -= 1
        if not bc in lbls:
            sys.stderr.write ('Error: mismatched brackets, exiting.')
            quit ()
        lbl = ''
        for i in range (bc + 1):
            code_slice += ' '
            lbl += "_%d" % lbls[i]
        output.append ("#%s]" % code_slice)
        output.append ("        movb    (%rdi), %al")
        output.append ("        cmpb    $0, %al")
        output.append ("        jne     loop%s_start" % lbl)
        output.append ("loop%s_end:" % lbl)
        dead = bc + 1
        while dead in lbls:
            del lbls[dead]
            dead += 1

# Print the assemblage to stdout
print header
for s in output:
    print s
print footer
