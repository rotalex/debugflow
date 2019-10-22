from pprint import pprint
from typing import *

import subprocess
import parser
import ast
import astunparse
import os
import fcntl
import threading
import ptyprocess
import select

def indentLvl(codeLine):
	tabCnt = 0
	spcCnt = 0

	for ch in codeLine:
		tabCnt += (ch == '\t')
		spcCnt += (ch == ' ')

	if tabCnt:
		return tabCnt

	if spcCnt:
		return spcCnt // 4

def stripIndent(codeLine, indents=1):
	# consider tab = 4 space
	if codeLine[0] == '\t':
		return codeLine[indents:] # indents tabs
	if codeLine[0] == ' ':
		return codeLine[indents * 4:]
	return codeLine

def runTest(tree, lines, interpreter, source = ""):
	pprint(list(enumerate(lines)))
	for node in ast.walk(tree):
		if not isinstance(node, ast.Module) and \
			not isinstance(node, ast.FunctionDef):
			continue

		if isinstance(node, ast.FunctionDef):
			comments = lines[node.lineno - 2][4:]
			values = eval(comments)
			for idx, funcArg in enumerate(node.args.args):
				code = f"{funcArg.arg} = {values[idx]}"
				interpreter.interpret(code)
				interpreter.getoutput()

		for stmt in node.body:
			code = astunparse.unparse(stmt)
			interpreter.interpret(code)
			if isinstance(stmt, ast.Assign):
				for subExpr in ast.walk(stmt.value):
					if subExpr is stmt.value:
						continue
					if isinstance(subExpr, ast.expr):
						expr_val = astunparse.unparse(subExpr).strip()
						interpreter.interpret(expr_val)
						print(f"#{expr_val} = {interpreter.getoutput()}")

				#for subExpr in stmt
				stored = "%s" % stmt.targets[0].id
				interpreter.interpret(stored)
				print(f"#{stored} = {interpreter.getoutput()}")


def runTests(interpreter):
	with open("scenarios.py", "r") as f:
		allText = f.read().split("#$#$")
		for test in allText:
			lines = test.split("\n")
			tree = ast.parse(test)
			runTest(tree, lines, interpreter, test)


class Interpreter:
	def __init__(self):
		self.proc = ptyprocess.PtyProcessUnicode.spawn(['python'])
		self.proc.setecho(False)

	def __canread(self, fd, timeout=1):
		return fd in select.select([fd], [], [], timeout)[0]

	def interpret(self, instruction):
		self.proc.write(instruction + "\n")

	def getoutput(self):
		resp = ""
		while self.__canread(self.proc.fd):
			resp += self.proc.read()

		# Cleaning out the >>> prompt from the interpreter
		prompt = ">>>"
		while resp.strip(" ").startswith(prompt):
			resp = resp[len(prompt):].strip()
		while resp.strip(" ").endswith(prompt):
			resp = resp[:-len(prompt)].strip()
		return resp

pyInterpreter = Interpreter()
pyInterpreter.getoutput() # get out the python notice

#while True:
#	print(pyInterpreter.getOutput())
#	pyInterpreter.interpret(input())


if __name__ == "__main__":
	runTests(pyInterpreter)
