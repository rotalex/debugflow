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
		self.seen = set()

	def traverse(self, node, insideCall=False):
		#TODO(rotaru): fix repetitive evaluation of the same name/expression
		if node in self.seen:
			return
		else:
			self.seen.add(node)

		if isinstance(node, ast.Store) or \
			isinstance(node, ast.Load) or \
			isinstance(node, ast.Num):
			return

		if isinstance(node, ast.Name):
			self.interpreter.interpret(node.id)
			print(f"#{node.id} = {self.interpreter.getoutput()}")
		elif isinstance(node, ast.Attribute):
			if insideCall:
				self.traverse(node.value)
			else:
				select_stmt = astunparse.unparse(node)
				self.interpreter.interpret(select_stmt)
				print(f"#{select_stmt} = {self.interpreter.getoutput()}")
		elif isinstance(node, ast.Assign):
			for expr in ast.walk(node.value):
				self.traverse(expr)
			code = astunparse.unparse(node)
			self.interpreter.interpret(code)
			for target in node.targets:
				stored = f"{target.id}"
				self.interpreter.interpret(stored)
				print(f"#{stored} = {self.interpreter.getoutput()}")
		elif isinstance(node, ast.For):
			code = astunparse.unparse(node)
			self.interpreter.interpret(code)
			code = "\tpass"
			self.interpreter.interpret(code)
			self.interpreter.getoutput()
			self.traverse(node.target)
			self.traverse(node.iter)
		elif isinstance(node, ast.BinOp):
			args = [node.left, node.right]
			for arg in args:
				self.traverse(arg)
		elif isinstance(node, ast.Attribute):
			self.interpreter.interpret(node.value)
			print(f"#{node.id} = {self.interpreter.getoutput()}")
		elif isinstance(node, ast.Call):
			code = astunparse.unparse(node)
			self.interpreter.interpret(code)
			print(f"#{code.strip()} = {self.interpreter.getoutput()}")
			if isinstance(node.func, ast.Expr) \
				or isinstance(node.func, ast.Attribute):
				self.traverse(node.func, insideCall=True)
			for arg in node.args:
				self.traverse(arg)
		elif isinstance(node, ast.Expr):
			self.traverse(node.value)
		elif isinstance(node, ast.Return):
			self.traverse(node.value)
		elif isinstance(node, ast.Module) or isinstance(node, ast.FunctionDef):
			if isinstance(node, ast.FunctionDef):
				comments = ast.get_docstring(node)
				values = eval(comments)
				for idx, funcArg in enumerate(node.args.args):
					code = f"{funcArg.arg} = {values[idx]}"
					self.interpreter.interpret(code)
					self.interpreter.getoutput()
			for stmt in node.body:
				self.traverse(stmt)

	def flow(self, code):
		# For now we take the whole code since we might get invalid code so we
		# could try to discard lines to have correct code.
		print(code)
		tree = ast.parse(code)
		for node in ast.walk(tree):
			self.traverse(node)



def runTests(debug):
	with open("scenarios.py", "r") as f:
		allText = f.read().split("#$#$")
		for test in allText:
			debug.flow(test)

if __name__ == "__main__":
	debug = DebugFlow()
	runTests(debug)
