from pprint import pprint
from typing import *

import os
import ast
import fcntl
import parser
import select
import warnings
import threading
import subprocess
import astunparse
import ptyprocess


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
		self.stream = print

	def traverseAttribute(self, node: ast.Attribute, call: bool = False):
		if call:
			self.traverse(node.value)
			return

		code = astunparse.unparse(node).strip()
		self.interpreter.interpret(code)
		self.stream(f"#{code} = {self.interpreter.getoutput()}")

	def traverseAssign(self, node: ast.Assign):
		for expr in ast.walk(node.value):
			self.traverse(expr)
		code = astunparse.unparse(node).strip()
		self.interpreter.interpret(code)
		for target in node.targets:
			code = f"{target.id}".strip()
			self.interpreter.interpret(code)
			self.stream(f"#{code} = {self.interpreter.getoutput()}")

	def traverseBinOp(self, node: ast.BinOp):
		for term in [node.left, node.right]:
			self.traverse(term)
		code = astunparse.unparse(node).strip()
		self.interpreter.interpret(code)
		self.stream(f"#{code} = {self.interpreter.getoutput()}")

	def traverseCall(self, node: ast.Call):
		code = astunparse.unparse(node).strip()
		self.interpreter.interpret(code)
		self.stream(f"#{code} = {self.interpreter.getoutput()}")
		for arg in node.args:
			self.traverse(arg)
		if (isinstance(node.func, ast.Expr) \
			or isinstance(node.func, ast.Attribute)):
			self.traverse(node.func, call=True)

	def traverseExpr(self, node: ast.Expr):
		self.traverse(node.value)

	def traverseFor(self, node: ast.For):
		self.interpreter.interpret(astunparse.unparse(node))
		self.interpreter.interpret("\tpass")
		self.interpreter.getoutput()
		self.traverse(node.target)
		self.traverse(node.iter)

	def traverseFunctionDef(self, node: ast.FunctionDef):
		comments = ast.get_docstring(node)
		values = eval(comments)
		for idx, funcArg in enumerate(node.args.args):
			self.interpreter.interpret(f"{funcArg.arg} = {values[idx]}")
			self.interpreter.getoutput()
		for stmt in node.body:
			self.traverse(stmt)

	def traverseModule(self, node: ast.Module):
		for stmt in node.body:
			self.traverse(stmt)

	def traverseName(self, node:ast.Name):
		self.interpreter.interpret(node.id)
		self.stream(f"#{node.id} = {self.interpreter.getoutput()}")

	def traverseReturn(self, node: ast.Return):
		self.traverse(node.value)

	def untraversable(self, node: Union[ast.Store, ast.Load, ast.Num]):
		return isinstance(node, ast.Store) \
			or isinstance(node, ast.Load) \
			or isinstance(node, ast.Num) \
			or isinstance(node, ast.Str)

	def traverse(self, node, call=False):
		if node in self.seen:
			return
		else:
			self.seen.add(node)

		if self.untraversable(node):
			return

		#TODO(rotaru): treat augassign & substript
		if isinstance(node, ast.Attribute):
			self.traverseAttribute(node, call=call)
		elif isinstance(node, ast.Assign):
			self.traverseAssign(node)
		elif isinstance(node, ast.BinOp):
			self.traverseBinOp(node)
		elif isinstance(node, ast.Call):
			self.traverseCall(node)
		elif isinstance(node, ast.For):
			self.traverseFor(node)
		elif isinstance(node, ast.FunctionDef):
			self.traverseFunctionDef(node)
		elif isinstance(node, ast.Module):
			self.traverseModule(node)
		elif isinstance(node, ast.Name):
			self.traverseName(node)
		elif isinstance(node, ast.Return):
			self.traverseReturn(node)
		elif isinstance(node, ast.Expr):
			self.traverseExpr(node)
		else:
			code = ""
			try:
				code = astunparse.unparse(node)
			except:
				pass
			wmsg = f"Unknown AST node type {str(node)} = [{code.strip()}]"
			warnings.warn(wmsg)

	def flow(self, code):
		# In the case of incorrect/incomplete code we might try to just simply
		# discard the lines that are incorrect (for now), hence we need the
		# whole code snippet at once. This will be changed in the future.
		print(code)
		self.traverse(ast.parse(code))

def runTests(debug):
	with open("scenarios.py", "r") as f:
		allText = f.read().split("#$#$")
		for test in allText:
			debug.flow(test)

if __name__ == "__main__":
	debug = DebugFlow()
	runTests(debug)
