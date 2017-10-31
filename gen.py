from random import randint, choice, normalvariate
from string import ascii_lowercase
from itertools import combinations_with_replacement
import subprocess
from os import remove
from sys import argv, setrecursionlimit
from math import ceil
from time import sleep


C_COMPILER = 'cc'


class EInt:
    def __init__(self, n):
        self.n = n
    
    def __str__(self):
        return str(self.n)

    def __c_str__(self):
        return self.__str__()


class EVar:
    def __init__(self, x):
        self.x = x

    def __str__(self):
        return self.x

    def __c_str__(self):
        return self.__str__()


class EBinOp:
    def __init__(self, op, e1, e2):
        self.op = op
        self.e1 = e1
        self.e2 = e2

    def __str__(self):
        fmt1 = '(%s)' if isinstance(self.e1, EBinOp) else '%s'
        fmt2 = '(%s)' if isinstance(self.e2, EBinOp) else '%s'
        return (fmt1 + ' %s ' + fmt2) % (self.e1, self.op, self.e2)

    def __c_str__(self):
        return self.__str__()


class SAss:
    def __init__(self, x, e):
        self.x = x
        self.e = e

    def __str__(self):
        return '%s = %s' % (self.x, self.e)

    def __c_str__(self):
        return self.__str__()


class SAllAss(SAss):
    def __c_str__(self):
        return 'int32_t %s = %s' % (self.x, self.e)


class SExp:
    def __init__(self, e):
        self.e = e

    def __str__(self):
        return self.e.__str__()

    def __c_str__(self):
        return 'printf("%%d\\n", %s);' % self.e


class Prog:
    def __init__(self, stmts):
        self.stmts = stmts

    def write_c(self, f):
        f.write(b'#include <stdio.h>\n')
        f.write(b'#include <stdint.h>\n')
        f.write(b'int main() {\n')
        for s in self.stmts:
            f.write(s.__c_str__().encode('utf-8'))
            f.write(b';\n')
        f.write(b'return 0;')
        f.write(b'}')

    def write_instant(self, f):
        for s in self.stmts:
            f.write(s.__str__().encode('utf-8'))
            f.write(b';\n')

def genEInt():
    # return EInt(abs(ceil(normalvariate(5, 40))))
    return EInt(randint(0, 2**31-1))


def genEVar(env):
    return EVar(choice(env))


def genEBinOp(env):
    op = choice(['+', '-', '/', '*'])
    return EBinOp(op, genExp(env), genExp(env))


def genExp(env):
    if env is None or len(env) is 0:
        r = choice([0,1])
    else:
        r = choice([0,1,2])

    if r is 0:
        return genEInt()
    elif r is 1:
        return genEBinOp(env)
    elif r is 2:
        return genEVar(env)


def genStmt(env):
    if env is None or len(env) is 0:
        r = choice([0,1,2])
    else:
        r = choice([0,1,2,3])

    vs, gen = env
    e = genExp(vs)

    if r is 0:
        x = gen.__next__()
        vs.append(x)
        return (env, SAllAss(x, e))
    elif r is 4:
        return (env, SAss(choice(vs), e))
    else:
        return (env, SExp(e))


def genProg(n):
    # l = randint(1, n)
    l = ceil(normalvariate(7.0/8 * n, 1.0/7 * n))
    p = []
    e = emptyEnv()
    for _ in range(l):
        e, p2 = genStmt(e)
        p.append(p2)

    return Prog(p)


def nextVar():
    i = 1
    while True:
        for p in combinations_with_replacement(ascii_lowercase, i):
            yield ''.join(p)
        i += 1

emptyEnv = lambda: ([], nextVar())


if __name__ == '__main__':
    if len(argv) != 4:
        print('Usage: %s path examples_number max_example_length' % argv[0])
        exit(1)

    maxn = int(argv[2])
    maxl = int(argv[3])
    path = argv[1]
    prefix = 'ex'

    setrecursionlimit(50000)
    i = 0;

    while i < maxn:
        src_inst = ('%s/' + prefix + '%03d.ins') % (path, i)
        src_c = ('%s/' + prefix + '%03d.c') % (path, i)
        out = ('%s/' + prefix + '%03d.output') % (path, i)
        try:
            prog = genProg(maxl)
        except RecursionError:
            continue

        with open(src_c, 'wb+') as f:
            prog.write_c(f)
        with open(src_inst, 'wb+') as f:
            prog.write_instant(f)
        
        # no overflows
        # p = subprocess.run([C_COMPILER, '-Werror=div-by-zero', '-Werror=overflow', src_c], stderr=subprocess.DEVNULL)
        p = subprocess.run([C_COMPILER, '-Werror=div-by-zero', src_c], stderr=subprocess.DEVNULL)
        if p.returncode is not 0:
            sleep(0.01)
            remove(src_c)
            remove(src_inst)
            continue

        f = open(out, 'wb+')
        p = subprocess.run(['./a.out'], stdout=f)
        if p.returncode is not 0:
            f.close()
            sleep(0.01)
            remove(src_c)
            remove(src_inst)
            remove(out)
        else:
            i += 1
            f.close()
    
    remove('./a.out')
