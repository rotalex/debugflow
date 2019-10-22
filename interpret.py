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


class Interpreter:
	"""
	Interpreter is an abstraction layer over a process of python in which we run
	and evaluate all of the instructions/statements. We interact with it by
	sending to the process the instruction to run and by getting the output.
	"""
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
		prompt = ">"
		while resp.strip(" ").startswith(prompt):
			resp = resp[len(prompt):].strip()
		while resp.strip(" ").endswith(prompt):
			resp = resp[:-len(prompt)].strip()
		return resp

class DebugFlow:
	"""
		DebugFlow contain the logic for ast traversal, detecting what object to
		render and what subexpression to display.
	"""
	def __init__(self, interp = None):
		self.interpreter = interp if interp else Interpreter()
		self.interpreter.getoutput() # get out the python notice

	def flow(self, code):
		# For now we take the whole code since we might get invalid code so we
		# could try to discard lines to have correct code.
		print(code)
		tree = ast.parse(code)
		for node in ast.walk(tree):
			if not isinstance(node, ast.Module) and \
				not isinstance(node, ast.FunctionDef):
				continue

			if isinstance(node, ast.FunctionDef):
				comments = ast.get_docstring(node)
				values = eval(comments)
				for idx, funcArg in enumerate(node.args.args):
					code = f"{funcArg.arg} = {values[idx]}"
					self.interpreter.interpret(code)
					self.interpreter.getoutput()

			for stmt in node.body:
				code = astunparse.unparse(stmt)
				self.interpreter.interpret(code)
				self.interpreter.getoutput()

				if isinstance(stmt, ast.Assign):
					for subExpr in ast.walk(stmt.value):
						if subExpr is stmt.value:
							continue
						if isinstance(subExpr, ast.expr):
							expr = astunparse.unparse(subExpr).strip()
							self.interpreter.interpret(expr)
							print(f"#{expr} = {self.interpreter.getoutput()}")
					stored = "%s" % stmt.targets[0].id
					self.interpreter.interpret(stored)
					print(f"#{stored} = {self.interpreter.getoutput()}")



def runTests(debug):
	with open("scenarios.py", "r") as f:
		allText = f.read().split("#$#$")
		for test in allText[2:]:
			debug.flow(test)

if __name__ == "__main__":
	debug = DebugFlow()
	runTests(debug)
